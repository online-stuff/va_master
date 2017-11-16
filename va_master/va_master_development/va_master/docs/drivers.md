<h2>Drivers</h2>

Drivers exist to create an abstraction between the API and differences between specific drivers. The API should not have to care whether it's creating an instance for an OS host or Libvirt host etc.

<h3>Inheritance</h3>

The base class which defines a driver is in the host_drivers/base.py module. This driver is a good starting point, but you need to override a few methods before it can work. 

First off, when a new driver is initialized, a few arguments are required.

    host_drivers/base.py
    _____
    
         def  __init__(self, driver_name,  provider_template, profile_template, provider_name, profile_name, host_ip, key_name, key_path):
        ...
    

The provider_template and profile_template are the files that will be written into the provider and profile configurations respectively. The templates have a series of VAR_X values inside, where X is something that needs to be programatically defined, for instance VAR_HOSTNAME. The base driver will initialize a self.profile_vars and a self.provider_vars dictionary, where the keys are these variables and their values are whatever needs to be in the configuration file. 

For instance, if in my profile_template I have

    
        ...
        image: VAR_IMAGE
        size: VAR_SIZE
        ...
    

Then, in the profile_vars I should have
    
        {
            ...
            'VAR_IMAGE' : 'some_image', 
            'VAR_SIZE' : 'some_flavour'
        }
    

The host_ip is the IP of the va_master host, which is provided when va_master is initialized. key_name and key_path are the name of the key which will be paired by nova, and the path to said key. 

This is an abstract method, and needs to be overridden, with all those variables supplied by the deploy handler. 

Custom drivers need to override ```driver_id()``` and ```friendly_name()```. You also probably want to override ```get_steps()``` if you have custom data you want the user to enter as well as ```validate_field_values()``` in order to handle said data. 

If your configuration is supported by salt, then you don't need to do a lot in order to create minions - the base driver should be able to handle it. 

<h3>Steps</h3>

In order for the hosts to be able to display certain information, va_master needs a connection first, so we need to use multiple steps. For instance, to list available images, we need to enter the url and authentication information. 

In the host_drivers/base.py file, you can find classes which allow you to create steps, which are then parsed as json structures and used in the dashboard. Each Step object has a list of fields, where a field can take on one of a few types - namely 'str', 'options' and 'description'. Driver objects have a list of Steps which are then used by the API. Steps have a ```validate()``` method which checks if all field values have been entered. 

If adding a field via the the add_field method, you can enter a 'blank' = True/False argument, which allows a field to not have a value. 

When steps are successfuly validated, they are turned into StepResults, which are parsed to json and then used by the dashboard. 



<h3>OpenStack Driver</h3>

This driver uses a lot of the base driver functionality. The difference is that OpenStack configuration requires some extra information about the host. 

    host_drivers/openstack.py
    _____
    
        steps[0].add_fields([
            ('host_ip', 'Keystone host_ip:port (xx.xx.xxx.xx:35357)', 'str'),
            ('tenant', 'Tenant', 'str'),
            ('region', 'Region', 'options'),
        ])
    

Then, the ```validate_field_values()``` is overriden in order to use the values from the new fields. 


    host_drivers/openstack.py
    _____
    
        self.provider_vars['VAR_TENANT'] = field_values['tenant']
        self.provider_vars['VAR_IDENTITY_URL'] = os_base_url
        self.provider_vars['VAR_REGION'] = field_values['region']
    

The base driver takes care of substituting these in the configs when the driver is added. 

Additionally, the driver needs to, somehow, receive information about available images, sizes, security groups and networks. This is why we need the following 4 functions. 

    host_drivers/openstac.py
    _____
    
        def get_images()
        def get_sizes()
        def get_networks()
        def get_sec_groups()
    

For OpenStack, the way this works is we use the Rest API to get a token, and then get values from various REST endpoints. Different drivers will use different methods to do this. 


<h3>LibVirt</h3>

Libvirt is a bit more messy to get working because it doesn't work with salt out of the box. So you need to do a lot of manual work to get it working - you have to create instances on your own (you can't rely on the base driver), you have to generate keys and add them to salt and so on. 

First of all, you don't use security groups in LibVirt. In order not to show a field, you just define ```get_sec_groups()``` to return an empty list and delete it from the steps list. 

    host_drivers/libvirt_driver.py
    _____
    
        steps[0].add_fields([
            ('host_ip', 'Host ip', 'str'),
            ('host_protocol', 'Protocol; use qemu with Cert or qemu+tcp for no auth', 'options'),
        ])
        del steps[1].fields[2]
    

We're also adding a few attributes we need to connect to the host. 

The rest of the functions which get libvirt info use the libvirt python module. The biggest issue with this comes when creating a minion, since it all has to be done manually. 

The entire process will not be described here, but what happens is basically this: 
    1. A config drive is generated by creating salt keys. This drive is used by cloud.init. 
    2. The image that the instance will be created with is cloned, and used as the volume for the new instance. 
    3. An .iso image is created from the config drive, which is uploaded for the new instance to use. 
    4. An XML is generated which will define the new instance. 
    5. Finally, using the defineXML method and the final XML, the new instance is created. 

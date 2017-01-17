import sys, importlib

import module_info

from va_master.host_drivers import base

listed_functions = {
    'general' : ['__init__', 'create_minion', 'driver_id', 'friendly_name'], 
    'host_actions' : ['get_host_data', 'get_images', 'get_sizes', 'get_sec_groups', 'get_networks', 'get_host_status'], 
    'networking' : [], 
    'storage' : [], 
    'images_actions' : []
}

def get_driver_methods(driver):
    return module_info.get_class_methods(driver)

def get_all_drivers_dicts(drivers): 
    if base.DriverBase not in drivers: 
        drivers.append((base.DriverBase, 'Driverbase'))
    all_methods = {d[1]: get_driver_methods(d[0]) for d in drivers}
    rows = get_rows(all_methods)
    return rows
   


def get_rows(driver_methods): 
#    driver_methods = driver_methods[driver_methods.keys()[0]]
    print 'My methods are : ', driver_methods
    rows = {
        section:{
            func: [
                any([x[0] == func for x in driver_methods[d] if x[1] not in ['base', 'unfinished']]) for d in driver_methods
            ] for func in listed_functions[section]
        } for section in listed_functions
    }

    return rows



def dicts_to_table(rows, drivers):
    table = ['Function|' + '|'.join(drivers)]
    table.append(('---|' * (1 + len(drivers)))[:-1])
    for section in rows: 
        table.append(section.capitalize())
        for row in rows[section]: 
            new_row = ([row] + [
                {
                    True : '+', 
                    False : '-',
                }[x] for x in rows[section][row][1:]
            ])
            table.append('|'.join(new_row))
        table.append('')
    table = '\n'.join(table)
    return table 


def get_drivers(driver_names, driver_class_names):
    driver_modules = [importlib.import_module(driver_name) for driver_name in driver_names]
    print 'Driver names : ', driver_names, ' and classes : ', driver_class_names
    print 'Getting attrs: ',  [(driver_modules[i], driver_class_names[i]) for i in range(len(driver_class_names))]

    drivers = [getattr(driver_modules[i], driver_class_names[i]) for i in range(len(driver_class_names))]
    return drivers


def predefined(): 
    base_pkg = 'va_master.host_drivers.'
    drivers = ['openstack', 'libvirt_driver', 'generic_driver', 'century_link']
    driver_names = ['OpenStackDriver', 'LibVirtDriver', 'GenericDriver', 'CenturyLinkDriver']
    args = list(reduce(lambda x, y: x + y, zip([base_pkg + x for x in drivers], driver_names)))
    return args

def main():
    table_file = sys.argv[1]
    if len(sys.argv) > 2: 
        args = sys.argv
    else: 
        args = predefined()
    print args
    driver_names = args[2::2]
    driver_class_names = args[3::2]
    

    driver_names = ['va_master.host_drivers.base'] + driver_names
    driver_class_names = ['DriverBase'] + driver_class_names

    drivers = get_drivers(driver_names, driver_class_names)

    print 'Driver names : ', drivers, ' and classes : ', driver_class_names

    all_dicts = get_all_drivers_dicts(zip(drivers, driver_class_names))
    t = dicts_to_table(all_dicts, driver_class_names)
    with open(table_file, 'w') as f: 
        f.write(t)


main()

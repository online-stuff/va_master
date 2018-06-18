import tornado.gen
from paramiko import SSHClient, AutoAddPolicy

#Everytime we use ssh_c.exec_command, the result is 3 'files'
#File 1 is stdin, we don't use it, file 2 is stdout, which is the output we want, file 3 is stderr, which we use for error_reporting


ssh_cl = SSHClient()
ssh_cl.load_system_host_keys()
ssh_cl.set_missing_host_key_policy(AutoAddPolicy())

def get_ssh_result(cmd):
    result = ssh_cl.exec_command(cmd)
    error = result[2].read()
    if error:
        raise Exception('Error performing SSH command. Command is: ' + cmd + '. Error is : ' + error)
    return result[1].read()


#Forms are made to work well with the front-end, where we have to define the type of result we return, as well as a list of elements that will be shown on the form. 
#Typically, functions starting with show_* are functions that will return some sort of a form. Anything else is a more generic function that returns lists or simpler JSON. 
@tornado.gen.coroutine
def get_forms():
    forms = {
        'restart_service' : [
            get_processes, 
            {
                'submit_action' : 'ssh/restart_service',
                'elements' : [
                    {'type' : 'text', 'key' : 'service_name', 'label' : 'Service name', 'size': 9},
                ],
                'type' : 'form', 
                'label' : 'Restart service',
            }
        ], 
    }
    raise tornado.gen.Return(forms)


@tornado.gen.coroutine
def get_form(action):
    form = yield get_forms()
    form = form[action]
    for i in range(len(form)): 
        if callable(form[i]):
            list_func = form[i]
            result = yield list_func()
            result = '</br>'.join(result)
            form[i] = {'data' : result}

    raise tornado.gen.Return(form)

#NOTE this wil probably change in the future. 
@tornado.gen.coroutine
def format_list(l):
    l = '</br>'.join(l)
    return l

@tornado.gen.coroutine
def get_processes():
    cmd = 'ps -e -o pid,user,pcpu,%cpu,%mem,vsz,rss,comm,args --sort=-pcpu'

    result = get_ssh_result(cmd)
    result = [x for x in result.split('\n') if x][1:]
    result = [[i.strip() for i in x.split(' ') if i.strip()] for x in result]

    #Columns are : 
    #PID USER %CPU %CPU %MEM VSZ RSS COMMAND COMMAND
    #And yes, some of the columns are duplicates. 

    result = [' '.join([x[0], x[1], x[7], ' '.join(x[8:])]) for x in result]
    raise tornado.gen.Return(result)


@tornado.gen.coroutine
def get_users():
    users = get_ssh_result('who')
    users = [x for x in users.split('\n') if x]
    users = yield format_list(users)
    raise tornado.gen.Return(users)

@tornado.gen.coroutine
def get_services():
    cmd = 'service --status-all | grep " + " | awk \'{ print $4; }\''
    result = get_ssh_result(cmd)

    result = [x for x in result.split('\n') if x]
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def restart_service(service_name = None):
    message = ''
    if not service_name: 
        result = yield get_form('restart_service')
    else: 
        cmd = 'service %s restart' % (service_name)
        result = get_ssh_result(cmd)
        message = 'Service %s restarted. ' % (service_name)


    result = {'message' : message, 'data' : result,  'success' : True}

    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def show_processes():
    processes = yield get_processes()
    processes = yield format_list(processes)
    result = {'data' : processes, 'success' : True, 'message' : ''}
    raise tornado.gen.Return(processes)

@tornado.gen.coroutine
def show_usage():
    usage = get_ssh_result('free -m')
    usage = [x for x in usage.split('\n') if x]
    usage = yield format_list(usage)
    raise tornado.gen.Return(usage)


    pass

@tornado.gen.coroutine
def show_services():
    services = yield get_services()
    services = yield format_list(services)
    services = {'data' : services, 'success' : True, 'message' : ''}
#    form = yield get_form('show_services')
    raise tornado.gen.Return(services)

@tornado.gen.coroutine
def remove_server(datastore_handler, server_name):
    server = yield datastore_handler.get_object(object_type = 'server', server_name = server_name)
    provider_name = server.get('provider_name', 'va_standalone_servers')

    provider = yield datastore_handler.get_object(object_type = 'provider', provider_name = provider_name)
    provider['servers'] = [x for x in provider['servers'] if x['server_name'] != server_name]

    yield datastore_handler.insert_object(object_type = 'provider', provider_name = provider_name, data = provider)
    yield datastore_handler.delete_object(object_type = 'server', server_name = server_name)

@tornado.gen.coroutine
def reboot():
    result = get_ssh_result('reboot')
    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def stop():
    result = get_ssh_result('stop')
    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def handle_ssh_action(datastore_handler, action, ip_addr, username = '', password = '', port = None, kwargs = {}):

    user_type = 'root' if username == 'root' else 'user'
    consul_ssh_actions = yield datastore_handler.get_object('managed_actions', manage_type = 'ssh', manage_subtype = user_type)

    consul_action = [x for x in consul_ssh_actions['actions'] if x['name'] == action]
    if not consul_action: 
        raise Exception("No action " + action + "found.")
    consul_action = consul_action[0]
    ssh_kwargs = consul_action.get('kwargs', [])

    ssh_kwargs = {x : kwargs[x] for x in ssh_kwargs}

    connect_kwargs = {}
    key_path = '/root/.ssh/va-master.pem'

    connect_kwargs['username'] = username

    if password: 
        connect_kwargs['password'] = password
    else: 
        connect_kwargs['key_filename'] = key_path

    if port: 
        connect_kwargs['port'] = int(data.get('port'))


    print ('Connecting with: ', connect_kwargs)
    if consul_action.get('requires_ssh', True):
        ssh_cl.connect(ip_addr, **connect_kwargs)
    ssh_func = globals()[action]
    result = yield ssh_func(**ssh_kwargs)
    raise tornado.gen.Return(result)

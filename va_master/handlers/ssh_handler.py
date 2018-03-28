import tornado.gen
from paramiko import SSHClient, AutoAddPolicy

#Everytime we use ssh_c.exec_command, the result is 3 'files'
#File 1 is stdin, we don't use it, file 2 is stdout, which is the output we want, file 3 is stderr, which we use for error_reporting


ssh_cl = SSHClient()
ssh_cl.load_system_host_keys()
ssh_cl.set_missing_host_key_policy(AutoAddPolicy())

def get_ssh_result(cmd):
    result = ssh_cl.exec_command('ps -e -o pid,user,pcpu,%cpu,%mem,vsz,rss,comm,args --sort=-pcpu')
    if result[2].read():
        raise Exception('Error performing SSH command. Command is: ' + cmd + '. Error is : ' + result[2].read())
    return result[1].read()

@tornado.gen.coroutine
def get_forms():
    forms = {
        'restart_service' : {
            'name' : 'restart_process', 
            'submit_action' : 'restart_process',
            'label' : 'Restart process', 
            'data' : [
                get_processes,
                'text_input', 
                'button',
            ]
        }, 
        'show_processes' : {
            'name' : 'show_processes', 
            'label' : 'Show processes', 
            'data' : [
                get_processes,
            ]
        },
        'show_services' : {
            'name' : 'show_services', 
            'label' : 'Show services', 
            'data' : [
                get_services, 
            ]
        },

    }
    raise tornado.gen.Return(forms)


@tornado.gen.coroutine
def get_form(action):
    form = yield get_forms()
    form = form[action]
    for i in range(len(form['data'])): 
        if callable(type(form['data'][i])): 
            list_func = form['data'][i]
            print ('Func is : ', list_func)
            form['data'][i] = yield list_func()
            print ('Data now is : ', form['data'])

    raise tornado.gen.Return(form)

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
    pass

@tornado.gen.coroutine
def get_services():
    cmd = 'service --status-all | grep " + " | awk \'{ print $4; }\''
    result = get_ssh_result(cmd)

    result = [x for x in result.split('\n') if x]
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def restart_process(service_name):
    if not process_id: 
        result = yield get_form('restart_process')
    else: 
        cmd = 'service %s restart' % (service_name)
        result = get_ssh_result(cmd)

    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def show_processes():
    form = yield get_form('show_processes')
    raise tornado.gen.Return(form)

@tornado.gen.coroutine
def show_usage():
    pass

@tornado.gen.coroutine
def show_services():
    form = yield get_form('show_services')
    raise tornado.gen.Return(form)

@tornado.gen.coroutine
def handle_ssh_action(action, ip_addr, username = '', password = '', port = None, kwargs = {}):
    connect_kwargs = {}
    key_path = '/root/.ssh/va-master.pem'


    if username or password: 
        connect_kwargs['username'] = username
        connect_kwargs['password'] = password
    else: 
        connect_kwargs['key_filename'] = key_path

    if port: 
        connect_kwargs['port'] = int(data.get('port'))


    print ('Kwargs are : ', connect_kwargs)
    ssh_cl.connect(ip_addr, **connect_kwargs)
    ssh_func = globals()[action]
    result = yield ssh_func(**kwargs)
    raise tornado.gen.Return(result)

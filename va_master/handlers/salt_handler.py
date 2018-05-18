import tornado, paramiko, subprocess

from va_master.utils.va_utils import call_master_cmd, get_route_to_minion
from va_master.utils.paramiko_utils import ssh_call
from salt.client import LocalClient

@tornado.gen.coroutine
def add_minion_to_server(datastore_handler, server_name, ip_address, role, username = '', password = '', key_filename = ''):
    '''
        Installs salt on the server, adds the master keys, runs highstate and adds a panel for that server. 
        In more details, the function does the following steps: 
            - Create minion keys locally using salt-key --gen-keys
            - Copy the public minion key to /local/salt/dir/pki/master/minions/
            - Create the /salt/dir/pki/minion dir on the remote server
            - Put the minion keys generated in the first step to the remote server in /salt/dir/pki/minion/
            - Copy the `minion.sh` script from this repo to /root/ on the remote server
            - Run the script
            - Update /etc/salt/minion_id on the remote server. 
            - If the minion has a role, add a panel for the minion
            - Run state.highstate on the minion. 

    '''

    print ('Called add_minino_to_server')

    ip_address = call_master_cmd('dnsutil.A', arg = [ip_address])[0]
    print ('Ip address now is : ', ip_address)

    minion_route = get_route_to_minion(ip_address)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    #local_key is where the minion keys will sit in salt
    #init_key is where they are initially created    
    local_key_dir = '/etc/salt/pki/master/minions/%s' % (server_name)
    init_key_dir = '/tmp/%s' % (server_name)

    #bootstrap_script is where the bootstrap script resides on the va_master
    #server_script is where it will reside on the targeted server
    bootstrap_script = '/opt/va_master/minion.sh'
    server_script = '/root/minion.sh'

    connect_kwargs = {'username' : username}
    if password: 
        connect_kwargs['password'] = password
    elif key_filename: 
        connect_kwargs['key_filename'] = key_filename
    else: 
        raise Exception('When adding minion to server, I expected either password or key_filename, but both values are empty. ')

    ssh.connect(ip_address, **connect_kwargs)
    sftp = ssh.open_sftp()

    #We generate keys in /tmp, and then copy the public key  to the salt dir
    create_key_cmd = ['salt-key', '--gen-keys=%s' % (server_name), '--gen-keys-dir=/tmp/']
    copy_key_to_salt_cmd = ['cp', init_key_dir + '.pub', local_key_dir]

    subprocess.check_output(create_key_cmd)
    subprocess.check_output(copy_key_to_salt_cmd)

    #We create the pki dir and copy the initial keys there
    ssh_call(ssh, 'mkdir -p /etc/salt/pki/minion/')

    sftp.put(init_key_dir + '.pem', '/etc/salt/pki/minion/minion.pem')
    sftp.put(init_key_dir + '.pub', '/etc/salt/pki/minion/minion.pub')

    #Finally, we download the bootstrap script on the remote server and run it
    #This should install salt-minion, which along with the minion keys should make it readily available. 
    sftp.put(bootstrap_script, server_script)

    ssh_call(ssh, 'chmod +x ' + server_script)
    ssh_call(ssh, "%s %s %s" % (server_script, role, minion_route))
    ssh_call(ssh, 'echo %s > /etc/salt/minion_id' % (server_name))


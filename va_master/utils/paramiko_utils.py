import paramiko

def ssh_call(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    error = stderr.read()
    if error: 
        print ('Error performing ' + str(command) + ': ' + error)

    return stdout.read()

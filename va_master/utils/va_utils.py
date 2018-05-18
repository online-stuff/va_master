from salt.client import LocalClient


prefixes = {'KB' : 10, 'MB' : 20, 'GB' : 30, 'TB' : 40}

def int_to_bytes(i):
    if not type(i) in [int, float]:
        return i
    if type(i) == str:
        return i
    prefix = 'GB'
    b = float(i) / (2 ** prefixes[prefix])
    b = '%.2f' % (b) + ' ' + prefix

    return b

def bytes_to_readable(num, suffix='B'):
    """Converts bytes integer to human readable"""

    num = int(num)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def bytes_to_int(b):
    if not type(b) in [str]:
        return b
    b = b.split(' ')
    i = float(b[0]) * (2 ** prefixes[b[1]])

    return i

def get_master_ip():
    ''' Gets the default gateway. Not used atm in lieu of get_route_to_minion but it might be useful sometimes. '''
    result = call_master_cmd('network.default_route')
    gateway = [x['gateway'] for x in result if x.get('gateway', '') != '::']
    gateway = gateway[0]
    result = call_master_cmd('network.get_route', arg = ['gateway'])
    ip = result['source']

    return ip

def get_route_to_minion(ip_address):
    ''' Calls salt-call network.get_route <ip_address> and returns the source. '''
    result = call_master_cmd('network.get_route', arg = [ip_address])
    return result['source']

def call_master_cmd(fun, arg = [], kwarg = {}):
    ''' Calls the salt function on the va-master. Used to work with salt-call but a recent salt version made it incompatible with tornado, so we resort to using the `role` grain to find the va-master and call the function that way. '''

    cl = LocalClient()
    result = cl.cmd('G@role:va-master', fun = fun, tgt_type = 'compound', arg = arg, kwarg = kwarg)
    result = [result[i] for i in result if result[i]]
    if not result: 
         raise Exception('Tried to run ' + str(fun) + ' on va-master, but there was no response. arg was ' + str(arg) + ' and kwarg was ' + str(kwarg))
    return result[0]


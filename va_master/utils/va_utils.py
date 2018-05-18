from salt.client import LocalClient


prefixes = {'KB' : 10, 'MB' : 20, 'GB' : 30, 'TB' : 40}
mebi = ['KiB', 'MiB', 'GiB', 'TiB']

def prefix_to_int(bytes, prefix):
    val = float(bytes) * (2 ** prefixes[prefix])
    return val

def mebi_to_int(bytes, prefix):
    mebi_index = mebi.index(prefix) + 1
    val = float(bytes) * (10 ** (mebi_index * 3))
    return val

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
    print ('Trying to convert ', b, ' to int. ')
    if not type(b) in [str, unicode]:
        return b
    b = b.split(' ')
    if b[1] in prefixes: 
        i = prefix_to_int(b[0], b[1])
    elif b[1] in mebi: 
        i = mebi_to_int(b[0], b[1])
    else:
        raise Exception('Cannot convert ' + str(b) + ' to int. ')

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


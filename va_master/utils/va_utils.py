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


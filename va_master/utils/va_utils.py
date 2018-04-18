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

def bytes_to_int(b):
    if not type(b) in [str]:
        return b
    b = b.split(' ')
    i = float(b[0]) * (2 ** prefixes[b[1]])

    return i


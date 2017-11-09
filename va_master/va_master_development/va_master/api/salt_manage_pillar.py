import re

def get_server_role_attrs(top_file, role):

    # Matches role:<some_role>':
    #    - some_attr
    #    - some_other_attr
    re_str = "role:" + role + "':\n((.*-.*\n)*)" 

    role_attrs = re.search(re_str, top_file)
    if not role_attrs: return []

    attrs = role_attrs.groups()[0]
    attrs = [x.replace('  ', '') for x in attrs.split('\n')]
    

    # Removes basic attributes; currently these are "match: grain", and "credentials". 
    attrs = [x for x in attrs if not any([i in x for i in ['grain', 'credentials']]) and x]
    return attrs

def get_server_role_attrs_from_file(file_location, role):
    with open(file_location) as f: 
        contents = f.read()

    return get_server_role_attrs(contents, role)

def prepare_server(server_name, attrs, role):
    server_str =   "\n  %s:\n     - %s-credentials" % (server_name, server_name)
    for a in attrs: 
        server_str += '\n     ' + a
    return server_str

def rm_server_contents(top_file, server_name):
    re_str = "%s:\n(( *-.*\n?)*)" % (server_name)
    top_file = re.sub(re_str, '', top_file)
    return top_file
   
def rm_server(server_name, pillar_top = '/srv/pillar/top.sls'):
    with open(pillar_top) as f: 
        contents = f.read()
        new_pillar = rm_server_contents(contents, server_name)
        new_pillar = new_pillar.rstrip()

    with open(pillar_top, 'w') as f: 
        f.write(new_pillar)


def add_server(server_name, role, pillar_top = '/srv/pillar/top.sls'):
    with open(pillar_top) as f:
        top_file = f.read()

        server_re = '%s:\n' % server_name
        server_exists = re.search(server_re, top_file)
        if server_exists: 
            rm_server(server_name, pillar_top)

        attrs = get_server_role_attrs(top_file, role)
        new_server = prepare_server(server_name, attrs, role)

    with open(pillar_top, 'a') as f: 
        f.write(new_server)
   

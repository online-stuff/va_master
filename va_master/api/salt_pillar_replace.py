import re

def get_instance_role_attrs(top_file, role):

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

def get_instance_role_attrs_from_file(file_location, role):
    with open(file_location) as f: 
        contents = f.read()

    return get_instance_role_attrs(contents, role)

def prepare_instance(instance_name, attrs, role):
    instance_str =   "\n  %s:\n     - %s-credentials" % (instance_name, instance_name)
    for a in attrs: 
        instance_str += '\n     ' + a
    return instance_str

def rm_instance_contents(top_file, instance_name):
    re_str = "%s:\n(( *-.*\n?)*)" % (instance_name)
    top_file = re.sub(re_str, '', top_file)
    return top_file
   
def rm_instance(instance_name, pillar_top = '/srv/pillar/top.sls'):
    with open(pillar_top) as f: 
        contents = f.read()
        new_pillar = rm_instance_contents(contents, instance_name)
        new_pillar = new_pillar.rstrip()

    with open(pillar_top, 'w') as f: 
        f.write(new_pillar)


def add_instance(instance_name, role, pillar_top = '/srv/pillar/top.sls'):
    with open(pillar_top) as f:
        top_file = f.read()

        instance_re = '%s:\n' % instance_name
        instance_exists = re.search(instance_re, top_file)
        if instance_exists: 
            rm_instance(instance_name, pillar_top)

        attrs = get_instance_role_attrs(top_file, role)
        new_instance = prepare_instance(instance_name, attrs, role)

    with open(pillar_top, 'a') as f: 
        f.write(new_instance)
   

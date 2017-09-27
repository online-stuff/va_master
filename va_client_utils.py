import argparse, json

module_mappings = {
    'providers' : {
        'list' : {"kwargs" : {"endpoint" : "/providers", "data" : '{}'}, "keys" : ["provider_name", 'driver_name', 'location']},
    },
    'apps' : {
        'list' : {
            'running' : {"kwargs" : {'endpoint' : '/providers/info', 'data' : '{}', 'method' : 'post'}, "keys" : ['provider_name', 'servers']}, 
            'available' : {"kwargs" : {'endpoint' : '/providers/info', 'data' : '{}', 'method' : 'post'}, 'keys' : ['provider_name', 'servers']}, 
        }, 
        'directory' : {
            'users' : {
                'list' : {"kwargs" : {'endpoint' : '/panels/action', 'data' : {'server_name' : 'va-directory', 'action' : 'list_users'}, 'keys' : ['users']}}, 
                'locked' : {"kwargs" : {'endpoint' : '/panels/action', 'data' : {'server_name' : 'va-directory', 'action' : 'list_users'}, 'keys' : ['users']}},
            }
        }
    },
    'services' : {
        'list' : {
            'kwargs' : {"endpoint" : '/services'}, 
            'ok' : {"kwargs" : {'endpoint' : '/services/by_status', 'data' : '{"status" : "OK"}'}},
            'critical' : {"kwargs" : {'endpoint' : '/services/by_status', 'data' : '{"status" : "CRITICAL"}'}},
        }
    },
    'vpn' :  {
        'list' : {"kwargs" : {"endpoint" : '/apps/vpn_users'}}, 
        'status' : {"kwargs" :  {"endpoint" : '/apps/vpn_status'}},
        'add' : {"kwargs" : {'endpoint' : '/apps/add_vpn_user', 'method' : 'post'}}, 
        'get-cert' : {"kwargs" : {'endpoint' : '/apps/download_vpn_cert', 'method' : 'post'}},
    }
}

module_args = {
    'providers' : {
        'description' : 'Allows you to call various providers related functions. ', 
        'choices' : ['list'], 
        'help' : 'Specific provider command. ', 
    },'apps' : {
        'description' : 'Allows you to call various apps related functions. ', 
        'choices' : ['list', 'running', 'available', 'directory', 'users', 'users', 'all', 'locked'], 
    },'vpn' : {
        'description' : 'Allows you to call various vpn related functions. ', 
        'choices' : ['list', 'status', 'add', 'get-cert'], 
        'extra_args' : ['--username'], 
    },'services' : {
        'description' : 'Allows you to call various services related functions. ', 
        'choices' : ['list', 'ok', 'critical'], 
    },

}
#Will traverse a mapping by using keys from the command. If it gets to the end of the command but not to the end of the tree, will raise an exception. If a command key is invalid, will also raise an exception. 
def get_mapping_arguments(mapping, command):
    extra_args = {}
    for key in command: 
        if key not in mapping.keys():

            #If the key is not in the expected command keys, it might be an argument. See if command has extra_args. 
            if mapping.get('kwargs', {}).get('extra_args', []):
                #Add the first key to the first argument in extra_args
                pass
#                extra_args[mapping['kwargs']['extra_args'].pop(0)] = key

            #Key is not in the expected keys, and there are more keys than arguments. There is an error. 
            else:
                expected_keys = [x if x != 'kwargs' else '<End of command>'  for x in mapping.keys()]
                raise Exception('Invalid command: ' + ' '.join(command) + '; Failed at ' + key + '. Did not find it in expected keys : ' + str(expected_keys) + '. Maybe there are too many arguments? Collected so far : ' + str(extra_args))

        mapping = mapping[key]

    #We have iterated throughout the entire command. If mapping does not contain "kwargs", we are not at the bottom of the tree. 
    if 'kwargs' not in mapping.keys():
        raise Exception('Invalid command: ' + ' '.join(command) + '; Parsed the entire command but did not find a suitable function. Maybe add one of these keywords : ' + str(mapping.keys()))

#    if extra_args: 
#        mapping['data'] = extra_args
#        mapping['kwargs'].pop('extra_args')
 #   print mapping
    return mapping

def extract_data_with_keys(result, keys = []):
    if not keys: return result

    final_result = []
    for data in result: 
#        print ('Data is : ', data)
        for k in keys: 
            if k not in data.keys(): 
                raise Exception('Key ' + k + ' not found in ' + str(data.keys()))
        data = {x : data[x] for x in keys}
        final_result.append(data)
    return final_result

import yaml, json, glob

def get_states_data():
    states_data = {}
    subdirs = glob.glob('/srv/salt/*')
    for state in subdirs:
        try: 
            with open(state + '/appinfo.json') as f: 
                states_data[state] = json.loads(f.read())
        except IOError as e: 
            print state, ' does not have an appinfo file, skipping. ' 
    print states_data

get_states_data()

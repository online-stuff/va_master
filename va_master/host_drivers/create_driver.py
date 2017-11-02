import argparse, os, re
from jinja2 import Template


def to_snake(s): 
    return re.sub('(?!^)([A-Z]+)', r'_\1', s).lower()

def to_camel(s): 
    return ''.join([x.capitalize() for x in s.split('_')])

def main(): 
    parser = argparse.ArgumentParser()

    parser.add_argument('--driver-name')
    parser.add_argument('--driver-friendly')

    args = parser.parse_args()
    driver_dir = os.path.dirname(os.path.realpath(__file__))
    print ('Dir is : ', driver_dir)

    old_driver = ''
    with open(driver_dir + '/driver_stub.py', 'r') as f: 
        old_driver = f.read()
    old_driver = Template(old_driver)
    old_driver = old_driver.render({
        'driver_name' : to_camel(args.driver_name), 
        'driver_id' : to_snake(args.driver_name), 
        'driver_friendly' : args.driver_friendly
    })

    with open(driver_dir + '/' + to_snake(args.driver_name) + '_driver.py', 'w') as f: 
        f.write(old_driver)

main()

from optparse import OptionParser
import sys, inspect, importlib, csv

#Gets a class
#Returns a list of tuples [('function_name', 'function_doc'), ...]
def get_class_methods(cls):
    methods = inspect.getmembers(cls, predicate = inspect.ismethod)
    methods = [(x[0], x[1].__doc__) for x in methods]
    return methods

#Gets a list of tuples [('class', 'ClassName')], ...]
#Returns a dictionary {'ClassName': [('function_name', 'function_doc'), ...]
def get_class_dict(cls_list): 
    all_methods = {c[1]: get_class_methods(c[0]) for c in cls_list}
    return all_methods


def dict_to_table(cls_name, cls_dict):
    table = ['|'.join(*func) for func in cls[cls_name]]
    table = ['Function | Documentation', '--- | ---'] + table
    table = '\n'.join(table)
    return table

def get_tables_for_dicts(cls_list):
    tables = [dict_to_table(cls, cls_list[cls]) for cls in cls_list]
    tables = '\n\n'.join(tables)
    return tables

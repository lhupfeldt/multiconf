# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
import inspect
from collections import namedtuple

_Traceback = namedtuple('Traceback', 'filename, lineno, function, code_context, index')


def lineno():
    return _Traceback(*inspect.stack()[1][1:]).lineno


def lazy(*args):
    return lambda: args[0](*args[1:])


def _config_msg(err_or_warn, file_name, line_num, *lines):
    if not file_name.endswith('.py'):
        # file_name  may end in .pyc!
        file_name = file_name[:-1]

    emsg = ""
    for line in lines:
        emsg += 'File "{file_name}", line {line_num}'.format(file_name=file_name, line_num=line_num) + '\n'
        emsg += 'Config' + err_or_warn + ': ' + line + '\n'
    return emsg
    

def config_error(file_name, line_num, *lines):
    return _config_msg('Error', file_name, line_num, *lines)


def config_warning(file_name, line_num, *lines):
    return _config_msg('Warning', file_name, line_num, *lines)


# Handle variable ids in json/repr output

_replace_ids_regex = re.compile(r'("__id__"|, id): [0-9]+("?),')
_replace_refs_regex = re.compile(r'": "#ref id: [0-9]+"')
_replace_named_as_regex = re.compile(r" #as: '[^,]+',")

def replace_ids(json_string, named_as=True):
    json_string = _replace_ids_regex.sub(r'\1: 0000\2,', json_string)
    if named_as:
        json_string = _replace_named_as_regex.sub(r" #as: 'xxxx',", json_string)
    return _replace_refs_regex.sub(r'": "#ref id: 0000"', json_string)


_compact_ids_regex = re.compile(r'("), \n *"__id__": ([0-9]+),')
_compact_calculated_regex = re.compile(r': ([^ ]+)"?, \n *"([a-zA-Z0-9]*) #calculated": true')
def to_compact(json_string):
    # There is no named_as in the non-compact format, just insert
    json_string = _compact_ids_regex.sub(r" #as: 'xxxx', id: \2\1,", json_string)
    return _compact_calculated_regex.sub(r': "\1 #calculated"', json_string)


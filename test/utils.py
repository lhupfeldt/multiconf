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


def _config_msg(error_type, file_name, line_num, *lines):
    if not file_name.endswith('.py'):
        # file_name  may end in .pyc!
        file_name = file_name[:-1]

    emsg = ""
    for line in lines:
        emsg += 'File "{file_name}", line {line_num}'.format(file_name=file_name, line_num=line_num) + '\n'
        emsg += error_type + ': ' + line + '\n'
    return emsg
    

def config_error(file_name, line_num, line):
    return _config_msg('ConfigError', file_name, line_num, *[line])


def config_warning(file_name, line_num, line):
    return _config_msg('ConfigWarning', file_name, line_num, *[line])


def api_error(file_name, line_num, line):
    return _config_msg('MultiConfApiError', file_name, line_num, *[line])


# Handle variable ids and source file line numbers in json/repr output

_replace_user_file_line_regex = re.compile(r"\('(.*)_test.py', [0-9]+\)")
def replace_user_file_line(json_string):
    return _replace_user_file_line_regex.sub(r"('\1_test.py', 999)", json_string)


_replace_ids_regex = re.compile(r'("__id__"|, id| #id): [0-9]+("?),')
_replace_refs_regex = re.compile(r'": "#ref id: [0-9]+"')
_replace_named_as_regex = re.compile(r" #as: '[^,]+',")
def replace_ids(json_string, named_as=True):
    json_string = _replace_ids_regex.sub(r'\1: 0000\2,', json_string)
    if named_as:
        json_string = _replace_named_as_regex.sub(r" #as: 'xxxx',", json_string)
    json_string = replace_user_file_line(json_string)
    return _replace_refs_regex.sub(r'": "#ref id: 0000"', json_string)


_compact_ids_regex = re.compile(r'("), \n *"__id__": ([0-9]+),')
_compact_calculated_regex = re.compile(r': ([^ ]+)"?, \n *"([a-zA-Z0-9]*) #calculated": true')
def to_compact(json_string):
    # There is no named_as in the non-compact format, just insert
    json_string = _compact_ids_regex.sub(r" #as: 'xxxx', id: \2\1,", json_string)
    return _compact_calculated_regex.sub(r': "\1 #calculated"', json_string)

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, re


def lineno():
    frame = sys._getframe(1)
    return frame.f_lineno


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


def config_error(file_name, line_num, *line):
    return _config_msg('ConfigError', file_name, line_num, *line)


def config_warning(file_name, line_num, *line):
    return _config_msg('ConfigWarning', file_name, line_num, *line)


def api_error(file_name, line_num, *line):
    return _config_msg('MultiConfApiError', file_name, line_num, *line)


def _multi_file_single_config_msg(error_type, msg, *file_line_msg):
    """
    file_line_msg: tuple of (filename, lineni, linemsg)
    msg: overall error message
    """

    emsg = ""
    for file_name, line_num, line_msg in file_line_msg:
        if not file_name.endswith('.py'):
            # file_name  may end in .pyc!
            file_name = file_name[:-1]

        emsg += 'File "{file_name}", line {line_num}'.format(file_name=file_name, line_num=line_num) + ', ' + line_msg + '\n'
    emsg += msg + '\n'
    return emsg


def multi_file_single_config_error(msg, *file_line_msg):
    return _multi_file_single_config_msg('ConfigError', msg, *file_line_msg)


# Handle variable ids and source file line numbers in json/repr output


_replace_user_file_line_tuple_regex = re.compile(r"\('[^,()]+/([^/]+)_test.py', [0-9]+\)")
def replace_user_file_line_tuple(string):
    return _replace_user_file_line_tuple_regex.sub(r"('fake_dir/\1_test.py', 999)", string)


_replace_user_file_line_msg_regex = re.compile(r'File "[^"]+/([^/]+)_test.py", line [0-9]+')
def replace_user_file_line_msg(string, line_no=999):
    return _replace_user_file_line_msg_regex.sub(r'File "fake_dir/\1_test.py", line %s' % line_no, string)

_replace_multiconf_file_line_msg_regex = re.compile(r'File "[^"]+/multiconf/([^/]+).py", line [0-9]+')
def replace_multiconf_file_line_msg(string):
    return _replace_multiconf_file_line_msg_regex.sub(r'File "fake_multiconf_dir/\1.py", line 999', string)

_replace_ids_regex = re.compile(r'("__id__"|, id| #id): [0-9]+("?)')
_replace_refs_regex = re.compile(r'"#ref (self, |later, |)id: [0-9]+')
_replace_named_as_regex = re.compile(r" #as: '[^,]+',")
def replace_ids(json_string, named_as=True):
    json_string = _replace_ids_regex.sub(r'\1: 0000\2', json_string)
    if named_as:
        json_string = _replace_named_as_regex.sub(r" #as: 'xxxx',", json_string)
    return _replace_refs_regex.sub(r'"#ref \1id: 0000', json_string)


_replace_builder_ids_regex = re.compile(r"""\.builder\.[0-9]+(["'])""")
def replace_ids_builder(json_string, named_as=True):
    json_string = _replace_builder_ids_regex.sub(r'.builder.0000\1', json_string)
    return replace_ids(json_string, named_as)


_compact_ids_regex = re.compile(r'("), \n *"__id__": ([0-9]+),')
_compact_calculated_regex = re.compile(r': "?([^"]+)"?, \n *"([a-zA-Z0-9_]*) #calculated": true')
def to_compact(json_string):
    # There is no named_as in the non-compact format, just insert
    json_string = _compact_ids_regex.sub(r" #as: 'xxxx', id: \2\1,", json_string)
    return _compact_calculated_regex.sub(r': "\1 #calculated"', json_string)


#    "item": false, 
#    "item #Excluded: <class 'multiconf.test.include_exclude_test.item'>": true

_compact_excluded_regex = re.compile(r""": false, \n *"([a-zA-Z0-9_]*) #Excluded: <class '([.xa-zA-Z0-9_]*)'>": true""")
def to_compact_excluded(json_string):
    json_string = to_compact(json_string)
    return _compact_excluded_regex.sub(r""": "false #Excluded: <class '\2'>""" + '"', json_string)

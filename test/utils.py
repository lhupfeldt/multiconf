# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

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

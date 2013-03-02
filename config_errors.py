# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os.path
from collections import namedtuple
import inspect

class ConfigBaseException(Exception):
    pass


class ConfigException(ConfigBaseException):
    pass


class NoAttributeException(ConfigBaseException):
    pass


class InvalidUsageException(ConfigBaseException):
    pass


_Traceback = namedtuple('Traceback', 'filename, lineno, function, code_context, index')


def _user_file_line(up_level_start=0):
    while 1:
        tb = _Traceback(*inspect.stack()[up_level_start][1:])
        if os.path.basename(os.path.dirname(tb.filename)) != 'multiconf':
            break
        up_level_start += 1

    return tb.filename, tb.lineno 


def _error_msg(num_errors, message, up_level=2, error_type='ConfigError'):
    print >> sys.stderr, 'File "%s", line %d' % _user_file_line(up_level+1)
    print >> sys.stderr, error_type + ':', message
    return num_errors + 1


def _warning_msg(message, up_level=2):
    _error_msg(0, message, up_level=up_level+1, error_type='ConfigWarning')

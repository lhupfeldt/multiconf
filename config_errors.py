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


def _line_msg(up_level=2, ufl=None, msg=''):
    """ufl is a tuple of filename, linenumber referece to user code"""
    ufl = ufl or _user_file_line(up_level+1)
    print >> sys.stderr, ('File "%s", line %d' % ufl) + (', ' + msg if msg else '')


def _error_type_msg(num_errors, message):
    print >> sys.stderr, 'ConfigError:', message
    return num_errors + 1

def _error_msg(num_errors, message, up_level=2, ufl=None):
    _line_msg(up_level, ufl)
    return _error_type_msg(num_errors, message)


def _warning_type_msg(num_warnings, message):
    print >> sys.stderr, 'ConfigWarning:', message
    return num_warnings + 1

def _warning_msg(num_warnings, message, up_level=2, ufl=None):
    _line_msg(up_level, ufl)
    return _warning_type_msg(num_warnings, message)


def _api_error_type_msg(num_warnings, message):
    print >> sys.stderr, 'MultiConfApiError:', message
    return num_warnings + 1

def _api_error_msg(num_errors, message, up_level=2, ufl=None):
    _line_msg(up_level, ufl)
    return _api_error_type_msg(num_errors, message)

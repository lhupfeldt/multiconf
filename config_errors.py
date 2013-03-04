# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os.path
from collections import namedtuple


class ConfigBaseException(Exception):
    pass


class ConfigException(ConfigBaseException):
    pass


class NoAttributeException(ConfigBaseException):
    pass


class InvalidUsageException(ConfigBaseException):
    pass


def _user_file_line(up_level_start=1):
    frame = sys._getframe(up_level_start)
    while 1:
        filename = frame.f_globals['__file__']
        if os.path.basename(os.path.dirname(filename)) != 'multiconf':
            break
        frame = frame.f_back

    return filename if filename[-1] == 'y' else filename[:-1], frame.f_lineno


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

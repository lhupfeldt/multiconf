# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, os.path


class ConfigBaseException(Exception):
    pass


class ConfigDefinitionException(ConfigBaseException):
    def __init__(self, msg):
        super(ConfigDefinitionException, self).__init__(msg)


class ConfigException(ConfigBaseException):
    pass


class NoAttributeException(ConfigBaseException):
    pass


class InvalidUsageException(ConfigBaseException):
    pass


class ConfigApiException(ConfigBaseException):
    pass


class ConfigAttributeError(AttributeError):
    def __init__(self, mc_object, attr_name):
        super(ConfigAttributeError, self).__init__("")
        self.mc_object = mc_object
        self.attr_name = attr_name

    @property
    def message(self):
        error_message = "%(mc_object_repr_and_type)s has no attribute %(attr_name)s"
        repeatable_attr_name = self.attr_name + 's'
        if self.mc_object._mc_attributes.get(repeatable_attr_name):
            error_message += ", but found attribute " + repr(repeatable_attr_name)
        try:
            arg_reprs = dict(mc_object_repr_and_type=repr(self.mc_object) + ", object of type: " + repr(type(self.mc_object)), attr_name=repr(self.attr_name))
        except:  # pylint: disable=bare-except
            arg_reprs = dict(mc_object_repr_and_type="Object of type: " + repr(type(self.mc_object)), attr_name=repr(self.attr_name))

        return error_message % arg_reprs

    def __str__(self):
        return self.message


def _user_file_line(up_level_start=1):
    frame = sys._getframe(up_level_start)
    while 1:
        if frame.f_globals['__package__'] != 'multiconf':
            return frame.f_globals['__file__'].rstrip('c'), frame.f_lineno
        frame = frame.f_back

    raise Exception("Internal error")


def _line_msg(up_level=2, ufl=None, msg=''):
    """ufl is a tuple of filename, linenumber referece to user code"""
    ufl = ufl or _user_file_line(up_level+1)
    print(('File "%s", line %d' % ufl) + (', ' + msg if msg else ''), file=sys.stderr)


def _error_type_msg(num_errors, message):
    print('ConfigError:', message, file=sys.stderr)
    return num_errors + 1


def _error_msg(num_errors, message, up_level=2, ufl=None):
    _line_msg(up_level, ufl)
    return _error_type_msg(num_errors, message)


def _warning_type_msg(num_warnings, message):
    print('ConfigWarning:', message, file=sys.stderr)
    return num_warnings + 1

def _warning_msg(num_warnings, message, up_level=2, ufl=None):
    _line_msg(up_level, ufl)
    return _warning_type_msg(num_warnings, message)


def _api_error_type_msg(num_warnings, message):
    print('MultiConfApiError:', message, file=sys.stderr)
    return num_warnings + 1


def _api_error_msg(num_errors, message, up_level=2, ufl=None):
    _line_msg(up_level, ufl)
    return _api_error_type_msg(num_errors, message)

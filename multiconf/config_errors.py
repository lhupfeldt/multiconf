# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys


class ConfigBaseException(Exception):
    is_summary = False


class ConfigDefinitionException(ConfigBaseException):
    def __init__(self, msg):
        super(ConfigDefinitionException, self).__init__(msg)


class ConfigException(ConfigBaseException):
    def __init__(self, msg, is_summary=False):
        super(ConfigException, self).__init__(msg)
        self.is_summary = is_summary


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


def caller_file_line(up_level=2):
    frame = sys._getframe(up_level)
    return frame.f_globals['__file__'], frame.f_lineno


def find_user_file_line(up_level_start=2):
    frame = sys._getframe(up_level_start)
    while 1:
        if frame.f_globals['__package__'] != 'multiconf':
            return frame.f_globals['__file__'], frame.f_lineno
        frame = frame.f_back


def _line_msg(up_level=2, file_name=None, line_num=None, msg=''):
    """ufl is a tuple of filename, linenumber referece to user code"""
    if file_name is None:
        file_name, line_num = find_user_file_line(up_level + 1)
    file_name = file_name.rstrip('c')  # file_name may point to the *.pyc file
    return ('File "%s", line %d' % (file_name, line_num)) + (', ' + msg if msg else '')


def _error_msg(message):
    return 'ConfigError: ' + message


def _warning_msg(message):
    return 'ConfigWarning: ' + message


def _api_error_msg(message):
    return 'MultiConfApiError: ' + message
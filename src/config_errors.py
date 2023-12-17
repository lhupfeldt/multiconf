# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys


class ConfigBaseException(Exception):
    is_summary = False
    is_fatal = False


class ConfigDefinitionException(ConfigBaseException):
    def __init__(self, msg):
        super().__init__(msg)


class ConfigException(ConfigBaseException):
    def __init__(self, msg, is_summary=False, is_fatal=False):
        super().__init__(msg)
        self.is_summary = is_summary
        self.is_fatal = is_fatal


class InvalidUsageException(ConfigBaseException):
    pass


class ConfigApiException(ConfigBaseException):
    pass


class ConfigAttributeError(AttributeError):
    def __init__(self, mc_object, attr_name, msg):
        super().__init__("")
        self.mc_object = mc_object
        self.attr_name = attr_name
        self.msg = msg

    @property
    def message(self):
        error_message = "%(item_repr_and_type)s has no attribute %(attr_name)s."
        if self.msg:
            error_message += ' ' + self.msg
        try:
            rep = self.mc_object.json(compact=True, property_methods=True, builders=False, depth=1) + ", object"
        except:  # pylint: disable=bare-except
            rep = "Object"
        return error_message % dict(item_repr_and_type=rep + " of type: " + repr(type(self.mc_object)), attr_name=repr(self.attr_name))

    def __str__(self):
        return self.message


class ConfigExcludedAttributeError(ConfigAttributeError):
    def __init__(self, mc_object, attr_name, env):
        super().__init__(mc_object, attr_name, None)
        self.env = env
        try:
            self.value = mc_object._mc_attributes[attr_name].env_values[env]
        except KeyError:
            self.value = None

    @property
    def message(self):
        error_message = "Accessing attribute '{attr_name}' for {env} on an excluded config item: {item_excl_repr}"
        return error_message.format(attr_name=self.attr_name, env=self.env, item_excl_repr=self.mc_object._mc_excl_repr())


class ConfigExcludedKeyError(KeyError):
    def __init__(self, mc_object, key_name):
        super().__init__(key_name)
        self.mc_object = mc_object
        self.key_name = key_name

    @property
    def message(self):
        error_message = "'{key_name}'. '{item_excl_repr}' for {env}."
        return error_message.format(key_name=self.key_name, item_excl_repr=self.mc_object._mc_excl_repr(), env=self.mc_object.env)

    def __str__(self):
        return self.message


def caller_file_line(up_level=2):
    """Return the file and line of the caller of the function calling this function (depending on up_level)"""
    frame = sys._getframe(up_level)
    return frame.f_globals['__file__'], frame.f_lineno


def find_user_file_line(up_level_start=2):
    frame = sys._getframe(up_level_start)
    while 1:
        if frame.f_globals['__package__'] != 'multiconf':
            return frame.f_globals['__file__'], frame.f_lineno
        frame = frame.f_back


def _line_msg(up_level=2, file_name=None, line_num=None, msg=''):
    """Generate the file:line information for error messages.

    Arguments:
        up_level (int): If file_name is None then automatically determine the file and line 'up_level' stack frames up from here.
        file_name (str): File name of user config with error.
        line_num (int): Line number of user config with error.
    """

    if file_name is None:
        file_name, line_num = find_user_file_line(up_level + 1)
    file_name = file_name.rstrip('c')  # file_name may point to the *.pyc file
    return ('File "%s", line %d' % (file_name, line_num)) + (', ' + msg if msg else '')


def _error_msg(message):
    return 'ConfigError: ' + message


def _warning_msg(message):
    return 'ConfigWarning: ' + message


failed_property_call_msg = "Attribute '{attr}' is defined as a multiconf attribute and as a @property method but value is undefined for {env} and @property method call failed with: {ex}"

not_repeatable_in_parent_msg = "'{repeatable_cls_key}': {repeatable_cls} is defined as repeatable, but this is not defined as a repeatable item in the containing class: '{ci_named_as}': {ci_cls}"
repeatable_in_parent_msg = "'{named_as}': {cls} is not defined as repeatable, but this is defined as a repeatable item in the containing class: {ci_item}"

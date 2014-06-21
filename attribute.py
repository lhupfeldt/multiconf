# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .config_errors import NoAttributeException, _error_type_msg as error_msg, _line_msg as line_msg, _error_msg, _warning_msg
from .values import _mc_invalid_values


class Attribute(object):
    def __init__(self, attribute_name, _mc_override=False):
        self.attribute_name = attribute_name
        self.env_values = {}
        self.num_errors = 0
        self.num_warnings = 0
        self._mc_frozen = False
        self._mc_override = _mc_override

    def validate_types(self, env_name, value):
        # Validate that an attribute has the same type for all envs
        val = value[0]
        if val is None or val in _mc_invalid_values:
            return

        v_type = type(val)
        for other_env, other_value in self.env_values.iteritems():
            other_val = other_value[0]
            if other_val is None or other_val in _mc_invalid_values:
                continue

            o_type = type(other_val)
            if v_type != o_type:
                line_msg(ufl=value[1], msg=env_name + ' ' + repr(v_type))
                other_env_name = other_env if isinstance(other_env, str) else other_env.name
                line_msg(ufl=other_value[1], msg=other_env_name + ' ' + repr(o_type))
                msg = "Found different value types for property " + repr(self.attribute_name) + " for different envs"
                self.num_errors = error_msg(self.num_errors, msg)

    def has_default(self):
        has_default = 'default' in self.env_values or '__init__' in self.env_values
        return False if not has_default else self.default_value()[0] not in _mc_invalid_values

    def default_value(self):
        """Must not be called unless 'has_default' is true"""
        for default_key in 'default', '__init__':
            if default_key in self.env_values:
                return self.env_values[default_key]
        raise Exception('Internal error')

    def _mc_freeze(self):
        return True

    def _user_validate_recursively(self):
        pass

    def _mc_value(self, current_env):
        """This is only guaranteed to return a correct value for the currently instantiated env!"""
        self._mc_frozen = True

        if current_env in self.env_values:
            return self.env_values[current_env][0]

        if self.has_default():
            return self.default_value()[0]

        raise NoAttributeException("Attribute " + repr(self.attribute_name) + " undefined for env " + repr(current_env))

    def error(self, msg):
        self.num_errors = _error_msg(self.num_errors, msg)

    def warning(self, msg):
        self.num_warnings = _warning_msg(self.num_warnings, msg)

    def __repr__(self):
        return self.__class__.__name__ + ': ' + repr(self.attribute_name) + ':' + ('frozen' if self._mc_frozen else 'not-frozen') + ", values: " + repr(self.env_values)

    def merge(self, other):
        for env, value in other.env_values.iteritems():
            self.env_values.setdefault(env, value)
        return self

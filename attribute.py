# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .config_errors import _error_type_msg as error_msg, _line_msg as line_msg

class Attribute(object):
    def __init__(self, attribute_name):
        self.attribute_name = attribute_name
        self.env_values = {}
        self.num_errors = 0
        self._frozen = False
        self.all_envs_initialized = False

    def validate_types(self, env_name, value):
        # Validate that an attribute has the same type for all envs
        v_type = type(value[0])
        if v_type != type(None):
            for other_env, other_value in self.env_values.iteritems():
                o_type = type(other_value[0])
                if v_type != o_type and other_value[0] is not None:
                    line_msg(ufl=value[1], msg=env_name + ' ' + repr(v_type))
                    other_env_name = other_env if isinstance(other_env, str) else other_env.name
                    line_msg(ufl=other_value[1], msg=other_env_name + ' ' + repr(o_type))
                    msg = "Found different value types for property " + repr(self.attribute_name) + " for different envs"
                    self.num_errors = error_msg(self.num_errors, msg)
            
    def has_default(self):
        return 'default' in self.env_values or '__init__' in self.env_values

    def default_value(self):
        for default_key in 'default', '__init__':
            if default_key in self.env_values:
                return self.env_values[default_key]
        raise Exception('No default value')

    def __repr__(self):
        return self.__class__.__name__ + ': ' + repr(self.attribute_name) + ':' + ('frozen' if self._frozen else 'not-frozen') + ' ' \
            + ('all-envs-initialized' if self.all_envs_initialized else 'not-all-envs-initialized') + ", values: " + repr(self.env_values)

    def env_value(self, env):
        return self.env_values[env]

    def freeze(self):
        self._frozen = True
# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .values import _MC_NO_VALUE
from .bits import int_to_bin_str


# Ordered values!
mc_where_from_nowhere = 0
mc_where_from_init = 1
mc_where_from_mc_init = 2
mc_where_from_with = 3


def where_from_name(where_from):
    if where_from == mc_where_from_nowhere:
        return "from_nowhere"
    if where_from == mc_where_from_init:
        return "from_init"
    if where_from == mc_where_from_with:
        return "from_with"
    if where_from == mc_where_from_mc_init:
        return "from_mc_init"
    raise Exception("Not a where_from value:" + repr(where_from))


class Attribute(object):
    def __init__(self, name, override_method=False):
        self.name = name
        self._value = _MC_NO_VALUE
        self.envs_set_mask = 0
        self.value_from_eg_bit = 0
        self.where_from = mc_where_from_nowhere
        self.file_name = None
        self.line_num = None
        self._mc_frozen = False
        self.override_method = override_method

    def all_set(self, mask):
        return (self.envs_set_mask & mask) == mask

    def _mc_freeze(self):
        return True

    def _user_validate_recursively(self):
        pass

    def set_env_provided(self, eg):
        """Update that a value was available for env, but don't update value since this might not be the current env."""
        self.envs_set_mask |= eg.mask

    def set_current_env_value(self, value, current_eg, where_from, file_name, line_num):
        """A value is available for current env, current_eg may be a group containing current env."""
        self._value = value
        self.where_from = where_from
        self.file_name = file_name
        self.line_num = line_num
        self.value_from_eg_bit = current_eg.bit

    def set_invalid_value(self, value, eg, where_from, file_name, line_num):
        """An MC_TODO value is provided for env, env may be a group containing current env."""
        if not hasattr(self, 'invalid_values'):
            self.invalid_values = []
        self.invalid_values.append((value, eg, where_from, file_name, line_num))

    def _mc_value(self):
        """Freeze and return value"""
        if self._value != _MC_NO_VALUE:
            self._mc_frozen = True
        return self._value

    def mask_to_str(self):
        return int_to_bin_str(self.envs_set_mask)

    def __repr__(self):
        return self.__class__.__name__ + ': ' + repr(self.name) + ':' + ('frozen' if self._mc_frozen else 'not-frozen') + \
            ", value: " + repr(self._value) + " " + self.mask_to_str() + ", " + repr(self.file_name) + ':' + repr(self.line_num) + ' ' + where_from_name(self.where_from)

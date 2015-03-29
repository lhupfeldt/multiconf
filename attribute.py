# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from enum import Enum

from .values import _MC_NO_VALUE
from .bits import int_to_bin_str


class Where(Enum):
    # Ordered values!
    NOWHERE = 0
    IN_INIT = 1
    IN_MC_INIT = 2
    IN_BUILD = 3
    IN_WITH = 4

    def __lt__(self, other):
        return self.value < other.value


class Attribute(object):
    def __init__(self, name, override_method):
        self.name = name
        self.override_method = override_method
        self._value = _MC_NO_VALUE
        self.envs_set_mask = 0
        self.value_from_eg_bit = 0
        self.where_from = Where.NOWHERE
        self.file_name = None
        self.line_num = None
        self._mc_frozen = False

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

    def override(self, other, current_env):
        """Override self with value of other if other sets value for current env, otherwise just update envs_set_mask"""
        if other.envs_set_mask & current_env.bit:
            self._value = other._value
            self.value_from_eg_bit = other.value_from_eg_bit
            self.where_from = other.where_from
            self.file_name = other.file_name
            self.line_num = other.line_num

        self.envs_set_mask |= other.envs_set_mask
        self._mc_frozen = other._mc_frozen or self._mc_frozen
        return self

    def _mc_value(self):
        """Freeze and return value"""
        if self._value != _MC_NO_VALUE:
            self._mc_frozen = True
        return self._value

    def mask_to_str(self):
        return int_to_bin_str(self.envs_set_mask)

    def __repr__(self):
        return self.__class__.__name__ + ': ' + repr(self.name) + ':' + ('frozen' if self._mc_frozen else 'not-frozen') + \
            ", value: " + repr(self._value) + " " + self.mask_to_str() + ", " + repr(self.file_name) + ':' + repr(self.line_num) + ' ' + str(self.where_from)


def new_attribute(name):
    if name.endswith('!'):
        name = name[:-1]
        return Attribute(name, override_method=True), name
    return Attribute(name, override_method=False), name

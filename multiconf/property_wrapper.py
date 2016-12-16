# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


class _McPropertyWrapper(object):
    __slots__ = ('prop_name', 'prop')

    def __init__(self, prop_name, prop):
        self.prop_name = prop_name
        self.prop = prop

    def __get__(self, obj, objtype):
        current_env = obj._mc_root._mc_env
        env_values = obj._mc_attributes[self.prop_name].env_values
        if current_env in env_values:
            return env_values[current_env]
        return self.prop.__get__(obj, objtype)

    def __set__(self, obj, val):
        raise Exception("Not settable")

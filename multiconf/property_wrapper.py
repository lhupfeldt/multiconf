# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


class _McPropertyWrapperException(AttributeError):
    def __init__(self, cause):
        self.cause = cause


class _McPropertyWrapper(object):
    __slots__ = ('prop_name', 'prop')

    def __init__(self, prop_name, prop):
        self.prop_name = prop_name
        self.prop = prop

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        try:
            env_values = obj._mc_attributes[self.prop_name].env_values
        except KeyError:
            # @property is not overwritten for current instance
            pass
        else:
            current_env = obj._mc_root._mc_env
            if current_env in env_values:
                return env_values[current_env]

        try:
            return self.prop.__get__(obj, objtype)
        except Exception as ex:
            raise _McPropertyWrapperException(ex)

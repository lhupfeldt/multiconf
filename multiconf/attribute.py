# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from enum import Enum

from .config_errors import ConfigAttributeError, ConfigExcludedAttributeError, ConfigApiException
from .envs import NO_ENV, thread_local


class Where(Enum):
    NOWHERE = 0
    IN_INIT = 1
    IN_RE_INIT = 2
    IN_MC_INIT = 3
    IN_MC_BUILD = 4
    IN_WITH = 5
    IN_RE_WITH = 6
    FROZEN = 7


class _McAttribute(object):
    "Give property access to env specific values"
    __slots__ = ('env_values', 'where_from', 'from_eg')

    def __init__(self):
        self.env_values = {}
        self.where_from = Where.NOWHERE

    def set(self, env, value, where_from, from_eg):
        self.env_values[env] = value
        self.where_from = where_from
        self.from_eg = from_eg


class _McAttributeAccessor(object):
    __slots__ = ('attr_name', 'attr')

    def __init__(self, attr_name):
        self.attr_name = attr_name

    def __get__(self, obj, objtype):
        if not obj:
            if obj is None:
                return self

            cr = obj._mc_root
            current_env = thread_local.env
            if cr._mc_config_loaded:
                raise ConfigExcludedAttributeError(obj, self.attr_name, current_env)

        cr = obj._mc_root
        current_env = thread_local.env

        try:
            mc_attribute = obj._mc_attributes[self.attr_name]
            if not cr._mc_in_json:
                mc_attribute.where_from = Where.FROZEN
            return mc_attribute.env_values[current_env]
        except KeyError as ex:
            # mc attribute does not exist for current instance or current env
            if current_env is NO_ENV:
                msg = "Trying to access attribute '{}'. "
                msg += "Item.attribute access is not allowed in 'mc_post_validate' as there is no current env, use: item.getattr(attr_name, env)"
                raise ConfigApiException(msg.format(self.attr_name))

            if not obj:
                raise ConfigExcludedAttributeError(obj, self.attr_name, current_env)

            raise ConfigAttributeError(obj, self.attr_name, '')

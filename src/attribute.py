# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from enum import Enum

from .config_errors import ConfigAttributeError, ConfigExcludedAttributeError, ConfigApiException
from .thread_state import thread_local
from .envs import MC_NO_ENV
from .values import MC_TODO


class Where(Enum):
    NOWHERE = 0
    IN_INIT = 1
    IN_RE_INIT = 2
    IN_MC_INIT = 3
    IN_MC_BUILD = 4
    IN_WITH = 5
    IN_RE_WITH = 6
    FROZEN = 7


class _McAttribute():
    "Give property access to env specific values"
    __slots__ = ('env_values', 'where_from', 'from_eg')

    def __init__(self):
        self.env_values = {}
        self.where_from = Where.NOWHERE

    def set(self, env, value, where_from, from_eg):
        self.env_values[env] = value
        self.where_from = where_from
        self.from_eg = from_eg


class _McAttributeAccessor():
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
            val = mc_attribute.env_values[current_env]
            if not cr._mc_in_json:
                mc_attribute.where_from = Where.FROZEN
                if val == MC_TODO:
                    raise ConfigAttributeError(obj, self.attr_name, 'Trying got get {}.'.format(MC_TODO.name))
            return val
        except KeyError as ex:
            # mc attribute does not exist for current instance or current env
            if current_env is MC_NO_ENV:
                msg = "Trying to access attribute '{attr_name}'. "
                if cr._mc_in_post_validate:
                    msg += "Item.attribute access is not allowed in 'mc_post_validate' as there is no current env. "
                else:
                    msg += "Item.attribute access is not allowed when config is instantiated with 'MC_NO_ENV'. "
                msg += "Use: item.attr_env_items('{attr_name}') or item.getattr('{attr_name}', <env>)"
                raise ConfigApiException(msg.format(attr_name=self.attr_name))

            if not obj:
                raise ConfigExcludedAttributeError(obj, self.attr_name, current_env)

            raise ConfigAttributeError(obj, self.attr_name, '')

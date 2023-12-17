# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .config_errors import ConfigExcludedKeyError


class AndTrue():
    def __and__(self, other):
        return True


class RepeatableDict():
    """Dictionary dedicated for holding RepeatableConfigItem.

    A ConfigItem may be excluded from some envs. This class works as a simplified dict, but behaves in an env specific manner
    excluding items which are excluded in the current env.
    """

    _mc_handled_env_bits = AndTrue()

    __slots__ = ('_all_items',)  # Referenced in multiconf.py
    __class__ = dict

    def __init__(self):
        self._all_items = {}

    def __getitem__(self, key):
        val = self._all_items[key]
        if val._mc_exists_in_env():
            return val
        raise ConfigExcludedKeyError(val, key)

    def __contains__(self, key):
        val = self._all_items.get(key)
        if val is not None and val._mc_exists_in_env():
            return True
        return False

    def get(self, key, default=None):
        val = self._all_items.get(key)
        if val is not None and val._mc_exists_in_env():
            return val
        return default

    def __eq__(self, other):
        return self is other or len(self) == 0 and len(other) == 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        yield from self.keys()

    def items(self):
        for key, val in self._all_items.items():
            if val._mc_exists_in_env():
                yield key, val

    def keys(self):
        for key, val in self._all_items.items():
            if val._mc_exists_in_env():
                yield key

    def values(self):
        for _, val in self._all_items.items():
            if val._mc_exists_in_env():
                yield val

    def __len__(self):
        count = 0
        for _, val in self._all_items.items():
            if val._mc_exists_in_env():
                count += 1
        return count

    def __bool__(self):
        for _, val in self._all_items.items():
            if val._mc_exists_in_env():
                return True

        return False

    def __repr__(self):
        return repr(dict(((key, val) for (key, val) in self._all_items.items() if val._mc_exists_in_env())))

    def _mc_call_mc_validate_recursively(self, env):
        """Call the user defined 'mc_validate' methods on all items"""

        for _, item in self._all_items.items():
            if item._mc_exists_in_given_env(env):
                item._mc_call_mc_validate_recursively(env)

    def _mc_validate_properties_recursively(self, env):
        """Call '_mc_validate_properties_recursively' methods on all items"""

        for _, item in self._all_items.items():
            if item._mc_exists_in_given_env(env):
                item._mc_validate_properties_recursively(env)

    def _mc_call_mc_post_validate_recursively(self):
        """Call the user defined 'mc_post_validate' methods on all items, including excluded items as there is no current env."""

        for _, item in self._all_items.items():
            item._mc_call_mc_post_validate_recursively()

    @property
    def all_items(self):
        """Return the underlying dict holding all items, including items excluded from current env.

        This can be used in applications which need access to the ConfigItems from all envs.
        Modifications are not allowed!
        """

        return self._all_items

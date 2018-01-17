# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict

from .config_errors import ConfigExcludedKeyError


class RepeatableDict(object):
    """Dictionary dedicated for holding RepeatableConfigItem.

    A ConfigItem may be excluded from some envs. This class works as a simplified OrderedDict, but behaves in an env specific manner
    excluding items which are excluded in the current env.
    """

    __slots__ = ('_all_items',)  # Referenced in multiconf.py
    __class__ = OrderedDict

    def __init__(self):
        self._all_items = OrderedDict()

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
        for key in self.keys():
            yield key

    def items(self):
        for key, val in self._all_items.items():
            if val._mc_exists_in_env():
                yield key, val

    # Python2 compatibility
    iteritems = items

    def keys(self):
        for key, val in self._all_items.items():
            if val._mc_exists_in_env():
                yield key

    # Python2 compatibility
    iterkeys = keys

    def values(self):
        for _, val in self._all_items.items():
            if val._mc_exists_in_env():
                yield val

    # Python2 compatibility
    itervalues = values

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

    # Python2 compatibility
    __nonzero__ = __bool__

    def __repr__(self):
        return repr(OrderedDict(((key, val) for (key, val) in self._all_items.items() if val._mc_exists_in_env())))

    def _update_mc_excluded_recursively(self, mc_excluded_mask):
        for item in self._all_items.values():
            item._update_mc_excluded_recursively(mc_excluded_mask)

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
        """Return the underlying OrderedDict holding all items, including items excluded from current env.

        This can be used in applications which need access to the ConfigItems from all envs.
        Modifications are not allowed!
        """

        return self._all_items

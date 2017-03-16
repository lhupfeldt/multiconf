# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict


class RepeatableDict(object):
    """Dictionary dedicated for holding RepeatableConfigItem"""
    __slots__ = ('_items',)
    __class__ = OrderedDict

    def __init__(self):
        self._items = OrderedDict()

    def __setitem__(self, key, val):
        self._items[key] = val

    def __getitem__(self, key):
        val = self._items[key]
        if val._mc_exists_in_env():
            return val
        raise KeyError(key)

    def __contains__(self, key):
        val = self._items.get(key)
        if val is not None and val._mc_exists_in_env():
            return True
        return False

    def get(self, key, default=None):
        val = self._items.get(key)
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
        for key, val in self._items.items():
            if val._mc_exists_in_env():
                yield key, val

    iteritems = items

    def keys(self):
        for key, val in self._items.items():
            if val._mc_exists_in_env():
                yield key

    def values(self):
        for _, val in self._items.items():
            if val._mc_exists_in_env():
                yield val

    def __len__(self):
        count = 0
        for _, val in self._items.items():
            if val._mc_exists_in_env():
                count += 1
        return count

    def __repr__(self):
        return repr(OrderedDict(((key, val) for (key, val) in self._items.items() if val._mc_exists_in_env())))

    def _mc_call_post_validate_recursively(self):
        """Call the user defined 'mc_post_validate' methods on all items"""
        for item in self.values():
            item._mc_call_post_validate_recursively()


a = RepeatableDict()
assert isinstance(a, dict)

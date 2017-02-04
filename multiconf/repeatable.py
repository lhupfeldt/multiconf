# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict


class RepeatableDict(OrderedDict):
    """Dictionary dedicated for holding RepeatableConfigItem"""

    def __init__(self, attr_name, obj):
        super(RepeatableDict, self).__init__()
        self.attr_name = attr_name
        self.obj = obj

    def __get__(self, obj, objtype):
        if obj._mc_root._mc_config_loaded:
            return OrderedDict(((key, val) for (key, val) in obj.__dict__[self.attr_name].items() if val and val._mc_exists_in_env()))
        return obj.__dict__[self.attr_name]

    def __set__(self, obj, val):
        if not isinstance(val, RepeatableDict):
            raise AttributeError("Not settable: " + self.attr_name)
        obj.__dict__[val.attr_name] = val

    def items(self):
        for (key, val) in super(RepeatableDict, self.obj.__dict__[self.attr_name]).items():
            if val and val._mc_exists_in_env():
                yield key, val

    iteritems = items

    def keys(self):
        for (key, val) in super(RepeatableDict, self.obj.__dict__[self.attr_name]).items():
            if val and val._mc_exists_in_env():
                yield key

    def values(self):
        for val in super(RepeatableDict, self.obj.__dict__[self.attr_name]).values():
            if val and val._mc_exists_in_env():
                yield val

    def __len__(self):
        count = 0
        for val in super(RepeatableDict, self.obj.__dict__[self.attr_name]).values():
            if val and val._mc_exists_in_env():
                count += 1
        return count

    def _mc_call_post_validate_recursively(self):
        """Call the user defined 'mc_post_validate' methods on all items"""
        for item in self.values():
            item._mc_call_post_validate_recursively()

    def _mc_is_excluded(self):
        return False

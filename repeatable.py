# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

from .excluded import Excluded


class Repeatable(OrderedDict):
    _mc_frozen = False

    def _mc_freeze(self):
        self._mc_frozen = True
        for item in self.itervalues():
            self._mc_frozen &= item._mc_freeze()
        return self._mc_frozen

    def _user_validate_recursively(self):
        for dict_entry in self.values():
            dict_entry._user_validate_recursively()

    def _mc_value(self):
        return self


class UserRepeatable(Repeatable):
    _mc_frozen = False

    def __init__(self, item):
        super(UserRepeatable, self).__init__()
        self.item = item
        self._mc_is_excluded = False

    def __getitem__(self, key):
        try:
            return super(UserRepeatable, self).__getitem__(key)
        except KeyError:
            if not self.item.root_conf._mc_config_loaded and self._mc_is_excluded:
                return Excluded(self.item)
            raise

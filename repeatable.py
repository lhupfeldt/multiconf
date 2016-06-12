# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

from .excluded import Excluded


class Repeatable(OrderedDict):
    _mc_frozen = False

    def _mc_freeze(self, previous_child):
        self._mc_frozen = True
        for item in self.values():
            self._mc_frozen &= item._mc_freeze(previous_child)
        return self._mc_frozen

    def _user_validate_recursively(self):
        for dict_entry in self.values():
            dict_entry._user_validate_recursively()

    def _mc_value(self):
        return self


class UserRepeatable(Repeatable):
    _mc_frozen = False

    def __init__(self, *args, **kwds):
        super(UserRepeatable, self).__init__(*args, **kwds)
        self.contained_in = None
        self._mc_is_excluded = False

    def copy(self):
        res = super(UserRepeatable, self).copy()
        res.contained_in = self.contained_in
        res._mc_is_excluded = self._mc_is_excluded
        return res

    def __getitem__(self, key):
        try:
            return super(UserRepeatable, self).__getitem__(key)
        except KeyError:
            if not self.contained_in.root_conf._mc_config_loaded and self._mc_is_excluded:
                return Excluded(self.contained_in)
            raise

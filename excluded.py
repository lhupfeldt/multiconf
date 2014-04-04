# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


class Excluded(object):
    _mc_frozen = True

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return "Excluded: " + repr(type(self.item))

    def __nonzero__(self):
        return False

    def _mc_freeze(self):
        return True

    def _user_validate_recursively(self):
        pass

    def _mc_value(self, _current_env):
        return self

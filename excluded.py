# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from . config_errors import ConfigException


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

    def _mc_value(self):
        return self

    def __getattr__(self, name):
        if self.item.root_conf.frozen:
            raise ConfigException("Accessing attribute " + repr(name) + " on an excluded object:", self.item)
        return self

    def __getitem__(self, key):
        if self.item.root_conf.frozen:
            raise ConfigException("Accessing key " + repr(key) + " on an excluded repeatable object:", self.item)
        return self

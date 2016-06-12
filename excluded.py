# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from . config_errors import ConfigException


class Excluded(object):
    __slots__ = ("_repr", "_mc_root_conf", "__weakref__")

    def __init__(self, excluded_item):
        self._repr = "Excluded: " + repr(type(excluded_item))
        self._mc_root_conf = excluded_item._mc_root_conf

    def __repr__(self):
        return self._repr

    def __bool__(self):
        return False

    # Python2 compatibility
    __nonzero__ = __bool__

    def _mc_freeze(self, previous_child):
        return True

    def _user_validate_recursively(self):
        pass

    def _mc_value(self):
        return self

    def __getattr__(self, name):
        if self._mc_root_conf._mc_config_loaded:
            raise ConfigException("Accessing attribute " + repr(name) + " on an excluded object:", self)
        return self

    def __getitem__(self, key):
        if self._mc_root_conf._mc_config_loaded:
            raise ConfigException("Accessing [key] " + repr(key) + " on an excluded object:", self)
        return self

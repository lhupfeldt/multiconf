# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from enum import Enum


class McInvalidValue(Enum):
    MC_NO_VALUE = 0
    MC_REQUIRED = 1
    MC_TODO = 2

    def __bool__(self):
        return False

    # Python2 compatibility
    __nonzero__ = __bool__

    def __repr__(self):
        return self.name

    def json_equivalent(self):
        return self.__repr__()

    def __add__(self, _):
        return self

    def __radd__(self, _):
        return self

    def append(self, _):
        return self


MC_REQUIRED = McInvalidValue.MC_REQUIRED
MC_TODO = McInvalidValue.MC_TODO
_MC_NO_VALUE = McInvalidValue.MC_NO_VALUE

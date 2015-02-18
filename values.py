# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


class MCInvalidValue(object):
    def __init__(self, name):
        self.name = name

    def __bool__(self):
        return False

    # Python2 compatibility
    __nonzero__ = __bool__

    def __repr__(self):
        return self.name

    def json_equivalent(self):
        return self.__repr__()


MC_REQUIRED = MCInvalidValue("MC_REQUIRED")
MC_TODO = MCInvalidValue("MC_TODO")
_MC_NO_VALUE = MCInvalidValue("_MC_NO_VALUE")

_mc_invalid_values = (MC_REQUIRED, MC_TODO, _MC_NO_VALUE)

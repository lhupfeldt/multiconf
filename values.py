# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


class MCRequired(object):
    def __nonzero__(self):
        return False

    def __repr__(self):
        return "MC_REQUIRED"
    
    def json_equivalent(self):
        return self.__repr__()


MC_REQUIRED = MCRequired()

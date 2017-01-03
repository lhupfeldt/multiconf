# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from enum import Enum


class Where(Enum):
    NOWHERE = 0
    IN_INIT = 1
    IN_MC_INIT = 2
    IN_WITH = 3


class _McAttribute(object):
    "Give property access to env specific values"
    __slots__ = ('env_values', 'where_from', 'from_eg')

    def __init__(self):
        self.env_values = {}
        self.where_from = Where.NOWHERE

    def set(self, env, value, where_from, from_eg):
        self.env_values[env] = value
        self.where_from = where_from
        self.from_eg = from_eg

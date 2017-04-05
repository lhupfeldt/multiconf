# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import abc

from multiconf import RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as


@named_as('someitems')
@nested_repeatables('someitems')
class _NamedNestedRepeatable(RepeatableConfigItem, metaclass=abc.ABCMeta):
    def __new__(cls, name):
        return super(_NamedNestedRepeatable, cls).__new__(cls, mc_key=name)

    def __init__(self, name):
        super(_NamedNestedRepeatable, self).__init__(mc_key=name)
        self.name = name
        self.x = 3

    @abc.abstractproperty
    def m(self):
        pass

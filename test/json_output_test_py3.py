# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import abc

from .. import ConfigItem
from ..decorators import nested_repeatables, named_as, repeat


@named_as('someitems')
@nested_repeatables('someitems')
@repeat()
class _NamedNestedRepeatable(ConfigItem, metaclass=abc.ABCMeta):
    def __init__(self, name):
        super(_NamedNestedRepeatable, self).__init__(mc_key=name)
        self.name = name
        self.x = 3
    
    @abc.abstractproperty
    def m(self):
        pass

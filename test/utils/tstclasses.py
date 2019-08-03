# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


from multiconf import ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from multiconf.decorators import named_as


class ItemWithName(ConfigItem):
    def __init__(self, name=MC_REQUIRED):
        super().__init__()
        self.name = name


class ItemWithAA(ConfigItem):
    def __init__(self, aa=MC_REQUIRED):
        super().__init__()
        self.aa = aa


class ItemWithAABB(ConfigItem):
    def __init__(self, aa=MC_REQUIRED, bb=None):
        super().__init__()
        self.aa = aa
        self.bb = bb


@named_as('RepeatableItems')
class RepeatableItemWithAA(RepeatableConfigItem):
    def __init__(self, mc_key, aa=MC_REQUIRED):
        super().__init__(mc_key=mc_key)
        self.aa = aa


class BuilderWithAA(ConfigBuilder):
    def __init__(self, aa=MC_REQUIRED):
        super().__init__()
        self.aa = aa

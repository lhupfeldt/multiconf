# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithName


ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


def test_configbuilders_alternating_with_items_repeatable_multilevel_required():
    class some_item(ConfigItem):
        xx = 1

    class another_item(ConfigItem):
        xx = 2

    @required('some_item')
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, name, some_attribute=MC_REQUIRED):
            super().__init__(mc_key=name)
            self.name = name
            self.some_attribute = some_attribute

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()
            self.some_attribute = MC_REQUIRED

        def mc_build(self):
            InnerItem('innermost', self.some_attribute)

    @nested_repeatables('inners')
    @required('another_item')
    class MiddleItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.id = mc_key
            self.another_attribute = MC_REQUIRED

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super().__init__()
            self.name = name
            self.builder_attribute = MC_REQUIRED

        def mc_build(self):
            with MiddleItem(self.name) as mi:
                mi.setattr('another_attribute', default=9)
                another_item()

    class OuterBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            with MiddleBuilder('base') as mb:
                mb.builder_attribute = 1
                with InnerBuilder() as ib:
                    ib.some_attribute = 1
                    some_item()

    class another_item(ConfigItem):
        xx = 2


    @nested_repeatables('MiddleItems')
    class OuterItem(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName('myp'):
            with OuterItem():
                OuterBuilder()

    cr = config(prod).ItemWithName
    cr.json(builders=True)
    # TODO, verify values

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from ..decorators import nested_repeatables, named_as, required
from ..envs import EnvFactory

from .utils.tstclasses import RootWithName


ef = EnvFactory()
prod = ef.Env('prod')


def test_configbuilders_alternating_with_items_repeatable_multilevel_required():
    class some_item(ConfigItem):
        xx = 1

    class another_item(ConfigItem):
        xx = 2
        
    @required('some_item')
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(mc_key=name)
            self.name = name
            self.some_attribute = MC_REQUIRED

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost')

    @nested_repeatables('inners')
    @required('another_item')
    class MiddleItem(RepeatableConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(mc_key=name)
            self.id = name
            self.another_attribute = MC_REQUIRED

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__()
            self.name = name
            self.builder_attribute = MC_REQUIRED

        def build(self):
            with MiddleItem(name=self.name) as mi:
                mi.setattr('another_attribute', default=9)
                another_item()

    class OuterBuilder(ConfigBuilder):
        def __init__(self):
            super(OuterBuilder, self).__init__()

        def build(self):
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

    with RootWithName(prod, ef) as cr:
        cr.name = 'myp'
        with OuterItem():
            OuterBuilder()

    cr.json(builders=True)
    # TODO

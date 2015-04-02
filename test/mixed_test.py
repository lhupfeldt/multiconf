# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..decorators import nested_repeatables, named_as, repeat, required
from ..envs import EnvFactory


ef = EnvFactory()
prod = ef.Env('prod')


def test_configbuilders_alternating_with_items_repeatable_multilevel_required():
    @repeat()
    @required('some_attribute')
    @named_as('inners')
    class InnerItem(ConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(mc_key=name)
            self.name = name

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost')

    @repeat()
    @nested_repeatables('inners')
    @required('another_attribute')
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(mc_key=name)
            self.id = name

    @required('builder_attribute')
    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__()
            self.name = name

        def build(self):
            with MiddleItem(name=self.name) as mi:
                mi.setattr('another_attribute', default=9)

    class OuterBuilder(ConfigBuilder):
        def __init__(self):
            super(OuterBuilder, self).__init__()

        def build(self):
            with MiddleBuilder('base') as mb:
                mb.builder_attribute = 1
                with InnerBuilder() as ib:
                    ib.some_attribute = 1

    @nested_repeatables('MiddleItems')
    class OuterItem(ConfigItem):
        pass

    with ConfigRoot(prod, ef) as cr:
        cr.name = 'myp'
        with OuterItem():
            OuterBuilder()

    cr.json(builders=True)
    # TODO

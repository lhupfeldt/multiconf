#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..decorators import nested_repeatables, named_as, repeat, required
from ..envs import EnvFactory


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


@named_as('xses')
@repeat()
@nested_repeatables('x_children')
class Xses(ConfigItem):
    pass


@named_as('x_children')
@repeat()
class XChild(ConfigItem):
    pass


def test_configbuilder_override():
    @required('b')
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers=4, **kwargs):
            super(XBuilder, self).__init__(num_servers=num_servers, **kwargs)

        def build(self):
            for server_num in xrange(1, self.num_servers+1):
                with Xses(name='server%d' % server_num, server_num=server_num) as c:
                    c.setattr('something', prod=1, pp=2)
                    c.none_is_not_used = False

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with Root(prod, [prod, pp]) as cr:
        with XBuilder(a=1, something=7) as xb:
            xb.setattr('num_servers', pp=2)
            xb.setattr('b', prod=3, pp=4)
            xb.none_is_not_used = None

    assert len(cr.xses) == 4
    assert cr.xses['server1'].a == 1
    assert cr.xses['server2'].b == 3
    assert cr.xses['server4'].b == 3
    assert cr.xses['server1'].something == 7
    assert cr.xses['server4'].something == 7
    assert cr.xses['server1'].server_num == 1
    assert cr.xses['server3'].server_num == 3
    assert cr.xses['server4'].server_num == 4
    assert cr.xses['server4'].none_is_not_used == False
    # TODO: override of conditional attributes (required_if)


def test_configbuilder_build_at_freeze():
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers=4, **kwargs):
            super(XBuilder, self).__init__(num_servers=num_servers, **kwargs)

        def build(self):
            for server_num in xrange(1, self.num_servers+1):
                with Xses(name='server%d' % server_num) as c:
                    pass

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with Root(prod, [prod, pp]) as cr:
        XBuilder(a=1)

    assert len(cr.xses) == 4
    for ii in 1, 2, 3, 4:
        name = 'server' + repr(ii)
        assert cr.xses[name].name == name


def test_configbuilder_access_to_contained_in_from_build():
    @named_as('y')
    class Y(ConfigItem):
        pass

    class YBuilder(ConfigBuilder):
        def build(self):
            with Y(number=self.contained_in.aaa):
                pass

    @nested_repeatables('ys')
    class Root(ConfigRoot):
        aaa = 7

    with Root(prod, [prod, pp]) as cr:
        YBuilder()

    assert cr.y.number == 7


def test_configbuilder_access_to_contained_in_from___init__():
    @named_as('x')
    class X(ConfigItem):
        pass

    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()
            self.number = self.contained_in.aaa

        def build(self):
            with X(number=self.number):
                pass

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        aaa = 7

    with Root(prod, [prod, pp]) as cr:
        XBuilder()

    assert cr.x.number == 7


def test_configbuilder_access_to_contained_in_from_with_block():
    @named_as('x')
    class X(ConfigItem):
        pass

    class XBuilder(ConfigBuilder):
        def build(self):
            X()

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        aaa = 7

    with Root(prod, [prod, pp]) as cr:
        with XBuilder() as xb:
            parent = xb.contained_in

    assert parent == cr


def test_configbuilder_access_to_contained_in_from_built_item_must_give_parent_of_builder():
    @named_as('x')
    class X(ConfigItem):
        def __init__(self, **kwargs):
            super(X, self).__init__(**kwargs)
            self.init_parent = self.contained_in

        def validate(self):
            self.validate_parent = self.contained_in

    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()
            self.number = self.contained_in.aaa

        def build(self):
            with X(number=self.number):
                pass

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        aaa = 7

    with Root(prod, [prod, pp]) as cr:
        XBuilder()

    assert cr.x.number == 7
    assert cr.x.init_parent == cr
    assert cr.x.validate_parent == cr


def test_configbuilder_nested_items():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()
            self.number = self.contained_in.aaa

        def build(self):
            for num in xrange(1, self.number+1):
                with Xses(name='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        aaa = 2

    with Root(prod, [prod, pp]) as cr:
        with XBuilder() as xb:
            xb.b = 27
            XChild(a=10)
            XChild(a=11)

    assert len(cr.xses) == 2
    for server in 'server1', 'server2':
        index = 10
        for x_child in cr.xses[server].x_children.values():
            assert x_child.a == index
            index += 1
        assert index == 12


def test_configbuilder_nested_items_access_to_contained_in():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()
            # Access to contained_in is allowed here depending on where the object
            # is created, so it is discouraged to use contained_in from init
            self.number = self.contained_in.aaa

        def build(self):
            for num in xrange(1, self.number+1):
                with Xses(name='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        aaa = 2

    with Root(prod, [prod, pp]) as cr:
        with XBuilder() as xb:
            xb.b = 27
            with XChild(a=10) as x1:
                with ConfigItem() as ci:
                    assert ci.contained_in == x1
            XChild(a=11)

    assert len(cr.xses) == 2
    for server in 'server1', 'server2':
        index = 10
        for x_child in cr.xses[server].x_children.values():
            assert x_child.a == index
            index += 1
        assert index == 12


def test_configbuilder_multilevel_nested_items_access_to_contained_in():
    ybuilder_in_build_contained_in = []
    ys_in_init_contained_in = []

    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super(YBuilder, self).__init__()
            self.start = start

        def build(self):
            ybuilder_in_build_contained_in.append(self.contained_in)
            for num in xrange(self.start, self.start + self.contained_in.aaa):
                with Y(name='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    @repeat()
    @nested_repeatables('y_children, ys')
    class Y(ConfigItem):
        def __init__(self, **kwarg):
            super(Y, self).__init__(**kwarg)
            ys_in_init_contained_in.append(self.contained_in)

    @named_as('y_children')
    @repeat()
    class YChild(ConfigItem):
        pass

    with ConfigRoot(prod, [prod, pp]) as cr:
        with ItemWithYs() as item:
            with YBuilder() as yb1:
                yb1.b = 27
                yc10 = YChild(a=10)
                with YBuilder(start=3) as yb2:
                    yb2.c = 28
                    yc11 = YChild(a=11)
                    YChild(a=12)

    assert len(item.ys) == 2
    total = 0
    for server in 'server1', 'server2':
        for y_child in item.ys[server].y_children.values():
            print y_child.a
            assert type(y_child.contained_in) == Y
            total += y_child.a
        for inner_server in 'server3', 'server4':
            for y_child in item.ys[server].ys[inner_server].y_children.values():
                assert type(y_child.contained_in) == Y
                print y_child.a
                total += y_child.a
    assert total == 112, total

    # The item created under the builder with statement will have contained_in == None
    # It may be cloned for insertion under multiple items created in 'build'
    # The cloning is necessery to make sure the contained_in ref actually references the final parent
    assert yc10.contained_in == None
    assert yc11.contained_in == None

    assert len(ybuilder_in_build_contained_in) == 2
    for ci in ybuilder_in_build_contained_in:
        assert ci == item

    assert len(ys_in_init_contained_in) == 4
    for ci in ys_in_init_contained_in:
        assert ci == item


def test_configbuilder_repeated():
    class XBuilder(ConfigBuilder):
        def __init__(self, first=1, last=2):
            super(XBuilder, self).__init__()
            self.first = first
            self.last = last

        def build(self):
            for num in xrange(self.first, self.last+1):
                with Xses(name='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2)
                self.q = self.last

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        aaa = 2

    with Root(prod, [prod, pp]) as cr:
        with XBuilder() as xb1:
            XChild(a=10)
            XChild(a=11)
        with XBuilder(first=3) as xb2:
            xb2.last = 3
            XChild(a=10)

    assert len(cr.xses) == 3
    total_children = 0
    for server in 'server1', 'server2', 'server3':
        index = 10
        for x_child in cr.xses[server].x_children.values():
            assert x_child.a == index
            index += 1
            total_children += 1
    assert total_children == 5

    assert len(xb1.what_built()) == 2
    assert isinstance(xb1.what_built(), OrderedDict) == True
    assert xb1.what_built()['q'] == 2

    assert len(xb2.what_built()) == 2
    assert isinstance(xb2.what_built(), OrderedDict) == True
    assert xb2.what_built()['xses']['server3'].something == 1
    assert xb2.what_built()['q'] == 3


def test_required_attributes_not_required_on_imtermediate_freeze_configbuilder():
    @required('a, b')
    class builder(ConfigBuilder):
        def build(self):
            pass

    with ConfigRoot(prod, [prod]):
        with builder() as ii:
            ii.a = 1
            assert ii.a == 1
            ii.setattr('b', prod=2)
            assert ii.b == 2


def test_configbuilder_child_with_nested_repeatables():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()

        def build(self):
            with Xses():
                XChild()

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with Root(prod, [prod, pp]) as cr:
        XBuilder()

    assert len(cr.xses) == 1
    for x in cr.xses.values():
        assert len(x.x_children) == 1


def test_configbuilder_child_with_declared_but_not_defined_nested_repeatables():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()

        def build(self):
            Xses()

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with Root(prod, [prod, pp]) as cr:
        XBuilder()

    assert len(cr.xses) == 1
    for x in cr.xses.values():
        assert isinstance(x.x_children, OrderedDict)
        assert len(x.x_children) == 0


def test_configbuilders_alternating_with_items():
    @named_as('inners')
    class InnerItem(ConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(name=name)

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost')

    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(id=name)

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__(name=name)

        def build(self):
            with MiddleItem(name=self.name):
                pass

    class OuterItem(ConfigItem):
        pass

    with ConfigRoot(prod, [prod], name='myp') as project:
        with OuterItem():
            with MiddleBuilder('base'):
                InnerBuilder()

    print project.json(compact=True)
    # TODO


def test_configbuilders_alternating_with_items_repeatable_simple():
    @repeat()
    @named_as('inners')
    class InnerItem(ConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(name=name)

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost')

    class OuterBuilder(ConfigBuilder):
        def __init__(self):
            super(OuterBuilder, self).__init__()

        def build(self):
            InnerBuilder()

    @nested_repeatables('inners')
    class OuterItem(ConfigItem):
        pass

    with ConfigRoot(prod, [prod], name='myp') as cr:
        with OuterItem():
            OuterBuilder()

    print cr.json()
    # TODO


def test_configbuilders_alternating_with_items_repeatable_many():
    @repeat()
    @named_as('inners')
    class InnerItem(ConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(name=name)

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost1')
            InnerItem('innermost2')

    @repeat()
    @nested_repeatables('inners')
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(id=name)

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__(name=name)

        def build(self):
            MiddleItem('middleitem1')
            MiddleItem('middleitem2')
            MiddleItem('middleitem3')

    @nested_repeatables('MiddleItems')
    class OuterItem(ConfigItem):
        pass

    with ConfigRoot(prod, [prod], name='myp') as project:
        with OuterItem():
            with MiddleBuilder('base'):
                InnerBuilder()

    print project.json(compact=True)
    # TODO


def test_configbuilders_alternating_with_items_repeatable_multilevel():
    @repeat()
    @named_as('inners')
    class InnerItem(ConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(name=name)

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost')

    @repeat()
    @nested_repeatables('inners')
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(id=name)

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__(name=name)

        def build(self):
            with MiddleItem(name=self.name):
                pass

    class OuterBuilder(ConfigBuilder):
        def __init__(self):
            super(OuterBuilder, self).__init__()

        def build(self):
            with MiddleBuilder('base'):
                InnerBuilder()

    @nested_repeatables('MiddleItems')
    class OuterItem(ConfigItem):
        pass

    with ConfigRoot(prod, [prod], name='myp') as cr:
        with OuterItem():
            OuterBuilder()

    print cr.json(builders=True)
    # TODO

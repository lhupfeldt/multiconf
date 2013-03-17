#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict
from oktest import fail

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..decorators import nested_repeatables, named_as, repeat, required
from ..envs import EnvFactory

ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class root(ConfigRoot):
    pass


@named_as('children')
@repeat()
class rchild(ConfigItem):
    pass


@named_as('recursive_items')
@nested_repeatables('recursive_items')
@repeat()
class NestedRepeatable(ConfigItem):
    pass


@named_as('xses')
@repeat()
class Xses(ConfigItem):
    pass


@named_as('x_children')
@repeat()
class XChild(ConfigItem):
    pass



def test_contained_in_root_conf():
    with ConfigRoot(prod, [prod]) as conf:
        assert conf.root_conf == conf
        assert conf.contained_in == None

        with ConfigItem() as c1:
            assert c1.root_conf == conf
            assert c1.contained_in == conf

            with ConfigItem() as c2:
                assert c2.root_conf == conf
                assert c2.contained_in == c1


def test_nested_repeatable_items():
    with root(prod, [prod, pp]) as cr:
        with rchild(name="first", aa=1, bb=1) as ci:
            ci.setattr('aa', prod=3)

        with rchild(name="second", aa=4) as ci:
            ci.setattr('bb', prod=2, pp=17)

        with rchild(name="third") as ci:
            ci.setattr('aa', prod=5, pp=18)
            ci.setattr('bb', prod=3, pp=19)

    assert cr.children['first'].bb == 1
    assert cr.children['second'].bb == 2
    assert cr.children['third'].bb == 3

    index = 3
    for ci in cr.children.values():
        assert ci.aa == index
        index += 1


def test_empty_nested_repeatable_items():
    with root(prod, [prod, pp]) as cr:
        pass

    for _ci in cr.children.values():
        fail ("list should be empty")


def test_unnamed_nested_repeatable_item_no_name_or_id():
    with root(prod, [prod, pp]) as cr:
        with rchild(aa=1, bb=1) as ci:
            ci.setattr('aa', prod=3)
        ci_id = id(ci)

    assert cr.children[ci_id].aa == 3


def test_unnamed_nested_repeatable_item_no_default_name_or_id():
    with root(prod, [prod, pp]) as cr:
        with rchild(aa=1, bb=1) as ci:
            ci.setattr('name', prod='somevalue', pp='another')
        ci_id = id(ci)

    assert cr.children[ci_id].aa == 1
    assert cr.children[ci_id].name == 'somevalue'


def test_iteritems_root_attributes():
    with ConfigRoot(prod, [prod, pp], a=1, b=2) as cr:
        pass

    for exp, actual in zip([('a', 1), ('b', 2)], list(cr.iteritems())):
        exp_key, exp_value = exp
        key, value = actual
        assert exp_key == key
        assert exp_value == value


def test_iteritems_item_attributes():
    with ConfigRoot(prod, [prod, pp]):
        with ConfigItem(a=1, b=2) as ci:
            pass

    for exp, actual in zip([('a', 1), ('b', 2)], list(ci.iteritems())):
        exp_key, exp_value = exp
        key, value = actual
        assert exp_key == key
        assert exp_value == value


def test_property_defined_with_same_type_and_none():
    with ConfigRoot(prod, [prod, pp], a=None) as cr:
        cr.setattr('a', prod=1, pp=2)
    assert cr.a == 1


def test_property_defined_with_none_and_same_type():
    with ConfigRoot(prod, [prod, pp], a=1) as cr:
        cr.setattr('a', prod=None, pp=2)
    assert cr.a == None


def test_automatic_freeze_of_child_on_exit():
    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        ConfigItem(something=1)
    assert cr.ConfigItem.something == 1


def test_automatic_freeze_of_previous_sibling():
    with root(prod, [prod, pp], a=0) as rt:
        rchild(id='a', x=18)
        assert rt.children['a'].x == 18


def test_automatic_contained_item_freeze_on_exit():
    @nested_repeatables('recursive_items')
    class root2(ConfigRoot):
        pass

    with root2(prod, [prod, pp], a=0) as cr:
        NestedRepeatable(id='a')
        with NestedRepeatable(id='b') as ci:
            NestedRepeatable(id='a')
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    ci.setattr('a', prod=1, pp=2)
                NestedRepeatable(id='c', something=1)
            NestedRepeatable(id='c', something=2)
        NestedRepeatable(id='c', something=3)

    assert len(cr.recursive_items['a'].recursive_items) == 0
    assert len(cr.recursive_items['b'].recursive_items) == 3
    assert len(cr.recursive_items['c'].recursive_items) == 0

    ids = ['a', 'b', 'c']
    index = 0
    for item_id, item in cr.recursive_items['b'].recursive_items.iteritems():
        assert item.id == ids[index]
        assert item_id == ids[index]
        index += 1
    assert index == 3

    assert cr.recursive_items['b'].recursive_items['b'].recursive_items['b'].a == 1


def test_automatic_freeze_of_property_defined_in_with_statement():
    with root(prod, [prod, pp], a=0):
        with rchild(id='a') as rc:
            rc.setattr('y', prod=1, pp=2)
            assert rc.y == 1


def test_automatic_freeze_of_property_overridden_in_with_statement():
    with root(prod, [prod, pp], a=0):
        with rchild(id='a', y=18) as rc:
            rc.setattr('y', prod=7, pp=2)
            assert rc.y == 7


def test_explicit_freeze_of_all_defined_properties():
    with root(prod, [prod, pp], a=0):
        with rchild(id='a', x=17, z=18) as rc:
            rc.setattr('y', prod=7, pp=2)
            rc.setattr('z', pp=3)

            assert rc.y == 7
            assert rc.x == 17
            assert rc.z == 18


def test_explicit_freeze_of_single_property():
    with root(prod, [prod, pp], a=0):
        with rchild(id='a', x=19, z=20) as rc:
            rc.setattr('y', prod=7, pp=2)
            assert rc.y == 7
            rc.setattr('z', pp=3)
            assert rc.z == 20
            assert rc.x == 19

# TODO: allow this (while inside with statement only)
#def define new attribute after freeze_test(self):
#    with root(prod, [prod, pp], a=0):
#        with rchild(id='a', x=19, z=20) as rc:
#            rc.setattr('y', prod=7, pp=2)
#            assert rc.y == 7
#            rc.setattr('z', pp=3)
#            assert rc.z == 20
#            assert rc.x == 19
#            rc.a(prod=3, pp=4)
#            assert rc.a == 3


def test_find_contained_in_named_as():
    @named_as('x')
    @nested_repeatables('recursive_items')
    class X(ConfigItem):
        pass

    @named_as('y')
    class Y(ConfigItem):
        pass

    @nested_repeatables('recursive_items')
    class root3(ConfigRoot):
        pass

    with root3(prod, [prod, pp], a=0) as cr:
        NestedRepeatable()
        with X() as ci:
            ci.setattr('a', prod=0, pp=2)
            NestedRepeatable(id='a')
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='c')
                with X() as ci:
                    ci.setattr('a', prod=1, pp=2)
                    with NestedRepeatable(id='d') as ci:
                        ci.setattr('a', prod=2, pp=2)
                        with Y() as ci:
                            ci.setattr('a', prod=3, pp=2)

    assert cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='x').a == 1
    assert cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='root3').a == 0
    assert cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='recursive_items').a == 2
    assert cr.x.recursive_items['b'].x.find_contained_in(named_as='x').a == 0


def test_find_attribute_attribute_name():
    @named_as('x')
    @nested_repeatables('recursive_items')
    class X(ConfigItem):
        pass

    @nested_repeatables('recursive_items')
    class root4(ConfigRoot):
        pass

    with root4(prod, [prod, pp], a=-1, q='q0') as cr:
        NestedRepeatable()
        with X() as ci:
            ci.setattr('a', prod=0, pp=20)
            NestedRepeatable(id='a', a=9)
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='c', a=7)
                with X() as ci:
                    ci.setattr('b', prod='b1', pp='b21')
                    with NestedRepeatable(id='d') as ci:
                        ci.setattr('a', prod=2, pp=22)
                        with X() as ci:
                            ci.setattr('a', prod=3, pp=23)

    assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('a') == 3
    assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('b') == 'b1'
    assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('recursive_items')['d'].a == 2
    assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('q') == 'q0'
    assert cr.x.recursive_items['b'].x.find_attribute(attribute_name='a') == 0


def test_configbuilder_override():
    @required('b')
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers=4, **kwargs):
            super(XBuilder, self).__init__(num_servers=num_servers, **kwargs)

        def build(self):
            for server_num in xrange(1, self.num_servers+1):
                with Xses(name='server%d' % server_num, server_num=server_num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with Root(prod, [prod, pp]) as cr:
        with XBuilder(a=1, something=7) as xb:
            xb.setattr('num_servers', pp=2)
            xb.setattr('b', prod=3, pp=4)

    assert len(cr.xses) == 4
    assert cr.xses['server1'].a == 1
    assert cr.xses['server2'].b == 3
    assert cr.xses['server4'].b == 3
    assert cr.xses['server1'].something == 7
    assert cr.xses['server4'].something == 7
    assert cr.xses['server1'].server_num == 1
    assert cr.xses['server3'].server_num == 3
    assert cr.xses['server4'].server_num == 4
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
                with_root = x1.contained_in
            XChild(a=11)

    assert len(cr.xses) == 2
    for server in 'server1', 'server2':
        index = 10
        for x_child in cr.xses[server].x_children.values():
            assert x_child.a == index
            index += 1
        assert index == 12
    assert with_root == cr


def test_configbuilder_multilevel_nested_items_access_to_contained_in():
    class XBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super(XBuilder, self).__init__()
            self.start = start
            self.number = self.contained_in.aaa

        def build(self):
            for num in xrange(self.start, self.start + self.number):
                with Xses(name='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('xses')
    class ItemWithXses(ConfigItem):
        aaa = 2

    with ConfigRoot(prod, [prod, pp]) as cr:
        with ItemWithXses() as item:
            with XBuilder() as xb1:
                xb1.b = 27
                with XChild(a=10) as x1:
                    xb1_with_item = x1.contained_in
                with XBuilder(start=3) as xb2:
                    xb2.c = 28
                    with XChild(a=11) as x2:
                        xb2_with_item = x2.contained_in
                    XChild(a=12)


    assert len(item.xses) == 4
    total = 0
    for server in 'server1', 'server2', 'server3', 'server4':
        for x_child in item.xses[server].x_children.values():
            print x_child.a
            total += x_child.a
    assert total == 66

    assert xb1_with_item == item
    assert xb2_with_item == item


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

    assert len(xb1.what_built()) == 2
    assert isinstance(xb2.what_built(), OrderedDict) == True
    assert xb2.what_built()['xses']['server3'].something == 1
    assert xb2.what_built()['q'] == 3


# TODO not yet implemented 'partial' feature
# def test_configbuilder_nested_items_override_values_extend_envs():
#     @nested_repeatables('xses, x_children')
#     class XBuilder(ConfigBuilder):
#         def __init__(self):
#             super(XBuilder, self).__init__()
#             self.number = self.contained_in.aaa
#
#         def build(self):
#             for num in xrange(1, self.number+1):
#                 with Xses(name='server%d' % num, server_num=num) as c:
#                     # This does not list all envs
#                     c.something(prod=1)
#
#     @nested_repeatables('xses')
#     class Root(ConfigRoot):
#         aaa = 2
#
#     with Root(prod, [prod, pp]) as cr:
#         with XBuilder() as xb:
#             xb.b = 27)
#             # Here we finalize the setting of 'something' which was started in the 'build' method
#             xb.something(pp=2)
#             XChild(a=10)
#             XChild(a=11)
#
#     assert len(cr.xses) == 2
#     index = 10
#     for x_child in cr.xses['server1'].x_children.values():
#         assert x_child.a == index
#         index += 1


def test_env_value_overrides_group_value():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        with ConfigItem() as ci:
            ci.setattr('aa', prod=1, g_prod_like=2)
            ci.setattr('bb', g_prod_like=2, prod=3)

    assert cr1.ConfigItem.aa == 1
    assert cr1.ConfigItem.bb == 3


def test_group_value_overrides_default_value_from_init():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        with ConfigItem(aa=1, bb=3) as ci:
            ci.setattr('aa', g_prod_like=2)
            ci.setattr('bb', pp=4)

    assert cr1.ConfigItem.aa == 2
    assert cr1.ConfigItem.bb == 3


def test_group_value_overrides_default_value_from_setattr():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        with ConfigItem() as ci:
            ci.setattr('aa', default=1, g_prod_like=2)

    assert cr1.ConfigItem.aa == 2


def test_assigned_default_value_overrides_default_value_from_init():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        with ConfigItem(aa=1) as ci:
            ci.aa = 2

    assert cr1.ConfigItem.aa == 2


def test_default_value_from_setattr_overrides_default_value_from_init():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        with ConfigItem(aa=1) as ci:
            ci.setattr('aa', default=2, pp=3)

    assert cr1.ConfigItem.aa == 2


def test_env_value_overrides_default_value():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        with ConfigItem(aa=1, bb=3) as ci:
            ci.setattr('aa', prod=2)
            ci.setattr('bb', pp=4)

    assert cr1.ConfigItem.aa == 2
    assert cr1.ConfigItem.bb == 3


def test_env_value_overrides_group_value_and_default_value():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        with ConfigItem(aa=0) as ci:
            ci.setattr('aa', prod=1, g_prod_like=2)
            ci.setattr('bb', g_prod_like=2, prod=3)

    assert cr1.ConfigItem.aa == 1
    assert cr1.ConfigItem.bb == 3


def test_attribute_is_an_ordereddict():
    class y(ConfigItem):
        pass

    with ConfigRoot(prod, [prod, pp]) as cr1:
        x = y(aa=0)
        od = OrderedDict(((None, 1), ('foo', x)))
        ConfigItem(aa=od)

    assert cr1.ConfigItem.aa == od


def test_attribute_is_a_sequence():
    with ConfigRoot(prod, [prod, pp]) as cr1:
        seq = []
        ConfigItem(aa=seq)

    assert cr1.ConfigItem.aa == seq


def test_get_valid_envs():
    ve = [prod, pp]
    with ConfigRoot(prod, ve) as cr:
        ConfigItem()

    assert cr.valid_envs == ve
    assert cr.ConfigItem.valid_envs == ve


def test_required_attributes_not_required_on_imtermediate_freeze_configroot():
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    with root(prod, [prod]) as cr:
        cr.setattr('anattr', prod=1)
        assert cr.anattr == 1
        cr.setattr('anotherattr', prod=2)
        assert cr.anotherattr == 2


def test_required_attributes_not_required_on_imtermediate_freeze_configitem():
    class root(ConfigRoot):
        pass

    @required('a, b')
    class item(ConfigItem):
        pass

    with root(prod, [prod]) as cr:
        with item() as ii:
            ii.a = 1
            assert cr.item.a == 1
            ii.setattr('b', prod=2)
            assert cr.item.b == 2


def test_required_attributes_not_required_on_imtermediate_freeze_configbuilder():
    class root(ConfigRoot):
        pass

    @required('a, b')
    class builder(ConfigBuilder):
        def build(self):
            pass

    with root(prod, [prod]) as cr:
        with builder() as ii:
            ii.a = 1
            assert ii.a == 1
            ii.setattr('b', prod=2)
            assert ii.b == 2


def test_hasattr():
    class root(ConfigRoot):
        pass

    with root(prod, [prod]) as cr:
        with ConfigItem(a=1) as ii:
            ii.b = 2
            ii.setattr('c', prod=3)
            assert not hasattr(ii, 'd')

        assert hasattr(ii, 'a')
        assert hasattr(ii, 'b')
        assert hasattr(ii, 'c')
        assert not hasattr(ii, 'd')


def test_assigning_to_attribute_root():
    with root(prod, [prod]) as cr:
        cr.a = 7
    assert cr.a == 7


def test_assigning_to_attribute_nested_item():
    with root(prod, [prod]) as cr:
        with ConfigItem() as ci:
            ci.a = 1
    assert ci.a == 1

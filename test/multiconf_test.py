#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict
# pylint: disable=E0611
from pytest import fail

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


def test_automatic_freeze_call_of_validate_root():
    @nested_repeatables('children')
    class root(ConfigRoot):
        def validate(self):
            self.y = 7

    with root(prod, [prod, pp], a=0) as rt:
        pass
    assert rt.y == 7


def test_automatic_freeze_call_of_validate_item():
    class item(ConfigItem):
        def validate(self):
            self.y = 7

    with root(prod, [prod, pp], a=0):
        ii = item()

    assert ii.y == 7


def test_automatic_freeze_call_of_validate_builder():
    class builder(ConfigBuilder):
        def validate(self):
            self.y = 7

        def build(self):
            pass

    with root(prod, [prod, pp], a=0):
        ii = builder()

    assert ii.y == 7


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


def test_freeze_of_property_at_access():
    with root(prod, [prod, pp], a=0):
        with rchild(id='a', x=19, z=20) as rc:
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


def test_assigning_to_attribute_underscore_attribute():
    with root(prod, [prod]) as cr:
        with ConfigItem() as ci:
            ci._a = 1
    assert ci._a == 1

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict
# pylint: disable=E0611
from pytest import fail

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from ..decorators import nested_repeatables, named_as, required
from ..envs import EnvFactory

from .utils.tstclasses import RootWithAA, RootWithAABB, ItemWithAA, ItemWithAABB


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)

ef3_dev1_pp_prod = EnvFactory()
dev13 = ef3_dev1_pp_prod.Env('dev1')
pp3 = ef3_dev1_pp_prod.Env('pp')
prod3 = ef3_dev1_pp_prod.Env('prod')
ef3_dev1_pp_prod.EnvGroup('g_prod_like', prod3, pp3, dev13)

ef4_a_dev1_pp_prod = EnvFactory()
_a = ef4_a_dev1_pp_prod.Env('a')
dev14 = ef4_a_dev1_pp_prod.Env('dev1')
pp4 = ef4_a_dev1_pp_prod.Env('pp')
prod4 = ef4_a_dev1_pp_prod.Env('prod')
ef4_a_dev1_pp_prod.EnvGroup('g_prod_like', _a, prod4, pp4)

ef5_a_dev1_pp_prod = EnvFactory()
_a = ef5_a_dev1_pp_prod.Env('a')
dev15 = ef5_a_dev1_pp_prod.Env('dev1')
pp5 = ef5_a_dev1_pp_prod.Env('pp')
prod15 = ef5_a_dev1_pp_prod.Env('prod1')
prod25 = ef5_a_dev1_pp_prod.Env('prod2')
g_prod5 = ef5_a_dev1_pp_prod.EnvGroup('g_prod', _a, prod15, prod25)
ef5_a_dev1_pp_prod.EnvGroup('g_prod_like', _a, g_prod5, pp5)


@nested_repeatables('children')
class nc_aa_root(ConfigRoot):
    def __init__(self, selected_env, env_factory, aa=None):
        super(nc_aa_root, self).__init__(selected_env, env_factory)
        self.aa = aa


class aabb_root(ConfigRoot):
    def __init__(self, selected_env, env_factory, aa=None, bb=None):
        super(aabb_root, self).__init__(selected_env, env_factory)
        self.aa = aa
        self.bb = bb


@named_as('children')
class rchild(RepeatableConfigItem):
    def __init__(self, name, aa=None, bb=None):
        super(rchild, self).__init__(mc_key=name)
        self.name = name
        self.aa = aa
        self.bb = bb


@named_as('recursive_items')
@nested_repeatables('recursive_items')
class NestedRepeatable(RepeatableConfigItem):
    def __init__(self, id, aa=None):
        super(NestedRepeatable, self).__init__(mc_key=id)
        self.id = id
        self.aa = aa


class KwargsItem(ConfigItem):
    def __init__(self, **kwargs):
        super(KwargsItem, self).__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)


class anitem(ConfigItem):
    xx = 1


class anotheritem(ConfigItem):
    xx = 2


def test_contained_in_root_conf():
    with ConfigRoot(prod2, ef2_pp_prod) as conf:
        assert conf.root_conf == conf
        assert conf.contained_in is None

        with ConfigItem() as c1:
            assert c1.root_conf == conf
            assert c1.contained_in == conf

            with ConfigItem() as c2:
                assert c2.root_conf == conf
                assert c2.contained_in == c1


def test_nested_repeatable_items():
    with nc_aa_root(prod2, ef2_pp_prod) as cr:
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
    with nc_aa_root(prod2, ef2_pp_prod) as cr:
        pass

    for _ci in cr.children.values():
        fail("list should be empty")


def test_unnamed_nested_repeatable_item_no_name_or_id():
    with nc_aa_root(prod2, ef2_pp_prod) as cr:
        with rchild(name=None, aa=1, bb=1) as ci:
            ci.setattr('aa', prod=3)
        ci_id = id(ci)

    assert cr.children[ci_id].aa == 3


def test_unnamed_nested_repeatable_item_no_default_name_or_id():
    with nc_aa_root(prod2, ef2_pp_prod) as cr:
        with rchild(name=None, aa=1, bb=1) as ci:
            ci.setattr('name', prod='somevalue', pp='another')
        ci_id = id(ci)

    assert cr.children[ci_id].aa == 1
    assert cr.children[ci_id].name == 'somevalue'


def test_iteritems_root_attributes():
    with aabb_root(prod2, ef2_pp_prod) as cr:
        cr.aa = 1
        cr.bb = 2

    for exp, actual in zip([('aa', 1), ('bb', 2)], list(cr.items())):
        exp_key, exp_value = exp
        key, value = actual
        assert exp_key == key
        assert exp_value == value


def test_iteritems_item_attributes():
    @required('anitem')
    class myitem(ConfigItem):
        def __init__(self):
            super(myitem, self).__init__()
            self.aa = MC_REQUIRED

    with ConfigRoot(prod2, ef2_pp_prod):
        with myitem() as ci:
            ci.aa = 1
            anitem()

    for key, value in ci.items():
        if key == 'aa':
            assert value == 1
            continue
        if key == 'anitem':
            assert value.xx == 1
            continue

        fail("unexpected key {} returned from 'items()'".format(key))


def test_property_defined_with_same_type_and_none():
    with RootWithAA(prod2, ef2_pp_prod) as cr:
        cr.setattr('aa', default=None, prod=1, pp=2)
    assert cr.aa == 1


def test_property_defined_with_none_and_same_type():
    with RootWithAA(prod2, ef2_pp_prod) as cr:
        cr.setattr('aa', default=1, prod=None, pp=2)
    assert cr.aa is None


def test_automatic_freeze_of_child_on_exit():
    with RootWithAA(prod2, ef2_pp_prod) as cr:
        cr.aa = 0
        with ItemWithAA() as ci:
            ci.aa = 1
    assert cr.ItemWithAA.aa == 1


def test_automatic_freeze_of_previous_sibling():
    with nc_aa_root(prod2, ef2_pp_prod, aa=0) as rt:
        rchild(name='aa', aa=18)
        assert rt.children['aa'].aa == 18


# TODO test_automatic_freeze_of_previous_sibling mc_init


def test_automatic_freeze_call_of_validate_root():
    @nested_repeatables('children')
    class root(ConfigRoot):
        def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                     mc_allow_todo=False, mc_allow_current_env_todo=False,
                     aa=None):
            super(root, self).__init__(
                selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
                mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
            self.aa = aa

        def validate(self):
            self.aa = 7

    with root(prod2, ef2_pp_prod) as rt:
        pass
    assert rt.aa == 7


def test_automatic_freeze_call_of_validate_set_unknown_root():
    @nested_repeatables('children')
    class root(ConfigRoot):
        def validate(self):
            self.setattr('y?', default=7)

    with root(prod2, ef2_pp_prod) as rt:
        pass
    assert rt.y == 7


def test_automatic_freeze_call_of_validate_item():
    class item(ConfigItem):
        def __init__(self):
            super(item, self).__init__()
            self.aa = None

        def validate(self):
            self.aa = 7

    with ConfigRoot(prod2, ef2_pp_prod):
        ii = item()

    assert ii.aa == 7


def test_automatic_freeze_call_of_validate_item_not_previously_set():
    class item(ConfigItem):
        def validate(self):
            self.aa = 7

    with ConfigRoot(prod2, ef2_pp_prod):
        ii = item()

    assert ii.aa == 7


def test_automatic_freeze_call_of_validate_set_unknown_item():
    class item(ConfigItem):
        def validate(self):
            self.setattr('y?', default=7)

    with nc_aa_root(prod2, ef2_pp_prod, aa=0):
        ii = item()

    assert ii.y == 7


def test_automatic_freeze_call_of_validate_builder():
    class builder(ConfigBuilder):
        def validate(self):
            self.y = 7

        def build(self):
            pass

    with nc_aa_root(prod2, ef2_pp_prod, aa=0):
        ii = builder()

    assert ii.y == 7


def test_automatic_contained_item_freeze_on_exit():
    @nested_repeatables('recursive_items')
    class root2(ConfigRoot):
        pass

    with root2(prod2, ef2_pp_prod) as cr:
        NestedRepeatable(id='aa')
        with NestedRepeatable(id='bb') as ci:
            NestedRepeatable(id='aa')
            with NestedRepeatable(id='bb') as ci:
                NestedRepeatable(id='aa')
                with NestedRepeatable(id='bb') as ci:
                    ci.setattr('aa', prod=1, pp=2)
                NestedRepeatable(id='cc')
            NestedRepeatable(id='cc')
        NestedRepeatable(id='cc')

    assert len(cr.recursive_items['aa'].recursive_items) == 0
    assert len(cr.recursive_items['bb'].recursive_items) == 3
    assert len(cr.recursive_items['cc'].recursive_items) == 0

    ids = ['aa', 'bb', 'cc']
    index = 0
    for item_id, item in cr.recursive_items['bb'].recursive_items.items():
        assert item.id == ids[index]
        assert item_id == ids[index]
        index += 1
    assert index == 3

    assert cr.recursive_items['bb'].recursive_items['bb'].recursive_items['bb'].aa == 1


def test_automatic_freeze_of_property_defined_in_with_statement_unknown():
    with nc_aa_root(prod2, ef2_pp_prod, aa=0):
        with rchild(name='aa') as rc:
            rc.setattr('y?', prod=1, pp=2)
            assert rc.y == 1


def test_automatic_freeze_of_property_overridden_in_with_statement():
    with nc_aa_root(prod2, ef2_pp_prod, aa=0):
        with rchild(name='aa', bb=18) as rc:
            rc.setattr('bb', prod=7, pp=2)
            assert rc.bb == 7


def test_freeze_of_property_at_access():
    with nc_aa_root(prod2, ef2_pp_prod, aa=0):
        with rchild(name='aa', aa=19, bb=20) as rc:
            assert rc.aa == 19


# TODO: allow this (while inside with statement only)
#def define new attribute after freeze_test(self):
#    with nc_aa_root(prod2, ef2_pp_prod, aa=0):
#        with rchild(id='aa', x=19, z=20) as rc:
#            rc.setattr('y', prod=7, pp=2)
#            assert rc.y == 7
#            rc.setattr('z', pp=3)
#            assert rc.z == 20
#            assert rc.x == 19
#            rc.a(prod=3, pp=4)
#            assert rc.aa == 3


def test_find_contained_in_named_as():
    @named_as('x')
    @nested_repeatables('recursive_items')
    class X(ItemWithAA):
        pass

    @named_as('y')
    class Y(ItemWithAA):
        pass

    @nested_repeatables('recursive_items')
    class root3(RootWithAA):
        pass

    with root3(prod2, ef2_pp_prod) as cr:
        cr.aa = 0
        NestedRepeatable(id=0)
        with X() as ci:
            ci.setattr('aa', prod=0, pp=2)
            NestedRepeatable(id='aa')
            with NestedRepeatable(id='bb') as ci:
                NestedRepeatable(id='cc')
                with X() as ci:
                    ci.setattr('aa', prod=1, pp=2)
                    with NestedRepeatable(id='dd') as ci:
                        ci.setattr('aa', prod=2, pp=2)
                        with Y() as ci:
                            ci.setattr('aa', prod=3, pp=2)

    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].y.find_contained_in(named_as='x').aa == 1
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].y.find_contained_in(named_as='root3').aa == 0
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].y.find_contained_in(named_as='recursive_items').aa == 2
    assert cr.x.recursive_items['bb'].x.find_contained_in(named_as='x').aa == 0


def test_find_attribute_attribute_name():
    @named_as('x')
    @nested_repeatables('recursive_items')
    class X(ItemWithAA):
        pass

    @nested_repeatables('recursive_items')
    class root4(RootWithAA):
        pass

    with root4(prod2, ef2_pp_prod, aa=-1) as cr:
        cr.setattr('q?', default='q0')
        NestedRepeatable(id=0)
        with X() as ci:
            ci.setattr('yy?', default=999)
            ci.setattr('aa', prod=0, pp=20)
            NestedRepeatable(id='aa', aa=9)
            with NestedRepeatable(id='bb') as ci:
                NestedRepeatable(id='cc', aa=7)
                with X() as ci:
                    ci.aa = 117
                    ci.setattr('bb?', prod='b1', pp='b21')
                    with NestedRepeatable(id='dd') as ci:
                        ci.setattr('aa', prod=2, pp=22)
                        with X() as ci:
                            ci.setattr('aa', prod=3, pp=23)

    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('aa') == 3
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('bb') == 'b1'
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('recursive_items')['dd'].aa == 2
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('q') == 'q0'
    assert cr.x.recursive_items['bb'].x.find_attribute(attribute_name='aa') == 117
    assert cr.x.recursive_items['bb'].x.contained_in.find_attribute(attribute_name='aa') == None
    assert cr.x.recursive_items['bb'].x.find_attribute(attribute_name='yy') == 999


def test_env_value_overrides_group_value():
    with ConfigRoot(prod4, ef4_a_dev1_pp_prod) as cr1:
        with ItemWithAABB() as ci:
            ci.setattr('aa', prod=1, g_prod_like=2, dev1=3)
            # Note: Parameters are passed as a dictionary with undefined order
            #  - Having a group named 'a' gives us 100% coverage in C Python
            ci.setattr('bb', dev1=1, a=2, prod=3, pp=4)

    assert cr1.ItemWithAABB.aa == 1
    assert cr1.ItemWithAABB.bb == 3


def test_group_value_overrides_default_value_from_init():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with KwargsItem(aa=1, bb=3) as ci:
            ci.setattr('aa', g_prod_like=2)
            ci.setattr('bb', pp=4)

    assert cr1.KwargsItem.aa == 2
    assert cr1.KwargsItem.bb == 3


def test_group_value_overrides_default_value_from_setattr():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with ItemWithAA() as ci:
            ci.setattr('aa', default=1, g_prod_like=2)

    assert cr1.ItemWithAA.aa == 2


def test_assigned_default_value_overrides_default_value_from_init():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with KwargsItem(aa=1) as ci:
            ci.aa = 2

    assert cr1.KwargsItem.aa == 2


def test_default_value_from_setattr_overrides_default_value_from_init():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with KwargsItem(aa=1) as ci:
            ci.setattr('aa', default=2, pp=3)

    assert cr1.KwargsItem.aa == 2


def test_env_value_overrides_default_value():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with KwargsItem(aa=1, bb=3) as ci:
            ci.setattr('aa', prod=2)
            ci.setattr('bb', pp=4)

    assert cr1.KwargsItem.aa == 2
    assert cr1.KwargsItem.bb == 3


def test_env_value_overrides_group_value_and_default_value():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with KwargsItem(aa=0, bb=0) as ci:
            ci.setattr('aa', prod=1, g_prod_like=2)
            ci.setattr('bb', g_prod_like=2, prod=3)

    assert cr1.KwargsItem.aa == 1
    assert cr1.KwargsItem.bb == 3


def test_more_specific_group_overrides_less_specific_group_value_and_default_value():
    with ConfigRoot(prod15, ef5_a_dev1_pp_prod) as cr1:
        with KwargsItem(aa=0, bb=0, cc=0, dd=0, ee=0, ff=0) as ci:
            ci.setattr('aa', g_prod=1, g_prod_like=2, a=17, dev1=18)
            ci.setattr('bb', a=17, dev1=18, g_prod_like=2, g_prod=3)
            ci.setattr('cc', prod1=1, g_prod=3, g_prod_like=2, a=17, dev1=18)
            ci.setattr('dd', a=17, dev1=18, g_prod_like=2, g_prod=3, prod1=3)
            ci.setattr('ee', g_prod=3, prod1=1, g_prod_like=2, a=17, dev1=18)
            ci.setattr('ff', a=17, dev1=18, g_prod_like=2, prod1=3, g_prod=3)

    print("aa:", cr1.KwargsItem.aa)
    assert cr1.KwargsItem.aa == 1
    assert cr1.KwargsItem.bb == 3
    print("cc:", cr1.KwargsItem.cc)
    assert cr1.KwargsItem.cc == 1
    assert cr1.KwargsItem.dd == 3
    assert cr1.KwargsItem.ee == 1
    assert cr1.KwargsItem.ff == 3


def test_attribute_is_an_ordereddict():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with ItemWithAA() as x:
            x.aa = 0
        od = OrderedDict(((None, 1), ('foo', x)))
        KwargsItem(aa=od)

    assert cr1.KwargsItem.aa == od


def test_attribute_is_a_sequence():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        seq = []
        KwargsItem(aa=seq)

    assert cr1.KwargsItem.aa == seq


def test_get_factory():
    ve = ef2_pp_prod
    with ConfigRoot(prod2, ve) as cr:
        ConfigItem()

    assert cr.env_factory == ve
    assert cr.ConfigItem.env_factory == ve


def test_required_items_not_required_on_imtermediate_freeze_configroot():
    @required('anitem, anotheritem')
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
        anitem()
        # Accessing anitem here will not freeze cr
        assert cr.anitem.xx == 1
        anotheritem()
        assert cr.anotheritem.xx == 2


def test_mc_required_attributes_not_required_on_imtermediate_freeze_configroot():
    class root(ConfigRoot):
        def __init__(self, selected_env, env_factory):
            super(root, self).__init__(selected_env, env_factory)
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

    with root(prod1, ef1_prod) as cr:
        cr.setattr('anattr', prod=1)
        # Accessing anattr here will not freeze cr
        assert cr.anattr == 1
        cr.setattr('anotherattr', prod=2)
        assert cr.anotherattr == 2


def test_required_items_not_required_on_imtermediate_freeze_configitem():
    class root(ConfigRoot):
        pass

    @required('anitem, anotheritem')
    class item(ConfigItem):
        pass

    with root(prod1, ef1_prod) as cr:
        with item() as ii:
            anitem()
            assert cr.item.anitem.xx == 1
            anotheritem()
            assert cr.item.anotheritem.xx == 2


def test_mc_required_attributes_not_required_on_imtermediate_freeze_configitem():
    class root(ConfigRoot):
        pass

    class item(ConfigItem):
        def __init__(self):
            super(item, self).__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED

    with root(prod1, ef1_prod) as cr:
        with item() as ii:
            ii.aa = 1
            assert cr.item.aa == 1
            ii.setattr('bb', prod=2)
            assert cr.item.bb == 2


def test_hasattr():
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
        with KwargsItem(aa=1, bb=0) as ii:
            ii.bb = 2
            ii.setattr('cc?', prod=3)
            assert not hasattr(ii, 'dd')

        assert hasattr(ii, 'aa')
        assert hasattr(ii, 'bb')
        assert hasattr(ii, 'cc')
        assert not hasattr(ii, 'dd')

    assert hasattr(ii, 'aa')
    assert hasattr(ii, 'bb')
    assert hasattr(ii, 'cc')
    assert not hasattr(ii, 'dd')


def test_assigning_to_attribute_root():
    with nc_aa_root(prod1, ef1_prod) as cr:
        cr.aa = 7
    assert cr.aa == 7


def test_assigning_to_attribute_nested_item():
    with nc_aa_root(prod1, ef1_prod) as cr:
        with ItemWithAA() as ci:
            ci.aa = 1
    assert ci.aa == 1


def test_assigning_to_attribute_underscore_attribute():
    with nc_aa_root(prod1, ef1_prod) as cr:
        with ConfigItem() as ci:
            ci._a = 1
    assert ci._a == 1


def test_mc_init_simple_items():
    class X(ItemWithAABB):
        def mc_init(self):
            self.aa = 1
            self.bb = 1
            KwargsItem(aa=1, bb=1)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with X() as x:
            x.aa = 2
            KwargsItem(aa=2)

    assert cr.X.aa == 2
    assert cr.X.bb == 1
    assert cr.X.KwargsItem.aa == 2
    assert not hasattr(cr.X.KwargsItem, 'bb')

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        X()

    assert cr.X.aa == 1
    assert cr.X.bb == 1
    assert cr.X.KwargsItem.aa == 1
    assert cr.X.KwargsItem.bb == 1


def test_mc_init_repeatable_items():
    class X(RepeatableConfigItem):
        def __init__(self, mc_key, aa, bb=None):
            super(X, self).__init__(mc_key)
            self.aa = aa
            if bb is not None:
                self.bb = bb

    @nested_repeatables('Xs')
    class Y(ItemWithAABB):
        def mc_init(self):
            self.aa = 1
            self.bb = 1
            with X(mc_key='aa', aa=1, bb=1) as x:
                x.setattr('aa', prod=7)
            X(mc_key='bb', aa=1, bb=1)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with Y() as y:
            y.aa = 3
            with X(mc_key='aa', aa=1) as x:
                x.aa = 3

    assert cr.Y.aa == 3
    assert cr.Y.Xs['aa'].aa == 3
    assert not hasattr(cr.Y.Xs['aa'], 'bb')
    assert cr.Y.Xs['bb'].aa == 1
    assert cr.Y.Xs['bb'].bb == 1


def test_mc_init_root():
    class RootX(RootWithAABB):
        def mc_init(self):
            self.aa = 1
            self.bb = 1
            KwargsItem(aa=1, bb=1)

    with RootX(prod2, ef2_pp_prod) as cr:
        cr.aa = 2
        KwargsItem(aa=2)

    assert cr.aa == 2
    assert cr.bb == 1
    assert cr.KwargsItem.aa == 2
    assert not hasattr(cr.KwargsItem, 'bb')

    with RootX(prod2, ef2_pp_prod) as cr:
        cr.aa = 2

    assert cr.aa == 2
    assert cr.bb == 1
    assert cr.KwargsItem.aa == 1
    assert cr.KwargsItem.bb == 1


def test_nested_mc_init_simple_items():
    class X1(ItemWithAABB):
        def mc_init(self):
            self.aa = 11
            self.bb = 11
            KwargsItem(aa=11, bb=11)

    class X2(ItemWithAABB):
        def mc_init(self):
            self.aa = 12
            self.bb = 12
            KwargsItem(aa=12, bb=12)

    class X3(ItemWithAABB):
        def mc_init(self):
            self.aa = 13
            self.bb = 13
            KwargsItem(aa=13, bb=13)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with X1() as x:
            x.aa = 1
            KwargsItem(aa=1)
            with X2() as x:
                x.aa = 2
                KwargsItem(aa=2)
                with X3() as x:
                    x.aa = 3
                    KwargsItem(aa=3)

    assert cr.X1.aa == 1
    assert cr.X1.bb == 11
    assert cr.X1.KwargsItem.aa == 1
    assert not hasattr(cr.X1.KwargsItem, 'bb')

    assert cr.X1.X2.aa == 2
    assert cr.X1.X2.bb == 12
    assert cr.X1.X2.KwargsItem.aa == 2
    assert not hasattr(cr.X1.X2.KwargsItem, 'bb')

    assert cr.X1.X2.X3.aa == 3
    assert cr.X1.X2.X3.bb == 13
    assert cr.X1.X2.X3.KwargsItem.aa == 3
    assert not hasattr(cr.X1.X2.X3.KwargsItem, 'bb')

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with X1() as x:
            x.aa = 1
            with X2() as x:
                x.aa = 2
                X3()

    assert cr.X1.aa == 1
    assert cr.X1.bb == 11
    assert cr.X1.KwargsItem.aa == 11
    assert cr.X1.KwargsItem.bb == 11

    assert cr.X1.X2.aa == 2
    assert cr.X1.X2.bb == 12
    assert cr.X1.X2.KwargsItem.aa == 12
    assert cr.X1.X2.KwargsItem.bb == 12

    assert cr.X1.X2.X3.aa == 13
    assert cr.X1.X2.X3.bb == 13
    assert cr.X1.X2.X3.KwargsItem.aa == 13
    assert cr.X1.X2.X3.KwargsItem.bb == 13


def test_mc_init_ref_env_attr_and_override():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super(X, self).__init__()
            self.aa = aa

        def mc_init(self):
            self.override('aa', self.aa + 1)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        X()
    assert cr.X.aa == 2

    with ConfigRoot(pp2, ef2_pp_prod) as cr:
        with X(aa=2) as x:
            x.aa = 3
    assert cr.X.aa == 4

    with ConfigRoot(pp2, ef2_pp_prod) as cr:
        with X(aa=2) as x:
            x.setattr('aa', default=3, pp=5)
    assert cr.X.aa == 6


def test_override_attr_in_init():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super(X, self).__init__()
            self.aa = aa
            self.override('aa', 17)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        X()
    assert cr.X.aa == 17

    with ConfigRoot(pp2, ef2_pp_prod) as cr:
        with X(aa=2) as x:
            x.aa = 3
    assert cr.X.aa == 3


def test_mc_init_override_change_type():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super(X, self).__init__()
            self.aa = aa

        def mc_init(self):
            # TODO? Override is allowed to change the attribute type
            self.override("aa", "Hello")

    with ConfigRoot(prod2, ef2_pp_prod):
        with X() as x:
            assert x.aa == 1
        assert x.aa == "Hello"


def test_override_repeated_attr():
    with ConfigRoot(prod2, ef2_pp_prod):
        with ItemWithAA() as ci:
            ci.aa = 1
            ci.override('aa', 7)
    assert ci.aa == 7


def test_override_repeated_unknown_attr():
    with ConfigRoot(prod2, ef2_pp_prod):
        with ConfigItem() as ci:
            ci.setattr('aa?', default=1)
            ci.override('aa', 7)
    assert ci.aa == 7


def test_override_override_method():
    """Test that 'override' method combined with '!' method override works."""
    class HasMethod(ConfigItem):
        @property
        def aa(self):
            return 1

    with ConfigRoot(prod2, ef2_pp_prod):
        with HasMethod() as ci:
            ci.override('aa!', 7)
    assert ci.aa == 7


def test_builder_ref_env_attr_and_override():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super(X, self).__init__()
            self.aa = aa

        def mc_init(self):
            self.override('aa', self.aa + 1)

    class XBuilder(ConfigBuilder):
        def __init__(self, aa=17):
            super(XBuilder, self).__init__()
            self.aa = aa

        def mc_init(self):
            self.override('aa', self.aa - 1)

        def build(self):
            # Everything in builder will be set on parent!
            # Maybe override should be forbidden here
            self.override('aa', self.aa + 3)
            X()

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        XBuilder()
    assert cr.aa == 19
    assert cr.X.aa == 16

    with ConfigRoot(pp2, ef2_pp_prod) as cr:
        with XBuilder(aa=2) as x:
            x.aa = 3
    assert cr.aa == 5
    assert cr.X.aa == 2

    with ConfigRoot(pp2, ef2_pp_prod) as cr:
        with XBuilder(aa=2) as x:
            x.setattr('aa', default=3, pp=5)
    assert cr.aa == 7
    assert cr.X.aa == 4


def test_find_contained_in_or_none():
    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with KwargsItem(aa=1) as i1:
            KwargsItem(aa=2)

    assert cr.KwargsItem.KwargsItem.find_contained_in_or_none('notthere') is None
    assert cr.KwargsItem.KwargsItem.find_contained_in_or_none('KwargsItem') == i1


def test_find_attribute_or_none():
    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with KwargsItem(aa=1, my_attr=0) as i1:
            i1.my_attr = 7
            KwargsItem(aa=2)

    assert cr.KwargsItem.KwargsItem.find_attribute_or_none('notthere') is None
    assert cr.KwargsItem.KwargsItem.find_attribute_or_none('my_attr') == 7


def test_mc_init_setattr_ref_env_value():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super(X, self).__init__()
            self.aa = aa

        def mc_init(self):
            self.setattr("aa", default=self.aa, prod=3)

    with ConfigRoot(pp2, ef2_pp_prod):
        x = X()
    assert x.aa == 1

    with ConfigRoot(prod2, ef2_pp_prod):
        x = X()
    assert x.aa == 3


def test_mc_init_setattr_ref_env_value_from_with():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super(X, self).__init__()
            self.aa = aa

        def mc_init(self):
            self.setattr("aa", default=self.aa, prod=3)

    with ConfigRoot(prod2, ef2_pp_prod):
        with X() as x:
            x.setattr('aa', default=13, pp=4, prod=7)
    assert x.aa == 7

    with ConfigRoot(prod2, ef2_pp_prod):
        with X() as x:
            x.setattr('aa', default=13, pp=4)
    assert x.aa == 3

    with ConfigRoot(pp2, ef2_pp_prod):
        with X() as x:
            x.setattr('aa', default=13, pp=4)
    assert x.aa == 4

    with ConfigRoot(pp2, ef2_pp_prod):
        with X() as x:
            x.setattr('aa', default=13)
    assert x.aa == 13


def test_attribute_args_partial_set_in_init_overridden_or_finished_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=13):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('bb', default=17, prod=2)

        def mc_init(self):
            self.setattr('aa', pp=7)
            self.bb = 7

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        Requires()

    assert cr.Requires.aa == 13
    assert cr.Requires.bb == 2

    with ConfigRoot(pp2, ef2_pp_prod) as cr:
        Requires()

    assert cr.Requires.aa == 7
    assert cr.Requires.bb == 7

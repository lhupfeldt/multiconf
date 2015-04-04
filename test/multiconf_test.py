# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict
# pylint: disable=E0611
from pytest import fail

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigBuilder
from ..decorators import nested_repeatables, named_as, required
from ..envs import EnvFactory

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
a = ef4_a_dev1_pp_prod.Env('a')
dev14 = ef4_a_dev1_pp_prod.Env('dev1')
pp4 = ef4_a_dev1_pp_prod.Env('pp')
prod4 = ef4_a_dev1_pp_prod.Env('prod')
ef4_a_dev1_pp_prod.EnvGroup('g_prod_like', a, prod4, pp4)

ef5_a_dev1_pp_prod = EnvFactory()
a = ef5_a_dev1_pp_prod.Env('a')
dev15 = ef5_a_dev1_pp_prod.Env('dev1')
pp5 = ef5_a_dev1_pp_prod.Env('pp')
prod15 = ef5_a_dev1_pp_prod.Env('prod1')
prod25 = ef5_a_dev1_pp_prod.Env('prod2')
g_prod5 = ef5_a_dev1_pp_prod.EnvGroup('g_prod', a, prod15, prod25)
ef5_a_dev1_pp_prod.EnvGroup('g_prod_like', a, g_prod5, pp5)


@nested_repeatables('children')
class root(ConfigRoot):
    def __init__(self, selected_env, env_factory, a=None):
        super(root, self).__init__(selected_env, env_factory)
        self.a = a


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
    def __init__(self, id, a=None):
        super(NestedRepeatable, self).__init__(mc_key=id)
        self.id = id
        if a is not None:
            self.a = a


class KwargsItem(ConfigItem):
    def __init__(self, **kwargs):
        super(KwargsItem, self).__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)


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
    with root(prod2, ef2_pp_prod) as cr:
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
    with root(prod2, ef2_pp_prod) as cr:
        pass

    for _ci in cr.children.values():
        fail("list should be empty")


def test_unnamed_nested_repeatable_item_no_name_or_id():
    with root(prod2, ef2_pp_prod) as cr:
        with rchild(name=None, aa=1, bb=1) as ci:
            ci.setattr('aa', prod=3)
        ci_id = id(ci)

    assert cr.children[ci_id].aa == 3


def test_unnamed_nested_repeatable_item_no_default_name_or_id():
    with root(prod2, ef2_pp_prod) as cr:
        with rchild(name=None, aa=1, bb=1) as ci:
            ci.setattr('name', prod='somevalue', pp='another')
        ci_id = id(ci)

    assert cr.children[ci_id].aa == 1
    assert cr.children[ci_id].name == 'somevalue'


def test_iteritems_root_attributes():
    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        cr.a = 1
        cr.b = 2

    for exp, actual in zip([('a', 1), ('b', 2)], list(cr.items())):
        exp_key, exp_value = exp
        key, value = actual
        assert exp_key == key
        assert exp_value == value


def test_iteritems_item_attributes():
    with ConfigRoot(prod2, ef2_pp_prod):
        with ConfigItem() as ci:
            ci.a = 1
            ci.b = 2

    for exp, actual in zip([('a', 1), ('b', 2)], list(ci.items())):
        exp_key, exp_value = exp
        key, value = actual
        assert exp_key == key
        assert exp_value == value


def test_property_defined_with_same_type_and_none():
    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        cr.setattr('a', default=None, prod=1, pp=2)
    assert cr.a == 1


def test_property_defined_with_none_and_same_type():
    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        cr.setattr('a', default=1, prod=None, pp=2)
    assert cr.a is None


def test_automatic_freeze_of_child_on_exit():
    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        cr.a = 0
        with ConfigItem() as ci:
            ci.something = 1
    assert cr.ConfigItem.something == 1


def test_automatic_freeze_of_previous_sibling():
    with root(prod2, ef2_pp_prod, a=0) as rt:
        rchild(name='a', aa=18)
        assert rt.children['a'].aa == 18


# TODO test_automatic_freeze_of_previous_sibling mc_init 


def test_automatic_freeze_call_of_validate_root():
    @nested_repeatables('children')
    class root(ConfigRoot):
        def validate(self):
            self.y = 7

    with root(prod2, ef2_pp_prod) as rt:
        pass
    assert rt.y == 7


def test_automatic_freeze_call_of_validate_item():
    class item(ConfigItem):
        def validate(self):
            self.y = 7

    with root(prod2, ef2_pp_prod, a=0):
        ii = item()

    assert ii.y == 7


def test_automatic_freeze_call_of_validate_builder():
    class builder(ConfigBuilder):
        def validate(self):
            self.y = 7

        def build(self):
            pass

    with root(prod2, ef2_pp_prod, a=0):
        ii = builder()

    assert ii.y == 7


def test_automatic_contained_item_freeze_on_exit():
    @nested_repeatables('recursive_items')
    class root2(ConfigRoot):
        pass

    with root2(prod2, ef2_pp_prod) as cr:
        NestedRepeatable(id='a')
        with NestedRepeatable(id='b') as ci:
            NestedRepeatable(id='a')
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    ci.setattr('a', prod=1, pp=2)
                NestedRepeatable(id='c')
            NestedRepeatable(id='c')
        NestedRepeatable(id='c')

    assert len(cr.recursive_items['a'].recursive_items) == 0
    assert len(cr.recursive_items['b'].recursive_items) == 3
    assert len(cr.recursive_items['c'].recursive_items) == 0

    ids = ['a', 'b', 'c']
    index = 0
    for item_id, item in cr.recursive_items['b'].recursive_items.items():
        assert item.id == ids[index]
        assert item_id == ids[index]
        index += 1
    assert index == 3

    assert cr.recursive_items['b'].recursive_items['b'].recursive_items['b'].a == 1


def test_automatic_freeze_of_property_defined_in_with_statement():
    with root(prod2, ef2_pp_prod, a=0):
        with rchild(name='a') as rc:
            rc.setattr('y', prod=1, pp=2)
            assert rc.y == 1


def test_automatic_freeze_of_property_overridden_in_with_statement():
    with root(prod2, ef2_pp_prod, a=0):
        with rchild(name='a', bb=18) as rc:
            rc.setattr('bb', prod=7, pp=2)
            assert rc.bb == 7


def test_freeze_of_property_at_access():
    with root(prod2, ef2_pp_prod, a=0):
        with rchild(name='a', aa=19, bb=20) as rc:
            assert rc.aa == 19


# TODO: allow this (while inside with statement only)
#def define new attribute after freeze_test(self):
#    with root(prod2, ef2_pp_prod, a=0):
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

    with root3(prod2, ef2_pp_prod) as cr:
        cr.a = 0
        NestedRepeatable(id=0)
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
        def __init__(self, selected_env, env_factory, a):
            super(root4, self).__init__(selected_env=selected_env, env_factory=env_factory)
            self.a = a

    with root4(prod2, ef2_pp_prod, a=-1) as cr:
        cr.q = 'q0'
        NestedRepeatable(id=0)
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
    with ConfigRoot(prod4, ef4_a_dev1_pp_prod) as cr1:
        with ConfigItem() as ci:
            ci.setattr('aa', prod=1, g_prod_like=2, dev1=3)
            # Note: Parameters are passed as a dictionary with undefined order
            #  - Having a group named 'a' gives us 100% coverage in C Python
            ci.setattr('bb', dev1=1, a=2, prod=3, pp=4)

    assert cr1.ConfigItem.aa == 1
    assert cr1.ConfigItem.bb == 3


def test_group_value_overrides_default_value_from_init():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with KwargsItem(aa=1, bb=3) as ci:
            ci.setattr('aa', g_prod_like=2)
            ci.setattr('bb', pp=4)

    assert cr1.KwargsItem.aa == 2
    assert cr1.KwargsItem.bb == 3


def test_group_value_overrides_default_value_from_setattr():
    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with ConfigItem() as ci:
            ci.setattr('aa', default=1, g_prod_like=2)

    assert cr1.ConfigItem.aa == 2


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
        with KwargsItem(aa=0) as ci:
            ci.setattr('aa', prod=1, g_prod_like=2)
            ci.setattr('bb', g_prod_like=2, prod=3)

    assert cr1.KwargsItem.aa == 1
    assert cr1.KwargsItem.bb == 3


def test_more_specific_group_overrides_less_specific_group_value_and_default_value():
    with ConfigRoot(prod15, ef5_a_dev1_pp_prod) as cr1:
        with KwargsItem(aa=0) as ci:
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
    class y(ConfigItem):
        pass

    with ConfigRoot(prod2, ef2_pp_prod) as cr1:
        with y() as x:
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


def test_required_attributes_not_required_on_imtermediate_freeze_configroot():
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
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

    with root(prod1, ef1_prod) as cr:
        with item() as ii:
            ii.a = 1
            assert cr.item.a == 1
            ii.setattr('b', prod=2)
            assert cr.item.b == 2


def test_hasattr():
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
        with KwargsItem(a=1) as ii:
            ii.b = 2
            ii.setattr('c', prod=3)
            assert not hasattr(ii, 'd')

        assert hasattr(ii, 'a')
        assert hasattr(ii, 'b')
        assert hasattr(ii, 'c')
        assert not hasattr(ii, 'd')


def test_assigning_to_attribute_root():
    with root(prod1, ef1_prod) as cr:
        cr.a = 7
    assert cr.a == 7


def test_assigning_to_attribute_nested_item():
    with root(prod1, ef1_prod) as cr:
        with ConfigItem() as ci:
            ci.a = 1
    assert ci.a == 1


def test_assigning_to_attribute_underscore_attribute():
    with root(prod1, ef1_prod) as cr:
        with ConfigItem() as ci:
            ci._a = 1
    assert ci._a == 1


def test_mc_init_simple_items():
    class X(ConfigItem):
        def mc_init(self):
            self.a = 1
            self.b = 1
            KwargsItem(a=1, b=1)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with X() as x:
            x.a = 2
            KwargsItem(a=2)

    assert cr.X.a == 2
    assert cr.X.b == 1
    assert cr.X.KwargsItem.a == 2
    assert not hasattr(cr.X.KwargsItem, 'b')

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        X()

    assert cr.X.a == 1
    assert cr.X.b == 1
    assert cr.X.KwargsItem.a == 1
    assert cr.X.KwargsItem.b == 1


def test_mc_init_repeatable_items():
    class X(RepeatableConfigItem):
        def __init__(self, mc_key, a, b=None):
            super(X, self).__init__(mc_key)
            self.a = a
            if b is not None:
                self.b = b

    @nested_repeatables('Xs')
    class Y(ConfigItem):
        def mc_init(self):
            self.a = 1
            self.b = 1
            with X(mc_key='a', a=1, b=1) as x:
                x.setattr('a', prod=7)
            X(mc_key='b', a=1, b=1)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with Y() as y:
            y.a = 3
            with X(mc_key='a', a=1) as x:
                x.a = 3

    assert cr.Y.a == 3
    assert cr.Y.Xs['a'].a == 3
    assert not hasattr(cr.Y.Xs['a'], 'b')
    assert cr.Y.Xs['b'].a == 1
    assert cr.Y.Xs['b'].b == 1


def test_mc_init_root():
    class RootX(ConfigRoot):
        def mc_init(self):
            self.a = 1
            self.b = 1
            KwargsItem(a=1, b=1)

    with RootX(prod2, ef2_pp_prod) as cr:
        cr.a = 2
        KwargsItem(a=2)

    assert cr.a == 2
    assert cr.b == 1
    assert cr.KwargsItem.a == 2
    assert not hasattr(cr.KwargsItem, 'b')

    with RootX(prod2, ef2_pp_prod) as cr:
        cr.a = 2

    assert cr.a == 2
    assert cr.b == 1
    assert cr.KwargsItem.a == 1
    assert cr.KwargsItem.b == 1


def test_nested_mc_init_simple_items():
    class X1(ConfigItem):
        def mc_init(self):
            self.a = 11
            self.b = 11
            KwargsItem(a=11, b=11)

    class X2(ConfigItem):
        def mc_init(self):
            self.a = 12
            self.b = 12
            KwargsItem(a=12, b=12)

    class X3(ConfigItem):
        def mc_init(self):
            self.a = 13
            self.b = 13
            KwargsItem(a=13, b=13)

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with X1() as x:
            x.a = 1
            KwargsItem(a=1)
            with X2() as x:
                x.a = 2
                KwargsItem(a=2)
                with X3() as x:
                    x.a = 3
                    KwargsItem(a=3)

    assert cr.X1.a == 1
    assert cr.X1.b == 11
    assert cr.X1.KwargsItem.a == 1
    assert not hasattr(cr.X1.KwargsItem, 'b')

    assert cr.X1.X2.a == 2
    assert cr.X1.X2.b == 12
    assert cr.X1.X2.KwargsItem.a == 2
    assert not hasattr(cr.X1.X2.KwargsItem, 'b')

    assert cr.X1.X2.X3.a == 3
    assert cr.X1.X2.X3.b == 13
    assert cr.X1.X2.X3.KwargsItem.a == 3
    assert not hasattr(cr.X1.X2.X3.KwargsItem, 'b')

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with X1() as x:
            x.a = 1
            with X2() as x:
                x.a = 2
                X3()

    assert cr.X1.a == 1
    assert cr.X1.b == 11
    assert cr.X1.KwargsItem.a == 11
    assert cr.X1.KwargsItem.b == 11

    assert cr.X1.X2.a == 2
    assert cr.X1.X2.b == 12
    assert cr.X1.X2.KwargsItem.a == 12
    assert cr.X1.X2.KwargsItem.b == 12

    assert cr.X1.X2.X3.a == 13
    assert cr.X1.X2.X3.b == 13
    assert cr.X1.X2.X3.KwargsItem.a == 13
    assert cr.X1.X2.X3.KwargsItem.b == 13


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
        with ConfigItem() as ci:
            ci.a = 1
            ci.override('a', 7)
    assert ci.a == 7


def test_override_override_method():
    """Test that 'override' method combined with '!' method override works."""
    class HasMethod(ConfigItem):
        @property
        def a(self):
            return 1

    with ConfigRoot(prod2, ef2_pp_prod):
        with HasMethod() as ci:
            ci.override('a!', 7)
    assert ci.a == 7


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
        with KwargsItem(a=1) as i1:
            KwargsItem(a=2)

    assert cr.KwargsItem.KwargsItem.find_contained_in_or_none('notthere') is None
    assert cr.KwargsItem.KwargsItem.find_contained_in_or_none('KwargsItem') == i1


def test_find_attribute_or_none():
    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        with KwargsItem(a=1) as i1:
            i1.my_attr = 7
            KwargsItem(a=2)

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
        def __init__(self, a=13):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('a', prod=a)
            self.setattr('b', default=17, prod=2)

        def mc_init(self):
            self.setattr('a', pp=7)
            self.b = 7

    with ConfigRoot(prod2, ef2_pp_prod) as cr:
        Requires()

    assert cr.Requires.a == 13
    assert cr.Requires.b == 2

    with ConfigRoot(pp2, ef2_pp_prod) as cr:
        Requires()

    assert cr.Requires.a == 7
    assert cr.Requires.b == 7

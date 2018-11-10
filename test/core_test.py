# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict
# pylint: disable=E0611
from pytest import raises, fail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, MC_REQUIRED
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory

from .utils.utils import replace_ids
from .utils.tstclasses import ItemWithAA, ItemWithAABB


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)

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
class nc_aa_root(ItemWithAA):
    def __init__(self, aa=None):
        super().__init__(aa)


class aabb_root(ItemWithAABB):
    def __init__(self, aa=None, bb=None):
        super().__init__(aa, bb)


@named_as('children')
class rchild(RepeatableConfigItem):
    def __init__(self, mc_key, aa=None, bb=None):
        super().__init__(mc_key=mc_key)
        self.name = mc_key
        self.aa = aa
        self.bb = bb


@named_as('recursive_items')
@nested_repeatables('recursive_items')
class NestedRepeatable(RepeatableConfigItem):
    def __init__(self, mc_key, aa=None):
        super().__init__(mc_key=mc_key)
        self.id = mc_key
        self.aa = aa


class KwargsItem(ConfigItem):
    def __init__(self, **kwargs):
        super().__init__()
        for key, val in sorted(kwargs.items()):
            setattr(self, key, val)


class anitem(ConfigItem):
    xx = 1


class anotheritem(ConfigItem):
    xx = 2


def test_unnamed_nested_repeatable_item_no_name_or_id():
    # Note: This changes from v6, earlier versions inserted objects with the id(obj) if key was None
    # mc_key is not optional, but None is just a value like other keys
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with nc_aa_root():
            with rchild(mc_key=None, aa=1, bb=1) as ci:
                ci.setattr('aa', prod=3)

    cr = config(prod2).nc_aa_root
    assert cr.children[None].aa == 3


def test_iteritems_root_attributes():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with aabb_root() as cr:
            cr.aa = 1
            cr.bb = 2

    cr = config(prod2).aabb_root
    for _, _ in cr.items():
        fail("items() yielded something, but there should be no items!")


def test_iteritems_item_attributes():
    @required('anitem')
    class myitem(ConfigItem):
        def __init__(self):
            super().__init__()
            self.aa = MC_REQUIRED

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with myitem() as ci:
            ci.aa = 1
            anitem()

    ci = config(prod2).myitem
    for key, value in ci.items():
        if key == 'aa':
            fail("items() returned attribute!")
        if key == 'anitem':
            assert value.xx == 1
            continue

        fail("unexpected key {} returned from 'items()'".format(key))


def test_property_defined_with_same_type_and_none():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with ItemWithAA() as cr:
            cr.setattr('aa', default=None, prod=1, pp=2)

    cr = config(prod2).ItemWithAA
    assert cr.aa == 1


def test_property_defined_with_none_and_same_type():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with ItemWithAA() as cr:
            cr.setattr('aa', default=1, prod=None, pp=2)

    cr = config(prod2).ItemWithAA
    assert cr.aa is None


def test_env_value_overrides_group_value():
    @mc_config(ef4_a_dev1_pp_prod, load_now=True)
    def config(_):
        with ItemWithAABB() as ci:
            ci.setattr('aa', prod=1, g_prod_like=2, dev1=3)
            # Note: Parameters are passed as a dictionary with undefined order
            #  - Having a group named 'a' gives us 100% coverage in C Python
            ci.setattr('bb', dev1=1, a=2, prod=3, pp=4)

    cr = config(prod4)
    assert cr.ItemWithAABB.aa == 1
    assert cr.ItemWithAABB.bb == 3


def test_group_value_overrides_default_value_from_init():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=1, bb=3) as ci:
            ci.setattr('aa', g_prod_like=2)
            ci.setattr('bb', pp=4)

    cr = config(prod2)
    assert cr.KwargsItem.aa == 2
    assert cr.KwargsItem.bb == 3


def test_group_value_overrides_default_value_from_setattr():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with ItemWithAA() as ci:
            ci.setattr('aa', default=1, g_prod_like=2)

    cr = config(prod2)
    assert cr.ItemWithAA.aa == 2


def test_assigned_default_value_overrides_default_value_from_init():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=1) as ci:
            ci.aa = 2

    cr = config(prod2)
    assert cr.KwargsItem.aa == 2


def test_default_value_from_setattr_overrides_default_value_from_init():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=1) as ci:
            ci.setattr('aa', default=2, pp=3)

    cr = config(prod2)
    assert cr.KwargsItem.aa == 2


def test_env_value_overrides_default_value():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=1, bb=3) as ci:
            ci.setattr('aa', prod=2)
            ci.setattr('bb', pp=4)

    cr = config(prod2)
    assert cr.KwargsItem.aa == 2
    assert cr.KwargsItem.bb == 3


def test_env_value_overrides_group_value_and_default_value():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=0, bb=0) as ci:
            ci.setattr('aa', prod=1, g_prod_like=2)
            ci.setattr('bb', g_prod_like=2, prod=3)

    cr = config(prod2)
    assert cr.KwargsItem.aa == 1
    assert cr.KwargsItem.bb == 3


def test_more_specific_group_overrides_less_specific_group_value_and_default_value():
    @mc_config(ef5_a_dev1_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=0, bb=0, cc=0, dd=0, ee=0, ff=0) as ci:
            ci.setattr('aa', g_prod=1, g_prod_like=2, a=17, dev1=18)
            ci.setattr('bb', a=17, dev1=18, g_prod_like=2, g_prod=3)
            ci.setattr('cc', prod1=1, g_prod=3, g_prod_like=2, a=17, dev1=18)
            ci.setattr('dd', a=17, dev1=18, g_prod_like=2, g_prod=3, prod1=3)
            ci.setattr('ee', g_prod=3, prod1=1, g_prod_like=2, a=17, dev1=18)
            ci.setattr('ff', a=17, dev1=18, g_prod_like=2, prod1=3, g_prod=3)

    cr1 = config(prod15)
    print("aa:", cr1.KwargsItem.aa)
    assert cr1.KwargsItem.aa == 1
    assert cr1.KwargsItem.bb == 3
    print("cc:", cr1.KwargsItem.cc)
    assert cr1.KwargsItem.cc == 1
    assert cr1.KwargsItem.dd == 3
    assert cr1.KwargsItem.ee == 1
    assert cr1.KwargsItem.ff == 3


def test_attribute_is_an_ordereddict():
    od_exp = [None]

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with ItemWithAA() as x:
            x.aa = 0
        od = OrderedDict(((None, 1), ('foo', x)))
        od_exp[0] = od
        KwargsItem(aa=od)

    cr = config(prod2)
    assert cr.KwargsItem.aa == od_exp[0]


def test_attribute_is_a_sequence():
    seq_exp = [None]

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        seq = []
        seq_exp[0] = seq
        KwargsItem(aa=seq)

    cr = config(prod2)
    assert cr.KwargsItem.aa == seq_exp[0]


def test_get_factory():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(root):
        with ConfigItem():
            ConfigItem()

    cr = config(prod2)
    assert cr.env_factory == ef2_pp_prod
    assert cr.ConfigItem.env_factory == ef2_pp_prod
    assert cr.ConfigItem.ConfigItem.env_factory == ef2_pp_prod


# 'dd' is set at class level, resulting in the long exception message
_hasattr_expected_ex = """{
    "__class__": "KwargsItem #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1,
    "bb": 2,
    "cc": 3
}, object of type: <class 'test.core_test.KwargsItem'> has no attribute 'dd'."""


def test_hasattr():
    ii_exp = [None]

    class root(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with root() as cr:
            with KwargsItem(aa=1, bb=0) as ii:
                ii_exp[0] = ii
                ii.bb = 2
                ii.setattr('cc', prod=3, mc_set_unknown=True)
                assert not hasattr(ii, 'dd')

            assert hasattr(ii, 'aa')
            assert hasattr(ii, 'bb')
            assert hasattr(ii, 'cc')
            assert not hasattr(ii, 'dd')

    cr = config(prod1).root
    ii = ii_exp[0]
    assert hasattr(ii, 'aa')
    assert hasattr(ii, 'bb')
    assert hasattr(ii, 'cc')
    assert not hasattr(ii, 'dd')

    with raises(AttributeError) as exinfo:
        print(ii.dd)

    assert replace_ids(str(exinfo.value)) == _hasattr_expected_ex


def test_assigning_to_attribute_root():
    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with nc_aa_root() as cr:
            cr.aa = 7

    cr = config(prod1).nc_aa_root
    assert cr.aa == 7


def test_assigning_to_attribute_nested_item():
    ci_exp = [None]

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with nc_aa_root():
            with ItemWithAA() as ci:
                ci_exp[0] = ci
                ci.aa = 1

    cr = config(prod1).nc_aa_root
    assert ci_exp[0].aa == 1


def test_assigning_to_attribute_underscore_attribute():
    ci_exp = [None]

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with nc_aa_root():
            with ConfigItem() as ci:
                ci_exp[0] = ci
                ci._a = 1

    cr = config(prod1).nc_aa_root
    assert ci_exp[0]._a == 1


def test_mc_init_simple_items():
    class X(ItemWithAABB):
        def mc_init(self):
            self.aa = 1
            self.bb = 1
            KwargsItem(aa=1, bb=1)

    @mc_config(ef2_pp_prod, load_now=True)
    def config0(_):
        with ConfigItem():
            with X() as x:
                x.aa = 2
                KwargsItem(aa=2)

    cr = config0(prod2).ConfigItem
    assert cr.X.aa == 2
    assert cr.X.bb is None  # v6 change: None is no longer overridable
    assert cr.X.KwargsItem.aa == 2
    assert cr.X.KwargsItem.bb == 1 # v6 change: 'bb' exist because of object merge

    @mc_config(ef2_pp_prod, load_now=True)
    def config1(_):
        X()

    cr = config1(prod2)
    assert cr.X.aa == 1
    assert cr.X.bb is None  # v6 change: None is no longer overridable
    assert cr.X.KwargsItem.aa == 1
    assert cr.X.KwargsItem.bb == 1


def test_mc_init_simple_item_definition_more_specific_env_attr_value_merge_to_item_from_with_block():
    class XChild(ConfigItem):
        def __init__(self, aa=None):
            # Don't try this at home
            if aa is None:
                self.setattr('aa', default=1, prod=17)
            else:
                self.aa = 1

    class X(ItemWithAA):
        def mc_init(self):
            self.aa = 1
            XChild()

    @mc_config(ef2_pp_prod, load_now=True)
    def config0(_):
        with ConfigItem():
            with X() as x:
                x.aa = 2
                XChild(aa=1)

    cr = config0(prod2).ConfigItem
    assert cr.X.aa == 2
    assert cr.X.XChild.aa == 17


def test_mc_init_simple_item_definition_less_specific_env_attr_value_merge_to_item_from_with_block():
    class X(ItemWithAA):
        def mc_init(self):
            self.aa = 1
            ItemWithAA(aa=1)

    @mc_config(ef2_pp_prod, load_now=True)
    def config0(_):
        with ConfigItem():
            with X() as x:
                x.aa = 2
                with ItemWithAA() as it:
                    it.setattr('aa', default=1, prod=17)

    cr = config0(prod2).ConfigItem
    assert cr.X.aa == 2
    assert cr.X.ItemWithAA.aa == 17


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

    @mc_config(ef2_pp_prod, load_now=True)
    def config0(_):
        with X1() as x:
            x.aa = 1
            KwargsItem(aa=1)
            with X2() as x:
                x.aa = 2
                KwargsItem(aa=2)
                with X3() as x:
                    x.aa = 3
                    KwargsItem(aa=3)

    cr = config0(prod2)
    assert cr.X1.aa == 1
    assert cr.X1.bb is None  # v6 change: None is no longer overridable
    assert cr.X1.KwargsItem.aa == 1
    assert cr.X1.KwargsItem.bb == 11  # v6 change: 'bb' exist because of object merge

    assert cr.X1.X2.aa == 2
    assert cr.X1.X2.bb is None  # v6 change: None is no longer overridable
    assert cr.X1.X2.KwargsItem.aa == 2
    assert cr.X1.X2.KwargsItem.bb == 12  # v6 change: 'bb' exist because of object merge

    assert cr.X1.X2.X3.aa == 3
    assert cr.X1.X2.X3.bb is None  # v6 change: None is no longer overridable
    assert cr.X1.X2.X3.KwargsItem.aa == 3
    assert cr.X1.X2.X3.KwargsItem.bb == 13  # v6 change: 'bb' exist because of object merge

    @mc_config(ef2_pp_prod, load_now=True)
    def config1(_):
        with X1() as x:
            x.aa = 1
            with X2() as x:
                x.aa = 2
                x.setattr('bb', prod=17)
                X3()

    cr = config1(prod2)
    assert cr.X1.aa == 1
    assert cr.X1.bb is None  # v6 change: None is no longer overridable
    assert cr.X1.KwargsItem.aa == 11
    assert cr.X1.KwargsItem.bb == 11

    assert cr.X1.X2.aa == 2
    assert cr.X1.X2.bb == 17
    assert cr.X1.X2.KwargsItem.aa == 12
    assert cr.X1.X2.KwargsItem.bb == 12

    assert cr.X1.X2.X3.aa == 13
    assert cr.X1.X2.X3.bb is None  # v6 change: None is no longer overridable
    assert cr.X1.X2.X3.KwargsItem.aa == 13
    assert cr.X1.X2.X3.KwargsItem.bb == 13


def test_override_attr_in_init():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super().__init__()
            self.aa = aa
            self.setattr('aa', default=17, mc_force=True)

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        X()

    cr = config(prod2)
    assert cr.X.aa == 17

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with X(aa=2) as x:
            x.aa = 3

    cr = config(pp2)
    assert cr.X.aa == 3


def test_mc_init_override_change_type():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super().__init__()
            self.aa = aa

        def mc_init(self):
            # TODO? force is allowed to change the attribute type, from v6 there is no type check
            self.setattr("aa", default="Hello", mc_force=True)

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with X() as x:
            assert x.aa == 1
        assert x.aa == "Hello"


def test_override_repeated_attr():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with ItemWithAA() as ci:
            ci.aa = 1
            ci.setattr('aa', default=7, mc_force=True)

    ci = config(prod2).ItemWithAA
    assert ci.aa == 7


def test_override_repeated_unknown_attr():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with ConfigItem() as ci:
            ci.setattr('aa', default=1, mc_set_unknown=True)
            ci.setattr('aa', default=7, mc_force=True)

    ci = config(prod2).ConfigItem
    assert ci.aa == 7


def test_mc_init_setattr_ref_env_value():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super().__init__()
            self.aa = aa

        def mc_init(self):
            self.setattr("aa", prod=3)

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        x = X()

    cr = config(pp2)
    assert cr.X.aa == 1

    cr = config(prod2)
    assert cr.X.aa == 3


def test_mc_init_setattr_ref_env_value_from_with():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super().__init__()
            self.aa = aa

        def mc_init(self):
            self.setattr("aa", prod=3)

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with X() as x:
            x.setattr('aa', default=13, pp=4, prod=7)

    cr = config(prod2)
    assert cr.X.aa == 7

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with X() as x:
            x.setattr('aa', default=13, pp=4)

    cr = config(prod2)
    assert cr.X.aa == 3

    cr = config(pp2)
    assert cr.X.aa == 4

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with X() as x:
            x.setattr('aa', default=13)

    cr = config(pp2)
    assert cr.X.aa == 13


def test_attribute_args_partial_set_in_init_overridden_or_finished_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=13):
            super().__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('bb', default=17, prod=2)

        def mc_init(self):
            self.setattr('aa', pp=7)
            self.bb = 7

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        Requires()

    cr = config(prod2)
    assert cr.Requires.aa == 13
    assert cr.Requires.bb == 2

    cr = config(pp2)
    assert cr.Requires.aa == 7
    assert cr.Requires.bb == 17  # Pre v6 this would be 7!

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Requires() as req:
            req.bb = 3

    cr = config(pp2)
    assert cr.Requires.aa == 7
    assert cr.Requires.bb == 3


def test_item_equality():
    class X(ConfigItem):
        pass

    class Y(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        X()
        Y()

    cr = config(prod2)
    assert cr.X == cr.X
    assert cr.X != cr.Y  # TODO? Equality between items?

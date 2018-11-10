# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict
# pylint: disable=E0611
from pytest import raises, fail

from multiconf import mc_config, McConfigRoot, ConfigItem, RepeatableConfigItem, MC_REQUIRED
from multiconf.decorators import nested_repeatables, named_as, required

from .utils.tstclasses import ItemWithAA, ItemWithAABB



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
    with McConfigRoot() as cr:
        with nc_aa_root():
            with rchild(mc_key=None, aa=1, bb=1) as ci:
                ci.aa = 3

    assert cr.nc_aa_root.children[None].aa == 3


def test_iteritems_root_attributes():
    with McConfigRoot():
        with aabb_root() as cr:
            cr.aa = 1
            cr.bb = 2

    for _, _ in cr.items():
        fail("items() yielded something, but there should be no items!")


def test_iteritems_item_attributes():
    @required('anitem')
    class myitem(ConfigItem):
        def __init__(self):
            super().__init__()
            self.aa = MC_REQUIRED

    with McConfigRoot():
        with myitem() as ci:
            ci.aa = 1
            anitem()

    for key, value in ci.items():
        if key == 'aa':
            fail("items() returned attribute!")
        if key == 'anitem':
            assert value.xx == 1
            continue

        fail("unexpected key {} returned from 'items()'".format(key))


def test_property_none():
    with McConfigRoot():
        with ItemWithAA() as cr:
            cr.aa = None

    assert cr.aa is None


def test_assigned_default_value_overrides_default_value_from_init():
    with McConfigRoot():
        with KwargsItem(aa=1) as ci:
            ci.aa = 2

    assert ci.aa == 2


def test_attribute_is_an_ordereddict():
    with McConfigRoot() as cr:
        with ItemWithAA() as x:
            x.aa = 0
        od = OrderedDict(((None, 1), ('foo', x)))
        KwargsItem(aa=od)

    assert cr.KwargsItem.aa == od


def test_hasattr():
    ii_exp = [None]

    class root(ConfigItem):
        pass

    with McConfigRoot():
        with root():
            with KwargsItem(aa=1, bb=0) as ii:
                ii.bb = 2
                ii.setattr('cc', default=3, mc_set_unknown=True)
                assert not hasattr(ii, 'dd')

            assert hasattr(ii, 'aa')
            assert hasattr(ii, 'bb')
            assert hasattr(ii, 'cc')
            assert not hasattr(ii, 'dd')

    assert hasattr(ii, 'aa')
    assert hasattr(ii, 'bb')
    assert hasattr(ii, 'cc')
    assert not hasattr(ii, 'dd')

    with raises(AttributeError) as exinfo:
        print(ii.dd)


def test_inherited_root_with_nested_repeatable_item():
    @nested_repeatables('children')
    class NewRoot(McConfigRoot):
        pass

    with NewRoot() as cr:
        with rchild(mc_key=1, aa=1, bb=1) as ci:
            ci.aa = 3

    assert cr.children[1].aa == 3


def test_mc_config_root_no_mc_select_envs():
    """Test that root does not have mc_select_envs (it does not make sense to exclude everything)"""

    with raises(AttributeError) as exinfo:
        with McConfigRoot() as rt:
            rt.mc_select_envs()

    assert "'McConfigRoot' object has no attribute 'mc_select_envs'" in str(exinfo.value)

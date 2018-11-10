# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import replace_ids, local_func
from .utils.tstclasses import ItemWithAA


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)


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
        for key, val in kwargs.items():
            setattr(self, key, val)


def test_find_contained_in_named_as():
    @named_as('x')
    @nested_repeatables('recursive_items')
    class X(ItemWithAA):
        pass

    @named_as('y')
    class Y(ItemWithAA):
        pass

    @nested_repeatables('recursive_items')
    class root3(ItemWithAA):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with root3() as cr:
            cr.aa = 0
            NestedRepeatable(mc_key=0)
            with X() as ci:
                ci.setattr('aa', prod=0, pp=2)
                NestedRepeatable(mc_key='aa')
                with NestedRepeatable(mc_key='bb') as ci:
                    NestedRepeatable(mc_key='cc')
                    with X() as ci:
                        ci.setattr('aa', prod=1, pp=2)
                        with NestedRepeatable(mc_key='dd') as ci:
                            ci.setattr('aa', prod=2, pp=2)
                            with Y() as ci:
                                ci.setattr('aa', prod=3, pp=2)

    cr = config(prod2).root3
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
    class root4(ItemWithAA):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with root4(aa=-1) as cr:
            cr.setattr('q', default='q0', mc_set_unknown=True)
            NestedRepeatable(mc_key=0)
            with X() as ci:
                ci.setattr('yy', default=999, mc_set_unknown=True)
                ci.setattr('aa', prod=0, pp=20)
                NestedRepeatable(mc_key='aa', aa=9)
                with NestedRepeatable(mc_key='bb') as ci:
                    NestedRepeatable(mc_key='cc', aa=7)
                    with X() as ci:
                        ci.aa = 117
                        ci.setattr('bb', prod='b1', pp='b21', mc_set_unknown=True)
                        with NestedRepeatable(mc_key='dd') as ci:
                            ci.setattr('aa', prod=2, pp=22)
                            with X() as ci:
                                ci.setattr('aa', prod=3, pp=23)

    cr = config(prod2).root4
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('aa') == 3
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('bb') == 'b1'
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('q') == 'q0'
    assert cr.x.recursive_items['bb'].x.find_attribute(name='aa') == 117
    assert cr.x.recursive_items['bb'].x.contained_in.find_attribute(name='aa') is None
    assert cr.x.recursive_items['bb'].x.find_attribute(name='yy') == 999

    # Find Item, not attribute, on parent
    assert cr.x.recursive_items['bb'].x.recursive_items['dd'].x.find_attribute('recursive_items')['dd'].aa == 2


def test_find_contained_in_or_none():
    i1_exp = [None]

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=1) as i1:
            i1_exp[0] = i1
            KwargsItem(aa=2)

    cr = config(prod2)
    assert cr.KwargsItem.KwargsItem.find_contained_in_or_none('notthere') is None
    assert cr.KwargsItem.KwargsItem.find_contained_in_or_none('KwargsItem') == i1_exp[0]


def test_find_attribute_or_none():
    exp_item = [None]

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with KwargsItem(aa=1, my_attr=0) as i1:
            i1.my_attr = 7
            KwargsItem(aa=2)
            exp_item[0] = ConfigItem()

    cr = config(prod2)
    assert cr.KwargsItem.KwargsItem.find_attribute_or_none('notthere') is None
    assert cr.KwargsItem.KwargsItem.find_attribute_or_none('my_attr') == 7

    # Find Item, not attribute, on parent
    assert cr.KwargsItem.KwargsItem.find_attribute_or_none('ConfigItem') == exp_item[0]


_find_contained_in_named_as_not_found_expected = """Searching from: <class 'test.find_test.%(local_func)sY'>: Could not find a parent container named as: 'notthere' in hieracy with names: ['someitems', 'x', 'someitems', 'x', 'root', 'McConfigRoot']"""

def test_find_contained_in_named_as_not_found():
    @named_as('someitems')
    @nested_repeatables('someitems')
    class NestedRepeatable(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.id = mc_key
            self.a = None

    @named_as('x')
    @nested_repeatables('someitems')
    class X(ItemWithAA):
        pass

    @named_as('y')
    class Y(ItemWithAA):
        pass

    @nested_repeatables('someitems')
    class root(ItemWithAA):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with root(aa=0):
            NestedRepeatable(mc_key=0)
            with X() as ci:
                ci.setattr('aa', prod=0)
                NestedRepeatable(mc_key='a')
                with NestedRepeatable(mc_key='b') as ci:
                    NestedRepeatable(mc_key='c')
                    with X() as ci:
                        ci.setattr('aa', prod=1)
                        with NestedRepeatable(mc_key='d') as ci:
                            ci.setattr('a', prod=2)
                            with Y() as ci:
                                ci.setattr('aa', prod=3)

    cr = config(prod1).root
    with raises(ConfigException) as exinfo:
        cr.x.someitems['b'].x.someitems['d'].y.find_contained_in(named_as='notthere').a

    assert replace_ids(str(exinfo.value)) == _find_contained_in_named_as_not_found_expected % dict(local_func=local_func())


_find_attribute_with_attribute_name_not_found = """Searching from: <class 'test.find_test.%(local_func)sX'>: Could not find an attribute named: 'e' in hieracy with names: ['x', 'someitems', 'x', 'someitems', 'x', 'root', 'McConfigRoot']"""

def test_find_attribute_with_attribute_name_not_found():
    @named_as('someitems')
    @nested_repeatables('someitems')
    class NestedRepeatable(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.id = mc_key
            self.a = None

    @named_as('x')
    @nested_repeatables('someitems')
    class X(ItemWithAA):
        pass

    @nested_repeatables('someitems')
    class root(ItemWithAA):
        def __init__(self, aa):
            super().__init__(aa=aa)
            self.q = None

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with root(aa=0) as cr:
            cr.q = 17
            NestedRepeatable(mc_key=1)
            with X() as ci:
                ci.setattr('aa', prod=0)
                with NestedRepeatable(mc_key='a') as nr:
                    nr.a = 9
                with NestedRepeatable(mc_key='b') as ci:
                    with NestedRepeatable(mc_key='c') as nr:
                        nr.a = 7
                    with X(aa=1) as ci:
                        ci.setattr('b', prod=1, mc_set_unknown=True)
                        with NestedRepeatable(mc_key='d') as ci:
                            ci.setattr('a', prod=2)
                            with X() as ci:
                                ci.setattr('aa', prod=3)

    cr = config(prod1).root
    with raises(ConfigException) as exinfo:
        assert cr.x.someitems['b'].x.someitems['d'].x.find_attribute('e') == 3

    assert replace_ids(str(exinfo.value)) == _find_attribute_with_attribute_name_not_found % dict(local_func=local_func())

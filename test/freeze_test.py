# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict
# pylint: disable=E0611
from pytest import fail

from multiconf import mc_config, ConfigItem, MC_REQUIRED
# from multiconf import ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA, ItemWithAABB


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)


# @nested_repeatables('children')
# class nc_aa_item(ConfigItem):
#     def __init__(self, selected_env, env_factory, aa=None):
#         super(nc_aa_item, self).__init__(selected_env, env_factory)
#         self.aa = aa


class aabb_root(ConfigItem):
    def __init__(self, aa=None, bb=None):
        super(aabb_root, self).__init__()
        self.aa = aa
        self.bb = bb


# @named_as('children')
# class rchild(RepeatableConfigItem):
#     def __init__(self, name, aa=None, bb=None):
#         super(rchild, self).__init__(mc_key=name)
#         self.name = name
#         self.aa = aa
#         self.bb = bb


# @named_as('recursive_items')
# @nested_repeatables('recursive_items')
# class NestedRepeatable(RepeatableConfigItem):
#     def __init__(self, id, aa=None):
#         super(NestedRepeatable, self).__init__(mc_key=id)
#         self.id = id
#         self.aa = aa


class anitem(ConfigItem):
    xx = 1


class anotheritem(ConfigItem):
    xx = 2


# def test_contained_in_root_conf():
#     with ConfigItem(prod2, ef2_pp_prod) as conf:
#         assert conf.root_conf == conf
#         assert conf.contained_in is None
#
#         with ConfigItem() as c1:
#             assert c1.root_conf == conf
#             assert c1.contained_in == conf
#
#             with ConfigItem() as c2:
#                 assert c2.root_conf == conf
#                 assert c2.contained_in == c1
#
#
# def test_nested_repeatable_items():
#     with nc_aa_item(prod2, ef2_pp_prod) as cr:
#         with rchild(name="first", aa=1, bb=1) as ci:
#             ci.setattr('aa', prod=3)
#
#         with rchild(name="second", aa=4) as ci:
#             ci.setattr('bb', prod=2, pp=17)
#
#         with rchild(name="third") as ci:
#             ci.setattr('aa', prod=5, pp=18)
#             ci.setattr('bb', prod=3, pp=19)
#
#     assert cr.children['first'].bb == 1
#     assert cr.children['second'].bb == 2
#     assert cr.children['third'].bb == 3
#
#     index = 3
#     for ci in cr.children.values():
#         assert ci.aa == index
#         index += 1
#
#
# def test_empty_nested_repeatable_items():
#     with nc_aa_item(prod2, ef2_pp_prod) as cr:
#         pass
#
#     for _ci in cr.children.values():
#         fail("list should be empty")
#
#
# def test_unnamed_nested_repeatable_item_no_name_or_id():
#     with nc_aa_item(prod2, ef2_pp_prod) as cr:
#         with rchild(name=None, aa=1, bb=1) as ci:
#             ci.setattr('aa', prod=3)
#         ci_id = id(ci)
#
#     assert cr.children[ci_id].aa == 3
#
#
# def test_unnamed_nested_repeatable_item_no_default_name_or_id():
#     with nc_aa_item(prod2, ef2_pp_prod) as cr:
#         with rchild(name=None, aa=1, bb=1) as ci:
#             ci.setattr('name', prod='somevalue', pp='another')
#         ci_id = id(ci)
#
#     assert cr.children[ci_id].aa == 1
#     assert cr.children[ci_id].name == 'somevalue'
#
#
# def test_iteritems_root_attributes():
#     with aabb_root(prod2, ef2_pp_prod) as cr:
#         cr.aa = 1
#         cr.bb = 2
#
#     for exp, actual in zip([('aa', 1), ('bb', 2)], list(cr.items())):
#         exp_key, exp_value = exp
#         key, value = actual
#         assert exp_key == key
#         assert exp_value == value
#
#
# def test_iteritems_item_attributes():
#     @required('anitem')
#     class myitem(ConfigItem):
#         def __init__(self):
#             super(myitem, self).__init__()
#             self.aa = MC_REQUIRED
#
#     with ConfigItem(prod2, ef2_pp_prod):
#         with myitem() as ci:
#             ci.aa = 1
#             anitem()
#
#     for key, value in ci.items():
#         if key == 'aa':
#             assert value == 1
#             continue
#         if key == 'anitem':
#             assert value.xx == 1
#             continue
#
#         fail("unexpected key {} returned from 'items()'".format(key))
#
#
# def test_property_defined_with_same_type_and_none():
#     with ItemWithAA(prod2, ef2_pp_prod) as cr:
#         cr.setattr('aa', default=None, prod=1, pp=2)
#     assert cr.aa == 1
#
#
# def test_property_defined_with_none_and_same_type():
#     with ItemWithAA(prod2, ef2_pp_prod) as cr:
#         cr.setattr('aa', default=1, prod=None, pp=2)
#     assert cr.aa is None
#

def test_automatic_freeze_of_child_on_exit():
    @mc_config(ef1_prod)
    def config(root):
        with ItemWithAA() as ci:
            ci.aa = 1
    prod_cfg = ef1_prod.config(prod1)
    assert prod_cfg.ItemWithAA.aa == 1


# def test_automatic_freeze_of_previous_sibling():
#     with nc_aa_item(prod2, ef2_pp_prod, aa=0) as rt:
#         rchild(name='aa', aa=18)
#         assert rt.children['aa'].aa == 18


# TODO test_automatic_freeze_of_previous_sibling mc_init


# def test_automatic_freeze_call_of_validate_root():
#     @nested_repeatables('children')
#     class root(ConfigItem):
#         def __init__(self, mc_json_filter=None, mc_json_fallback=None,
#                      mc_allow_todo=False, mc_allow_current_env_todo=False,
#                      aa=None):
#             super(root, self).__init__(mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
#                 mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
#             self.aa = aa
#
#         def validate(self):
#             self.aa = 7
#
#     with root(prod2, ef2_pp_prod) as rt:
#         pass
#     assert rt.aa == 7
#
#
# def test_automatic_freeze_call_of_validate_set_unknown_root():
#     @nested_repeatables('children')
#     class root(ConfigItem):
#         def validate(self):
#             self.setattr('y?', default=7)
#
#     with root(prod2, ef2_pp_prod) as rt:
#         pass
#     assert rt.y == 7
#
#
# def test_automatic_freeze_call_of_validate_item():
#     class item(ConfigItem):
#         def __init__(self):
#             super(item, self).__init__()
#             self.aa = None
#
#         def validate(self):
#             self.aa = 7
#
#     with ConfigItem(prod2, ef2_pp_prod):
#         ii = item()
#
#     assert ii.aa == 7
#
#
# def test_automatic_freeze_call_of_validate_item_not_previously_set():
#     class item(ConfigItem):
#         def validate(self):
#             self.aa = 7
#
#     with ConfigItem(prod2, ef2_pp_prod):
#         ii = item()
#
#     assert ii.aa == 7
#
#
# def test_automatic_freeze_call_of_validate_set_unknown_item():
#     class item(ConfigItem):
#         def validate(self):
#             self.setattr('y?', default=7)
#
#     with nc_aa_item(prod2, ef2_pp_prod, aa=0):
#         ii = item()
#
#     assert ii.y == 7
#
#
# def test_automatic_freeze_call_of_validate_builder():
#     class builder(ConfigBuilder):
#         def validate(self):
#             self.y = 7
#
#         def build(self):
#             pass
#
#     with nc_aa_item(prod2, ef2_pp_prod, aa=0):
#         ii = builder()
#
#     assert ii.y == 7
#
#
# def test_automatic_contained_item_freeze_on_exit():
#     @nested_repeatables('recursive_items')
#     class root2(ConfigItem):
#         pass
#
#     with root2(prod2, ef2_pp_prod) as cr:
#         NestedRepeatable(id='aa')
#         with NestedRepeatable(id='bb') as ci:
#             NestedRepeatable(id='aa')
#             with NestedRepeatable(id='bb') as ci:
#                 NestedRepeatable(id='aa')
#                 with NestedRepeatable(id='bb') as ci:
#                     ci.setattr('aa', prod=1, pp=2)
#                 NestedRepeatable(id='cc')
#             NestedRepeatable(id='cc')
#         NestedRepeatable(id='cc')
#
#     assert len(cr.recursive_items['aa'].recursive_items) == 0
#     assert len(cr.recursive_items['bb'].recursive_items) == 3
#     assert len(cr.recursive_items['cc'].recursive_items) == 0
#
#     ids = ['aa', 'bb', 'cc']
#     index = 0
#     for item_id, item in cr.recursive_items['bb'].recursive_items.items():
#         assert item.id == ids[index]
#         assert item_id == ids[index]
#         index += 1
#     assert index == 3
#
#     assert cr.recursive_items['bb'].recursive_items['bb'].recursive_items['bb'].aa == 1
#
#
# def test_automatic_freeze_of_property_defined_in_with_statement_unknown():
#     with nc_aa_item(prod2, ef2_pp_prod, aa=0):
#         with rchild(name='aa') as rc:
#             rc.setattr('y?', prod=1, pp=2)
#             assert rc.y == 1
#

# def test_automatic_freeze_of_property_overridden_in_with_statement():
#     with nc_aa_item(prod2, ef2_pp_prod, aa=0):
#         with rchild(name='aa', bb=18) as rc:
#             rc.setattr('bb', prod=7, pp=2)
#             assert rc.bb == 7
#
#
# def test_freeze_of_property_at_access():
#     with nc_aa_item(prod2, ef2_pp_prod, aa=0):
#         with rchild(name='aa', aa=19, bb=20) as rc:
#             assert rc.aa == 19


# TODO: allow this (while inside with statement only)
#def define new attribute after freeze_test(self):
#    with nc_aa_item(prod2, ef2_pp_prod, aa=0):
#        with rchild(id='aa', x=19, z=20) as rc:
#            rc.setattr('y', prod=7, pp=2)
#            assert rc.y == 7
#            rc.setattr('z', pp=3)
#            assert rc.z == 20
#            assert rc.x == 19
#            rc.a(prod=3, pp=4)
#            assert rc.aa == 3


def test_required_items_not_required_on_imtermediate_freeze_configroot():
    @required('anitem', 'anotheritem')
    class root(ConfigItem):
        pass

    @mc_config(ef1_prod)
    def config(rr):
        with root() as cr:
            anitem()
            # Accessing anitem here will not freeze cr
            assert cr.anitem.xx == 1
            anotheritem()
            assert cr.anotheritem.xx == 2


def test_mc_required_attributes_not_required_on_imtermediate_freeze_configroot():
    class root(ConfigItem):
        def __init__(self):
            super(root, self).__init__()
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

    @mc_config(ef1_prod)
    def config(rr):
        with root() as cr:
            cr.setattr('anattr', prod=1)
            # Accessing anattr here will not freeze cr
            assert cr.anattr == 1
            cr.setattr('anotherattr', prod=2)
            assert cr.anotherattr == 2


def test_required_items_not_required_on_imtermediate_freeze_configitem():
    class root(ConfigItem):
        pass

    @required('anitem', 'anotheritem')
    class item(ConfigItem):
        pass

    @mc_config(ef1_prod)
    def config(rr):
        with root() as cr:
            with item() as ii:
                anitem()
                assert ii.anitem.xx == 1
                anotheritem()
                assert cr.item.anotheritem.xx == 2


def test_mc_required_attributes_not_required_on_imtermediate_freeze_configitem():
    class root(ConfigItem):
        pass

    class item(ConfigItem):
        def __init__(self):
            super(item, self).__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED

    @mc_config(ef1_prod)
    def config(rr):
        with root() as cr:
            with item() as ii:
                ii.aa = 1
                assert cr.item.aa == 1
                ii.setattr('bb', prod=2)
                assert cr.item.bb == 2

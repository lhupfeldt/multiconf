#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from oktest import fail

from .utils import config_error, lineno, replace_ids, replace_user_file_line_tuple, replace_user_file_line_msg

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException, ConfigDefinitionException
from ..decorators import nested_repeatables, repeat
from ..envs import EnvFactory

ef = EnvFactory()

dev2ct = ef.Env('dev2CT')
dev2st = ef.Env('dev2ST')
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3CT')
dev3st = ef.Env('dev3ST')
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

_e_expected = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "hi"
}"""


_f_expected = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "hello"
}"""

_g_expected = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 1
}"""

_h_expected = """The attribute 'a' is already fully defined"""
_h_expected_ex = _h_expected + """ on object {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 1
}"""


_i_expected = """'ConfigItem' is defined both as simple value and a contained item: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen"
}"""


_j_expected = """'RepeatableItems': {
    "__class__": "RepeatableItem #as: 'RepeatableItems', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"""


_k1_expected = """'RepeatableItems': {
    "__class__": "RepeatableItem #as: 'RepeatableItems', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"""


_k4_expected = """'RepeatableItems': {
    "__class__": "RepeatableItems #as: 'RepeatableItems', id: 0000, not-frozen"
} is defined as non-repeatable, but the containing object has repeatable items with the same name: {
    "__class__": "project #as: 'project', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "RepeatableItems": {}
}"""


_o_expected = """A value is already specified for: Env('dev2CT') from group EnvGroup('g_dev_overlap') {
     Env('dev2CT')
}=(3, ('fake_dir/multiconf_definition_errors_test.py', 999)), previous value: EnvGroup('g_dev2') {
     Env('dev2CT'),
     Env('dev2ST')
}=(2, ('fake_dir/multiconf_definition_errors_test.py', 999))"""

_o_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 1
}"""


_p_expected = """A value is already specified for: Env('dev2CT') from group EnvGroup('g_dev_overlap') {
     Env('dev2CT'),
     Env('dev3CT')
}=(3, ('fake_dir/multiconf_definition_errors_test.py', 999)), previous value: EnvGroup('g_dev2') {
     Env('dev2CT'),
     Env('dev2ST')
}=(2, ('fake_dir/multiconf_definition_errors_test.py', 999))"""

_p_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 1
}"""


_r_expected = """The attribute 'a' is already fully defined"""
_r1_expected_ex = _r_expected + """ on object {
    "__class__": "project #as: 'project', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "RepeatableItems": {}, 
    "a": 1
}"""
_r2_expected_ex = _r_expected + """ on object {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen", 
    "a": 1
}"""


_group_for_selected_env_expected = """project: env must be instance of 'Env'; found type 'EnvGroup': EnvGroup('g_dev3') {
     Env('dev3CT'),
     Env('dev3ST')
}"""


@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass


@repeat()
class RepeatableItem(ConfigItem):
    pass



def test_non_env_for_instantiatiation_env(capsys):
    try:
        project('Why?', [prod])
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == "project: env must be instance of 'Env'; found type 'str': 'Why?'"


def test_non_env_in_valid_envs(capsys):
    try:
        project(prod, [prod, 'Why?'])
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == "project: valid_envs items must be instance of 'Env' or 'EnvGroup'; found a 'str': 'Why?'"


def test_valid_envs_is_not_a_sequence(capsys):
    try:
        project(prod, 1)
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == "project: valid_envs arg must be a 'Sequence'; found type 'int': 1"


def test_valid_envs_is_a_str(capsys):
    try:
        project(prod, 'Why?')
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == "project: valid_envs arg must be a 'Sequence'; found type 'str': 'Why?'"


def test_valid_envs_arg_as_envgroup(capsys):
    try:
        ConfigRoot(prod, valid_envs)
    except ConfigException as ex:
        pass


def test_selected_conf_not_in_valid_envs(capsys):
    try:
        ConfigRoot(prod, [dev3ct, dev3st])
    except ConfigException as ex:
        pass


def test_assign_to_undefine_env(capsys):
    try:
        with ConfigRoot(prod, [prod]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', pros="hello", prod="hi")
        fail ("Expected exception")
    except ConfigException as ex:
        _sout, serr = capsys.readouterr()
        assert serr == ce(errorline, "No such Env or EnvGroup: 'pros'")
        assert replace_ids(ex.message, False) == _e_expected


def test_value_not_assigned_to_all_envs(capsys):
    try:
        with ConfigRoot(prod, [prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod="hello")
        fail ("Expected exception")
    except ConfigException as ex:
        _sout, serr = capsys.readouterr()
        assert serr == ce(errorline, "Attribute: 'a' did not receive a value for env Env('pp')")
        assert replace_ids(ex.message, False) == _f_expected

# TODO handle this error output format in test
# def attribute_defined_with_different_types(self):
#     try:
#         with ConfigRoot(prod, [prod, pp]) as cr:
#             errorline = lineno() + 1
#             cr.setattr('a', prod=1, pp="hello")
#         fail ("Expected exception")
#     except ConfigException as ex:
#         _sout, serr = capsys.readouterr()
#         assert serr == ce(errorline, "ConfigError: Found different value types for property 'a' for different envs")
#         assert replace_ids(ex.message, False) == _g_expected


def test_attribute_redefinition_attempt(capsys):
    try:
        with ConfigRoot(prod, [prod]) as cr:
            cr.setattr('a', prod=1)
            errorline = lineno() + 1
            cr.setattr('a', prod=2)
            fail ("Expected exception")
    except ConfigException as ex:
        _sout, serr = capsys.readouterr()
        assert serr == ce(errorline, _h_expected)
        assert replace_ids(ex.message, named_as=False) == _h_expected_ex


def test_nested_item_overrides_simple_attribute(capsys):
    try:
        with ConfigRoot(prod, [prod]) as cr:
            cr.setattr('ConfigItem', prod="hello")
            ConfigItem()
        fail ("Expected exception")
    except ConfigException as ex:
        assert replace_ids(ex.message, named_as=False) == _i_expected


def test_nested_repeatable_item_not_defined_as_repeatable_in_contained_in_class(capsys):
    try:
        with ConfigRoot(prod, [prod]) as cr:
            RepeatableItem()
        fail ("Expected exception")
    except ConfigException as ex:
        assert replace_ids(ex.message, named_as=False) == _j_expected


def test_nested_repeatable_item_overrides_simple_attribute_not_contained_in_repeatable(capsys):
    try:
        with ConfigRoot(prod, [prod]) as cr:
            # cr.RepeatableItems is just an attribute named like an item
            cr.setattr('RepeatableItems', prod="hello")
            RepeatableItem()
        fail ("Expected exception")
    except ConfigException as ex:
        assert replace_ids(ex.message, named_as=False) == _k1_expected


def test_nested_repeatable_item_shadowed_by_default_attribute(capsys):
    try:
        # RepeatableItems is just an attribute named like an item
        with project(prod, [prod], RepeatableItems=1) as cr:
            RepeatableItem()
        fail ("Expected exception")
    except ConfigException as ex:
        assert replace_ids(ex.message, named_as=False) == "'RepeatableItems' defined as default value shadows a nested-repeatable"

# def nested_repeatable_item_overrides_simple_attribute_contained_in_repeatable(self):
# @todo
#     try:
#         @nested_repeatables('children')
#         class root(ConfigRoot):
#             pass
#
#         @named_as('children')
#         class rchild(RepeatableItem):
#             pass
#
#         with root(prod, [prod]) as cr:
              # TODO: 'cr' is an OrderedDict, so this call is not possible, which is fine, but the error message is not good
#             cr.children(prod="hello")
#             rchild()
#         fail ("Expected exception")
#     except ConfigException as ex:
#         assert ex.message == "'children' is defined both as simple value and a contained item: children {\n}"


def test_non_repeatable_but_container_expects_repeatable(capsys):
    try:
        # The following class in not repeatable!
        class RepeatableItems(ConfigItem):
            pass

        with project(prod, [prod]) as cr:
            RepeatableItems()
        fail ("Expected exception")
    except ConfigException as ex:
        assert replace_ids(ex.message, named_as=False) == _k4_expected


def test_simple_attribute_attempt_to_override_contained_item(capsys):
    try:
        with ConfigRoot(prod, [prod]) as cr:
            ConfigItem()
            errorline = lineno() + 1
            cr.ConfigItem(prod="hello")
        fail ("Expected exception")
    except TypeError as ex:
        assert ex.message == "'ConfigItem' object is not callable"


def test_repeated_non_repeatable_item(capsys):
    try:
        with ConfigRoot(prod, [prod]) as cr:
            ConfigItem()
            errorline = lineno() + 1
            ConfigItem()
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == "Repeated non repeatable conf item: 'ConfigItem'"


def test_nested_repeatable_items_with_repeated_name(capsys):
    try:
        with project(prod, [prod]) as cr:
            RepeatableItem(id='my_name')
            RepeatableItem(id='my_name')
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == "Re-used id/name 'my_name' in nested objects"


def test_value_defined_through_multiple_groups(capsys):
    try:
        g_dev_overlap = ef.EnvGroup('g_dev_overlap', dev2ct)

        with ConfigRoot(prod, [prod, g_dev2, g_dev_overlap]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=1, g_dev2=2, g_dev_overlap=3)
        fail ("Expected exception")
    except ConfigException as ex:
        _sout, serr = capsys.readouterr()
        assert replace_user_file_line_tuple(serr) == ce(errorline, _o_expected)
        assert replace_ids(ex.message, False) == _o_expected_ex


def test_value_defined_through_multiple_groups2(capsys):
    try:
        g_dev_overlap = ef.EnvGroup('g_dev_overlap', dev2ct, dev3ct)

        with ConfigRoot(prod, [prod, g_dev2, g_dev_overlap]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=1, g_dev2=2, g_dev_overlap=3)
        fail ("Expected exception")
    except ConfigException as ex:
        _sout, serr = capsys.readouterr()
        assert replace_user_file_line_tuple(serr) == ce(errorline, _p_expected)
        assert replace_ids(ex.message, False) == _p_expected_ex


def test_assigning_owerwrites_attribute_root(capsys):
    try:
        with project(prod, [prod]) as cr:
            cr.setattr('a', prod=1)
            errorline = lineno() + 1
            cr.a = 2
        fail ("Expected exception")
    except ConfigException as ex:
        _sout, serr = capsys.readouterr()
        assert serr == ce(errorline, _r_expected)
        assert replace_ids(ex.message, named_as=False) == _r1_expected_ex


def test_assigning_owerwrites_attribute_nested_item(capsys):
    try:
        with project(prod, [prod]) as cr:
            with ConfigItem() as ci:
                ci.setattr('a', prod=1)
                errorline = lineno() + 1
                ci.a = 1
        fail ("Expected exception")
    except ConfigException as ex:
        _sout, serr = capsys.readouterr()
        assert serr == ce(errorline, _r_expected)
        assert replace_ids(ex.message, named_as=False) == _r2_expected_ex


def test_configitem_outside_of_root(capsys):
    try:
        ConfigItem()
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == "ConfigItem object must be nested (indirectly) in a 'ConfigRoot'"


def test_using_group_for_selected_env(capsys):
    try:
        project(g_dev3, [g_dev3])
        fail ("Expected exception")
    except ConfigException as ex:
        assert ex.message == _group_for_selected_env_expected


def test_exception_in___exit___must_print_ex_info_and_raise_original_exception_if_any_pending(capsys):
    try:
        class root(ConfigRoot):
            pass

        class inner(ConfigBuilder):
            def build(self):
                raise Exception("in build")

        with root(prod, [prod, pp], a=0):
            with inner(id='n1', b=1):
                raise Exception("in with")

        fail ("Expected exception")
    except Exception as ex:
        _sout, serr = capsys.readouterr()
        assert serr == "Exception in __exit__: Exception('in build',)\nException in with block will be raised\n"
        assert ex.message == 'in with'


def test_builder_does_not_accept_nested_repeatables_decorator(capsys):
    try:
        @nested_repeatables('a')
        class _inner(ConfigBuilder):
            def build(self):
                _a = 1

        fail ("Expected exception")
    except ConfigDefinitionException as ex:
        _sout, serr = capsys.readouterr()
        err_msg = "File \"fake_dir/multiconf_definition_errors_test.py\", line 999\nConfigError: Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder.\n"
        assert replace_user_file_line_msg(serr) == err_msg
        assert ex.message == "Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder."

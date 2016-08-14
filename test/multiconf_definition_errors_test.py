# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, replace_ids, replace_user_file_line_msg, assert_lines_in, py3_local, total_msg
from .utils.messages import already_printed_msg, exception_previous_object_expected_stderr
from .utils.messages import config_error_mc_required_current_env_expected, config_error_mc_required_other_env_expected
from .utils.messages import mc_required_current_env_expected, mc_required_other_env_expected
from .utils.messages import config_error_no_value_current_env_expected, config_error_no_value_other_env_expected
from .utils.messages import no_value_current_env_expected, no_value_other_env_expected
from .utils.tstclasses import RootWithAA, ItemWithAA

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigBuilder, ConfigException, ConfigDefinitionException, MC_REQUIRED
from ..decorators import nested_repeatables, required
from ..envs import EnvFactory


# ef1
ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

# ef2
ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')

# ef3
ef3_dev_prod = EnvFactory()

dev2ct3 = ef3_dev_prod.Env('dev2ct')
dev2st3 = ef3_dev_prod.Env('dev2st')
g_dev23 = ef3_dev_prod.EnvGroup('g_dev2', dev2ct3, dev2st3)

dev3ct3 = ef3_dev_prod.Env('dev3ct')
dev3st3 = ef3_dev_prod.Env('dev3st')
g_dev33 = ef3_dev_prod.EnvGroup('g_dev3', dev3ct3, dev3st3)

g_dev_overlap3 = ef3_dev_prod.EnvGroup('g_dev_overlap', dev2ct3)

g_all_dev3 = ef3_dev_prod.EnvGroup('g_dev', g_dev23, g_dev33)

pp3 = ef3_dev_prod.Env('pp')
prod3 = ef3_dev_prod.Env('prod')
g_prod3 = ef3_dev_prod.EnvGroup('g_prod', pp3, prod3)

g_all3 = ef3_dev_prod.EnvGroup('g_all', g_all_dev3, g_prod3)

# ef4
ef4_dev_prod = EnvFactory()

dev2ct4 = ef4_dev_prod.Env('dev2ct')
dev2st4 = ef4_dev_prod.Env('dev2st')
g_dev24 = ef4_dev_prod.EnvGroup('g_dev2', dev2ct4, dev2st4)

dev3ct4 = ef4_dev_prod.Env('dev3ct')
dev3st4 = ef4_dev_prod.Env('dev3st')
g_dev34 = ef4_dev_prod.EnvGroup('g_dev3', dev3ct4, dev3st4)

g_dev_overlap4 = ef4_dev_prod.EnvGroup('g_dev_overlap', dev2ct4, dev3ct4)

g_all_dev4 = ef4_dev_prod.EnvGroup('g_dev', g_dev24, g_dev34)

pp4 = ef4_dev_prod.Env('pp')
prod4 = ef4_dev_prod.Env('prod')
g_prod4 = ef4_dev_prod.EnvGroup('g_prod', pp4, prod4)

g_all4 = ef4_dev_prod.EnvGroup('g_all', g_all_dev4, g_prod4)

# ef5
ef5_dev_prod = EnvFactory()

dev2ct5 = ef5_dev_prod.Env('dev2ct')
dev2st5 = ef5_dev_prod.Env('dev2st')
g_dev25 = ef5_dev_prod.EnvGroup('g_dev2', dev2ct5, dev2st5)

dev3ct5 = ef5_dev_prod.Env('dev3ct')
dev3st5 = ef5_dev_prod.Env('dev3st')
g_dev35 = ef5_dev_prod.EnvGroup('g_dev3', dev3ct5, dev3st5)

g_dev_overlap15 = ef5_dev_prod.EnvGroup('g_dev_overlap1', dev2ct5)
g_dev_overlap25 = ef5_dev_prod.EnvGroup('g_dev_overlap2', dev2ct5)

g_all_dev5 = ef5_dev_prod.EnvGroup('g_dev', g_dev25, g_dev35)

pp5 = ef5_dev_prod.Env('pp')
prod5 = ef5_dev_prod.Env('prod')
g_prod5 = ef5_dev_prod.EnvGroup('g_prod', pp5, prod5)

g_all5 = ef5_dev_prod.EnvGroup('g_all', g_all_dev5, g_prod5)


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_single_error_on_root_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": %s
}""" + already_printed_msg


_single_error_on_project_expected_ex = """There was 1 error when defining item: {
    "__class__": "project #as: 'project', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    %s
}""" + already_printed_msg

_repeatable_item_json = """{
        "a": {
            "__class__": "RepeatableItem #as: 'RepeatableItems', id: 0000"
        }
    }
""".strip()


_i_expected_ex = """'ConfigItem' is defined both as simple value and a contained item: {
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


_p_expected = """File "fake_dir/multiconf_definition_errors_test.py", line %(line)s
ConfigError: Value for env 'dev2ct' is specified more than once, with no single most specific group or direct env:
value: 2, from: EnvGroup('g_dev2') {
     Env('dev2ct'),
     Env('dev2st')
}
value: 3, from: EnvGroup('g_dev_overlap') {
     Env('dev2ct'),
     Env('dev3ct')
}
File "fake_dir/multiconf_definition_errors_test.py", line %(line)s
ConfigError: Value for env 'dev3ct' is specified more than once, with no single most specific group or direct env:
value: 12, from: EnvGroup('g_dev3') {
     Env('dev3ct'),
     Env('dev3st')
}
value: 3, from: EnvGroup('g_dev_overlap') {
     Env('dev2ct'),
     Env('dev3ct')
}"""

_p_expected_ex = """There were 2 errors when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg


@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass


class RepeatableItem(RepeatableConfigItem):
    pass


def test_non_env_for_instantiatiation_env():
    with raises(ConfigException) as exinfo:
        project('Why?', ef1_prod)

    assert str(exinfo.value) == "project: env must be instance of 'Env'; found type 'str': 'Why?'"


def test_env_factory_is_not_an_env_factory():
    with raises(ConfigException) as exinfo:
        project(prod3, 1)

    assert str(exinfo.value) == "project: env_factory arg must be instance of 'EnvFactory'; found type 'int': 1"


_env_factory_arg_as_envgroup_exp = """ConfigRoot: env_factory arg must be instance of 'EnvFactory'; found type 'EnvGroup': EnvGroup('g_all') {
     EnvGroup('g_dev') {
       EnvGroup('g_dev2') {
         Env('dev2ct'),
         Env('dev2st')
    },
       EnvGroup('g_dev3') {
         Env('dev3ct'),
         Env('dev3st')
    }
  },
     EnvGroup('g_prod') {
       Env('pp'),
       Env('prod')
  }
}"""

def test_env_factory_arg_as_envgroup():
    with raises(ConfigException) as exinfo:
        ConfigRoot(prod3, g_all3)

    assert str(exinfo.value) == _env_factory_arg_as_envgroup_exp


def test_selected_conf_not_from_env_factory():
    with raises(ConfigException) as exinfo:
        ConfigRoot(prod3, EnvFactory())

    assert str(exinfo.value) == """The selected env Env('prod') must be from the specified 'env_factory'"""


def test_assign_to_undefine_env(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', pros="hello", prod="hi")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "No such Env or EnvGroup: 'pros'")
    assert replace_ids(str(exinfo.value), False) == _single_error_on_root_expected_ex % '"hi"'


def test_value_not_assigned_to_all_envs(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod2, ef2_pp_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, mc_required_other_env_expected.format(attr='aa', env=pp2))
    assert replace_ids(str(exinfo.value), False) == _single_error_on_root_expected_ex % '"hello"'


def test_value_not_assigned_to_all_envs_in_builder(capsys):
    with raises(ConfigException) as exinfo:
        class B(ConfigBuilder):
            def build(self):
                pass

        with ConfigRoot(prod2, ef2_pp_prod) as cr:
            with B() as bb:
                errorline = lineno() + 1
                bb.setattr('a', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, no_value_other_env_expected.format(attr='a', env=pp2))


def test_attribute_defined_with_different_types_root(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod2, ef2_pp_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod=1, pp="hello")

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        ("^%(lnum)s, prod <%(type_or_class)s 'int'>", "^%(lnum)s, pp <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_root_expected_ex % 1


def test_attribute_defined_with_different_types_root_default(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod2, ef2_pp_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', default="hello", prod=1)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        ("^%(lnum)s, prod <%(type_or_class)s 'int'>", "^%(lnum)s, default <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_root_expected_ex % 1


_attribute_defined_with_different_types_item_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "aa": 1
}"""

def test_attribute_defined_with_different_types_item(capsys):
    with raises(ConfigException) as exinfo:
        with project(prod2, ef2_pp_prod):
            init_line = lineno() + 1
            with ItemWithAA() as ci:
                errorline = lineno() + 1
                ci.setattr('aa', pp="hello", prod=1)

    _sout, serr = capsys.readouterr()
    assert replace_ids(str(exinfo.value), named_as=False) == _attribute_defined_with_different_types_item_expected_ex + already_printed_msg

    assert_lines_in(
        __file__, errorline, serr,
        ("^%(lnum)s, prod <%(type_or_class)s 'int'>", "^%(lnum)s, pp <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
    )


def test_attribute_defined_with_different_types_item_default(capsys):
    with raises(ConfigException) as exinfo:
        with project(prod1, ef1_prod):
            init_line = lineno() + 1
            with ItemWithAA() as ci:
                errorline = lineno() + 1
                ci.setattr('aa', default="hello", prod=1)

    _sout, serr = capsys.readouterr()
    assert replace_ids(str(exinfo.value), named_as=False) == _attribute_defined_with_different_types_item_expected_ex + already_printed_msg

    assert_lines_in(
        __file__, errorline, serr,
        ("^%(lnum)s, prod <%(type_or_class)s 'int'>", "^%(lnum)s, default <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
    )


_attribute_defined_with_different_types_root_init_expected_ex = """There was 1 error when defining item: {
    "__class__": "root #as: 'root', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": 1
}"""

_attribute_defined_with_different_types_item_init_expected_ex = """There was 1 error when defining item: {
    "__class__": "item #as: 'item', id: 0000",
    "a": 1
}"""

def test_attribute_defined_with_different_types_init(capsys):
    class root(ConfigRoot):
        init_line = 0

        def __init__(self, selected_env, env_factory, a):
            super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)
            root.init_line = lineno() + 1
            self.a = a

    with raises(ConfigException) as exinfo:
        with root(prod2, ef2_pp_prod, a="hello") as cr:
            errorline1 = lineno() + 1
            cr.setattr('a', default=1)

    _sout, serr1 = capsys.readouterr()
    assert replace_ids(str(exinfo.value), False) == _attribute_defined_with_different_types_root_init_expected_ex + already_printed_msg

    class item(ConfigItem):
        init_line = 0

        def __init__(self, a):
            super(item, self).__init__()
            item.init_line = lineno() + 1
            self.a = a

    with raises(ConfigException) as exinfo:
        with project(prod1, ef1_prod):
            with item(a="hello") as ci:
                errorline2 = lineno() + 1
                ci.a = 1

    _sout, serr2 = capsys.readouterr()
    assert replace_ids(str(exinfo.value), named_as=False) == _attribute_defined_with_different_types_item_init_expected_ex + already_printed_msg

    for init_line, errorline, serr in ((root.init_line, errorline1, serr1), (item.init_line, errorline2, serr2)):
        assert_lines_in(
            __file__, errorline, serr,
            "^%(lnum)s, default <%(type_or_class)s 'int'>",
            """^File "%(file_name)s", line {line_num}, default <%(type_or_class)s 'str'>""".format(line_num=init_line),
            "^ConfigError: Found different value types for property 'a' for different envs",
        )


def test_attribute_redefinition_attempt(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod) as cr:
            cr.setattr('aa', prod=1)
            errorline = lineno() + 1
            cr.setattr('aa', prod=2)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "The attribute 'aa' is already fully defined")
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_root_expected_ex % 1


def test_nested_item_overrides_simple_attribute():
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            cr.setattr('ConfigItem?', prod="hello")
            ConfigItem()

    assert replace_ids(str(exinfo.value), named_as=False) == _i_expected_ex


def test_nested_repeatable_item_not_defined_as_repeatable_in_contained_in_class():
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            RepeatableItem(mc_key=None)

    assert replace_ids(str(exinfo.value), named_as=False) == _j_expected


def test_nested_repeatable_item_overrides_simple_attribute_not_contained_in_repeatable():
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            # cr.RepeatableItems is just an attribute named like an item
            cr.setattr('RepeatableItems', prod="hello")
            RepeatableItem(mc_key=None)

    assert replace_ids(str(exinfo.value), named_as=False) == _k1_expected


def test_attempt_to_replace_empty_nested_repeatable_by_attribute_assignment(capsys):
    with raises(ConfigException) as exinfo:
        # RepeatableItems is just an attribute named like an item
        with project(prod1, ef1_prod) as cr:
            errorline = lineno() + 1
            cr.RepeatableItems = 1

    _sout, serr = capsys.readouterr()
    msg = "'RepeatableItems' is already defined as a nested-repeatable and may not be replaced with an attribute."
    assert serr == ce(errorline, msg)
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_project_expected_ex % '"RepeatableItems": {}'


def test_attempt_to_replace_non_empty_nested_repeatable_by_attribute_assignment(capsys):
    with raises(ConfigException) as exinfo:
        # RepeatableItems is just an attribute named like an item
        with project(prod1, ef1_prod) as cr:
            RepeatableItem(mc_key='a')
            errorline = lineno() + 1
            cr.RepeatableItems = 1

    _sout, serr = capsys.readouterr()
    msg = "'RepeatableItems' is already defined as a nested-repeatable and may not be replaced with an attribute."
    assert serr == ce(errorline, msg)
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_project_expected_ex % ('"RepeatableItems": ' + _repeatable_item_json)


# def nested_repeatable_item_overrides_simple_attribute_contained_in_repeatable(self):
# @todo
#     with raises(ConfigException) as exinfo:
#         @nested_repeatables('children')
#         class root(ConfigRoot):
#             pass
#
#         @named_as('children')
#         class rchild(RepeatableItem):
#             pass
#
#         with root(prod1, ef1_prod) as cr:
# TODO: 'cr' is an OrderedDict, so this call is not possible, which is fine, but the error message is not good
#             cr.children(prod="hello")
#             rchild()
#     assert str(exinfo.value) == "'children' is defined both as simple value and a contained item: children {\n}"


def test_non_repeatable_but_container_expects_repeatable():
    with raises(ConfigException) as exinfo:
        # The following class in not repeatable!
        class RepeatableItems(ConfigItem):
            pass

        with project(prod1, ef1_prod):
            RepeatableItems()

    assert replace_ids(str(exinfo.value), named_as=False) == _k4_expected


def test_attempt_to_call_contained_item():
    with raises(TypeError) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            ConfigItem()
            errorline = lineno() + 1
            cr.ConfigItem(prod="hello")

    assert str(exinfo.value) == "'ConfigItem' object is not callable"


def test_simple_attribute_attempt_to_override_contained_item(capsys):
    msg = "'ConfigItem' <class 'multiconf.multiconf.ConfigItem'> is already defined and may not be replaced with an attribute."

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            with ConfigItem():
                pass
            errorline = lineno() + 1
            cr.setattr('ConfigItem', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, msg)

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            ConfigItem()
            errorline = lineno() + 1
            cr.setattr('ConfigItem', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, msg)


def test_repeated_non_repeatable_item():
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            ConfigItem()
            errorline = lineno() + 1
            ConfigItem()

    assert str(exinfo.value) == "Repeated non repeatable conf item: 'ConfigItem'"


def test_nested_repeatable_items_with_repeated_name():
    with raises(ConfigException) as exinfo:
        with project(prod1, ef1_prod):
            RepeatableItem(mc_key='my_name')
            RepeatableItem(mc_key='my_name')

    assert str(exinfo.value) == "Re-used key 'my_name' in nested objects"


_value_defined_through_two_groups_expected = """File "fake_dir/multiconf_definition_errors_test.py", line %(line)s
ConfigError: Value for env 'dev2ct' is specified more than once, with no single most specific group or direct env:
value: 2, from: EnvGroup('g_dev2') {
     Env('dev2ct'),
     Env('dev2st')
}
value: 3, from: EnvGroup('g_dev_overlap') {
     Env('dev2ct')
}"""

_value_defined_through_two_groups_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg

def test_value_defined_through_two_groups(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod3, ef3_dev_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', default=7, prod=1, g_dev2=2, g_dev_overlap=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline) == _value_defined_through_two_groups_expected % dict(line=errorline)
    assert replace_ids(str(exinfo.value), False) == _value_defined_through_two_groups_expected_ex


_value_defined_through_three_groups_expected = """File "fake_dir/multiconf_definition_errors_test.py", line %(line)s
ConfigError: Value for env 'dev2ct' is specified more than once, with no single most specific group or direct env:
value: 2, from: EnvGroup('g_dev2') {
     Env('dev2ct'),
     Env('dev2st')
}
value: 3, from: EnvGroup('g_dev_overlap1') {
     Env('dev2ct')
}
value: 7, from: EnvGroup('g_dev_overlap2') {
     Env('dev2ct')
}"""

_value_defined_through_three_groups_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg

def test_value_defined_through_three_groups(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod5, ef5_dev_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', g_dev_overlap2=7, default=7, prod=1, g_dev2=2, g_dev_overlap1=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline) == _value_defined_through_three_groups_expected % dict(line=errorline)
    assert replace_ids(str(exinfo.value), False) == _value_defined_through_three_groups_expected_ex


def test_two_values_defined_through_two_groups(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod4, ef4_dev_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod=1, dev3st=14, pp=33, g_dev2=2, g_dev3=12, g_dev_overlap=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline) == _p_expected.strip() % dict(line=errorline)
    assert replace_ids(str(exinfo.value), False) == _p_expected_ex


_assigning_owerwrites_attribute_expected = """The attribute 'aa' is already fully defined"""
_assigning_owerwrites_attribute_root_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg


def test_assigning_owerwrites_attribute_root(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod) as cr:
            cr.setattr('aa', prod=1)
            errorline = lineno() + 1
            cr.aa = 2

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _assigning_owerwrites_attribute_expected)
    assert replace_ids(str(exinfo.value), named_as=False) == _assigning_owerwrites_attribute_root_expected_ex


_test_assigning_owerwrites_attribute_nested_item_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "aa": 1
}""" + already_printed_msg

def test_assigning_owerwrites_attribute_nested_item(capsys):
    with raises(ConfigException) as exinfo:
        with project(prod1, ef1_prod):
            with ItemWithAA() as ci:
                ci.setattr('aa', prod=1)
                errorline = lineno() + 1
                ci.aa = 1

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _assigning_owerwrites_attribute_expected)
    assert replace_ids(str(exinfo.value), named_as=False) == _test_assigning_owerwrites_attribute_nested_item_ex


def test_configitem_outside_of_root():
    with raises(ConfigException) as exinfo:
        ConfigItem()

    assert str(exinfo.value) == "ConfigItem object must be nested (indirectly) in a 'ConfigRoot'"


_group_for_selected_env_expected = """project: env must be instance of 'Env'; found type 'EnvGroup': EnvGroup('g_dev3') {
     Env('dev3ct'),
     Env('dev3st')
}"""

def test_using_group_for_selected_env():
    with raises(ConfigException) as exinfo:
        project(g_dev33, ef3_dev_prod)

    assert str(exinfo.value) == _group_for_selected_env_expected


def test_exception_in___exit___must_print_ex_info_and_raise_original_exception_if_any_pending_builder(capsys):
    with raises(Exception) as exinfo:
        class root(ConfigRoot):
            pass

        class inner(ConfigBuilder):
            def build(self):
                raise Exception("in build")

        with root(prod2, ef2_pp_prod):
            with inner():
                raise Exception("in with")

    _sout, serr = capsys.readouterr()
    assert serr == ""
    assert str(exinfo.value) == 'in with'


def test_double_error_for_configroot_mc_required_missing(capsys):
    with raises(Exception) as exinfo:
        class root(ConfigRoot):
            def __init__(self, selected_env, env_factory):
                super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)
                self.someattr1 = MC_REQUIRED

        with root(prod1, ef1_prod):
            errorline = lineno() + 1
            raise Exception("Error in root with block")

    _sout, serr = capsys.readouterr()
    assert serr == ""
    print(exinfo.value)
    assert str(exinfo.value) == "Error in root with block"


def test_double_error_for_configroot_required_item_missing(capsys):
    with raises(Exception) as exinfo:
        @required('someitem')
        class root(ConfigRoot):
            def __init__(self, selected_env, env_factory):
                super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)

        with root(prod1, ef1_prod):
            errorline = lineno() + 1
            raise Exception("Error in root with block")

    _sout, serr = capsys.readouterr()
    assert serr == ""
    print(exinfo.value)
    assert str(exinfo.value) == "Error in root with block"
    

def test_builder_does_not_accept_nested_repeatables_decorator(capsys):
    with raises(ConfigDefinitionException) as exinfo:
        @nested_repeatables('a')
        class _inner(ConfigBuilder):
            def build(self):
                _a = 1

    _sout, serr = capsys.readouterr()
    err_msg = "File \"fake_dir/multiconf_definition_errors_test.py\", line 999\nConfigError: Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder.\n"
    assert replace_user_file_line_msg(serr) == err_msg
    assert str(exinfo.value) == "Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder."


def test_root_attribute_exception_in_with_block():
    with raises(Exception) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            raise Exception("Error in root with block")

    assert str(exinfo.value) == "Error in root with block"


def test_error_freezing_previous_sibling__build(capsys):
    class inner(ConfigBuilder):
        def build(self):
            raise Exception("Error in build")

    with raises(Exception) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod) as cr:
            errorline = lineno() + 1
            inner()
            inner()

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr) == exception_previous_object_expected_stderr % dict(
        module='multiconf_definition_errors_test', py3_local=py3_local())
    assert str(exinfo.value) == "Error in build"


def test_mc_init_override_underscore_error(capsys):
    errorline = lineno() + 3
    class X(ConfigItem):
        def mc_init(self):
            self.override("_a", "Hello")

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            X()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_a' on a config item. Atributes starting with '_' can not be set using item.override. Use assignment instead."
    assert ce(errorline, msg) == serr


def test_mc_init_override_underscore_mc_error(capsys):
    errorline = lineno() + 3
    class X(ConfigItem):
        def mc_init(self):
            self.override("_mca", "Hello")

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            X()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_mca' on a config item. Atributes starting with '_mc' are reserved for multiconf internal usage."
    assert serr == ce(errorline, msg)


def test_build_override_underscore_mc_error(capsys):
    errorline = lineno() + 3
    class B(ConfigBuilder):
        def build(self):
            self.override("_mca", "Hello")

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            B()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_mca' on a config item. Atributes starting with '_mc' are reserved for multiconf internal usage."
    assert serr == ce(errorline, msg)


def test_attribute_mc_required_args_partial_set_in_init_unfinished():
    class Requires(ConfigItem):
        def __init__(self, a=13):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('a', prod=a)
            self.setattr('b', default=17, prod=2)

        def mc_init(self):
            self.b = 7

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod) as cr:
            Requires()


def test_setattr_no_envs(capsys):
    def check(errorline):
        _sout, serr = capsys.readouterr()
        assert_lines_in(
            __file__, errorline, serr,
            "^%(lnum)s",
            "^ConfigError: No Env or EnvGroup names specified.",
            "^%(lnum)s",
            config_error_no_value_other_env_expected.format(attr='aa', env=pp2),
            config_error_no_value_current_env_expected.format(attr='aa', env=prod2),
        )

    # ConfigRoot
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa')

    check(errorline)

    with raises(Exception) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', 1)

    check(errorline)

    # ConfigItem
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            with ConfigItem() as ci:
                errorline = lineno() + 1
                ci.setattr('aa')

    check(errorline)

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            with ConfigItem() as ci:
                errorline = lineno() + 1
                ci.setattr('aa', 1)

    check(errorline)

    # RepeatableItem
    with raises(ConfigException) as exinfo:
        with project(prod2, ef2_pp_prod):
            with RepeatableItem(mc_key='a') as ci:
                errorline = lineno() + 1
                ci.setattr('aa')

    check(errorline)

    with raises(ConfigException) as exinfo:
        with project(prod2, ef2_pp_prod):
            with RepeatableItem(mc_key='a') as ci:
                errorline = lineno() + 1
                ci.setattr('aa', 1)

    check(errorline)

    # ConfigBuilder
    class B(ConfigBuilder):
        def build(self):
            pass

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            with B() as ci:
                errorline = lineno() + 1
                ci.setattr('aa')

    check(errorline)

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            with B() as ci:
                errorline = lineno() + 1
                ci.setattr('aa', 1)

    check(errorline)


def test_init_lineno(capsys):
    class init_overidden1(ConfigItem):
        def __init__(self):
            super(init_overidden1, self).__init__()
            self.a = MC_REQUIRED

    with raises(Exception) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            errorline = lineno() + 1
            init_overidden1()
            init_overidden1()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='a', env=pp2),
        config_error_mc_required_current_env_expected.format(attr='a', env=prod2),
    )

    class intermediate(init_overidden1):
        pass

    with raises(Exception) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            errorline = lineno() + 1
            intermediate()
            intermediate()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='a', env=pp2),
        config_error_mc_required_current_env_expected.format(attr='a', env=prod2),
    )

    class init_overidden2(intermediate):
        def __init__(self):
            super(init_overidden2, self).__init__()
            self.b = MC_REQUIRED

    with raises(Exception) as exinfo:
        with ConfigRoot(prod2, ef2_pp_prod):
            errorline = lineno() + 1
            init_overidden2()
            init_overidden2()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='a', env=pp2),
        config_error_mc_required_current_env_expected.format(attr='a', env=prod2),
        config_error_mc_required_other_env_expected.format(attr='b', env=pp2),
        config_error_mc_required_current_env_expected.format(attr='b', env=prod2),
    )

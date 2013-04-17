#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils import config_error, multi_file_single_config_error, lineno, replace_ids, replace_user_file_line_tuple, replace_user_file_line_msg

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException, ConfigDefinitionException
from ..decorators import nested_repeatables, repeat, required
from ..envs import EnvFactory

ef = EnvFactory()

dev2ct = ef.Env('dev2ct')
dev2st = ef.Env('dev2st')
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3ct')
dev3st = ef.Env('dev3st')
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)

oops = ef.Env('declared_not_valid_env')
g_oops = ef.EnvGroup('declared_not_valid_group', prod, oops)

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def mfsce_local(msg, line_num, *line_msgs):
    lines_info = [(__file__, line_num, line_msg) for line_msg in line_msgs]
    return multi_file_single_config_error(msg, *lines_info)


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


_o_expected = """A value is already specified for: Env('dev2ct') from group EnvGroup('g_dev_overlap') {
     Env('dev2ct')
}=(3, ('fake_dir/multiconf_definition_errors_test.py', 999)), previous value: EnvGroup('g_dev2') {
     Env('dev2ct'),
     Env('dev2st')
}=(2, ('fake_dir/multiconf_definition_errors_test.py', 999))"""

_o_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 1
}"""


_p_expected = """A value is already specified for: Env('dev2ct') from group EnvGroup('g_dev_overlap') {
     Env('dev2ct'),
     Env('dev3ct')
}=(3, ('fake_dir/multiconf_definition_errors_test.py', 999)), previous value: EnvGroup('g_dev2') {
     Env('dev2ct'),
     Env('dev2st')
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


@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass


@repeat()
class RepeatableItem(ConfigItem):
    pass



def test_non_env_for_instantiatiation_env():
    with raises(ConfigException) as exinfo:
        project('Why?', [prod])

    assert exinfo.value.message == "project: env must be instance of 'Env'; found type 'str': 'Why?'"


def test_non_env_in_valid_envs():
    with raises(ConfigException) as exinfo:
        project(prod, [prod, 'Why?'])

    assert exinfo.value.message == "project: valid_envs items must be instance of 'Env' or 'EnvGroup'; found a 'str': 'Why?'"


def test_valid_envs_is_not_a_sequence(capsys):
    with raises(ConfigException) as exinfo:
        project(prod, 1)

    assert exinfo.value.message == "project: valid_envs arg must be a 'Sequence'; found type 'int': 1"


def test_valid_envs_is_a_str(capsys):
    with raises(ConfigException) as exinfo:
        project(prod, 'Why?')

    assert exinfo.value.message == "project: valid_envs arg must be a 'Sequence'; found type 'str': 'Why?'"


_test_valid_envs_arg_as_envgroup_exp = """ConfigRoot: valid_envs arg must be a 'Sequence'; found type 'EnvGroup': EnvGroup('g_all') {
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

def test_valid_envs_arg_as_envgroup(capsys):
    with raises(ConfigException) as exinfo:
        ConfigRoot(prod, valid_envs)

    assert exinfo.value.message == _test_valid_envs_arg_as_envgroup_exp


def test_selected_conf_not_in_valid_envs(capsys):
    with raises(ConfigException) as exinfo:
        ConfigRoot(prod, [dev3ct, dev3st])

    assert exinfo.value.message == """The env Env('prod') must be in the (nested) list of valid_envs [Env('dev3ct'), Env('dev3st')]"""


def test_assign_to_undefine_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', pros="hello", prod="hi")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "No such Env or EnvGroup: 'pros'")
    assert replace_ids(exinfo.value.message, False) == _e_expected


def test_value_not_assigned_to_all_envs(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Attribute: 'a' did not receive a value for env Env('pp')")
    assert replace_ids(exinfo.value.message, False) == _f_expected


_test_attribute_defined_with_different_types_expected = "ConfigError: Found different value types for property 'a' for different envs"
_test_attribute_defined_with_different_types_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 1
}"""

def test_attribute_defined_with_different_types(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=1, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == mfsce_local(_test_attribute_defined_with_different_types_expected, errorline, "prod <type 'int'>", "pp <type 'str'>")
    assert replace_ids(exinfo.value.message, False) == _test_attribute_defined_with_different_types_expected_ex


def test_attribute_redefinition_attempt(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod]) as cr:
            cr.setattr('a', prod=1)
            errorline = lineno() + 1
            cr.setattr('a', prod=2)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _h_expected)
    assert replace_ids(exinfo.value.message, named_as=False) == _h_expected_ex


def test_nested_item_overrides_simple_attribute(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod]) as cr:
            cr.setattr('ConfigItem', prod="hello")
            ConfigItem()

    assert replace_ids(exinfo.value.message, named_as=False) == _i_expected


def test_nested_repeatable_item_not_defined_as_repeatable_in_contained_in_class(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod]) as cr:
            RepeatableItem()

    assert replace_ids(exinfo.value.message, named_as=False) == _j_expected


def test_nested_repeatable_item_overrides_simple_attribute_not_contained_in_repeatable(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod]) as cr:
            # cr.RepeatableItems is just an attribute named like an item
            cr.setattr('RepeatableItems', prod="hello")
            RepeatableItem()

    assert replace_ids(exinfo.value.message, named_as=False) == _k1_expected


def test_nested_repeatable_item_shadowed_by_default_attribute(capsys):
    with raises(ConfigException) as exinfo:
        # RepeatableItems is just an attribute named like an item
        with project(prod, [prod], RepeatableItems=1) as cr:
            RepeatableItem()

    assert replace_ids(exinfo.value.message, named_as=False) == "'RepeatableItems' defined as default value shadows a nested-repeatable"


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
#         with root(prod, [prod]) as cr:
# TODO: 'cr' is an OrderedDict, so this call is not possible, which is fine, but the error message is not good
#             cr.children(prod="hello")
#             rchild()
#     assert exinfo.value.message == "'children' is defined both as simple value and a contained item: children {\n}"


def test_non_repeatable_but_container_expects_repeatable(capsys):
    with raises(ConfigException) as exinfo:
        # The following class in not repeatable!
        class RepeatableItems(ConfigItem):
            pass

        with project(prod, [prod]) as cr:
            RepeatableItems()

    assert replace_ids(exinfo.value.message, named_as=False) == _k4_expected


def test_simple_attribute_attempt_to_override_contained_item(capsys):
    with raises(TypeError) as exinfo:
        with ConfigRoot(prod, [prod]) as cr:
            ConfigItem()
            errorline = lineno() + 1
            cr.ConfigItem(prod="hello")

    assert exinfo.value.message == "'ConfigItem' object is not callable"


def test_repeated_non_repeatable_item(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod]) as cr:
            ConfigItem()
            errorline = lineno() + 1
            ConfigItem()

    assert exinfo.value.message == "Repeated non repeatable conf item: 'ConfigItem'"


def test_nested_repeatable_items_with_repeated_name(capsys):
    with raises(ConfigException) as exinfo:
        with project(prod, [prod]) as cr:
            RepeatableItem(id='my_name')
            RepeatableItem(id='my_name')

    assert exinfo.value.message == "Re-used id/name 'my_name' in nested objects"


def test_value_defined_through_multiple_groups(capsys):
    with raises(ConfigException) as exinfo:
        g_dev_overlap = ef.EnvGroup('g_dev_overlap', dev2ct)

        with ConfigRoot(prod, [prod, g_dev2, g_dev_overlap]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=1, g_dev2=2, g_dev_overlap=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_tuple(serr) == ce(errorline, _o_expected)
    assert replace_ids(exinfo.value.message, False) == _o_expected_ex


def test_value_defined_through_multiple_groups2(capsys):
    with raises(ConfigException) as exinfo:
        g_dev_overlap = ef.EnvGroup('g_dev_overlap', dev2ct, dev3ct)

        with ConfigRoot(prod, [prod, g_dev2, g_dev_overlap]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=1, g_dev2=2, g_dev_overlap=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_tuple(serr) == ce(errorline, _p_expected)
    assert replace_ids(exinfo.value.message, False) == _p_expected_ex


def test_assigning_owerwrites_attribute_root(capsys):
    with raises(ConfigException) as exinfo:
        with project(prod, [prod]) as cr:
            cr.setattr('a', prod=1)
            errorline = lineno() + 1
            cr.a = 2

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _r_expected)
    assert replace_ids(exinfo.value.message, named_as=False) == _r1_expected_ex


def test_assigning_owerwrites_attribute_nested_item(capsys):
    with raises(ConfigException) as exinfo:
        with project(prod, [prod]) as cr:
            with ConfigItem() as ci:
                ci.setattr('a', prod=1)
                errorline = lineno() + 1
                ci.a = 1

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _r_expected)
    assert replace_ids(exinfo.value.message, named_as=False) == _r2_expected_ex


def test_configitem_outside_of_root(capsys):
    with raises(ConfigException) as exinfo:
        ConfigItem()

    assert exinfo.value.message == "ConfigItem object must be nested (indirectly) in a 'ConfigRoot'"


_group_for_selected_env_expected = """project: env must be instance of 'Env'; found type 'EnvGroup': EnvGroup('g_dev3') {
     Env('dev3ct'),
     Env('dev3st')
}"""

def test_using_group_for_selected_env(capsys):
    with raises(ConfigException) as exinfo:
        project(g_dev3, [g_dev3])

    assert exinfo.value.message == _group_for_selected_env_expected


_test_exception_in___exit___and_build = """Exception in __exit__: Exception('in build',)
Exception in with block will be raised
"""

def test_exception_in___exit___must_print_ex_info_and_raise_original_exception_if_any_pending_builder(capsys):
    with raises(Exception) as exinfo:
        class root(ConfigRoot):
            pass

        class inner(ConfigBuilder):
            def build(self):
                raise Exception("in build")

        with root(prod, [prod, pp], a=0):
            with inner(id='n1', b=1):
                raise Exception("in with")

    _sout, serr = capsys.readouterr()
    assert serr == _test_exception_in___exit___and_build
    assert exinfo.value.message == 'in with'


_test_double_error_for_configroot_expected_stderr = """Exception in __exit__: ConfigException("No value given for required attributes: ['someattr1', 'someattr2']",)
Exception in with block will be raised
"""

def test_double_error_for_configroot(capsys):
    with raises(Exception) as exinfo:
        @required('someattr1, someattr2')
        class root(ConfigRoot):
            pass

        with root(prod, [prod]):
            raise Exception("Error in root with block")

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr) == _test_double_error_for_configroot_expected_stderr
    assert exinfo.value.message == "Error in root with block"


def test_builder_does_not_accept_nested_repeatables_decorator(capsys):
    with raises(ConfigDefinitionException) as exinfo:
        @nested_repeatables('a')
        class _inner(ConfigBuilder):
            def build(self):
                _a = 1

    _sout, serr = capsys.readouterr()
    err_msg = "File \"fake_dir/multiconf_definition_errors_test.py\", line 999\nConfigError: Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder.\n"
    assert replace_user_file_line_msg(serr) == err_msg
    assert exinfo.value.message == "Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder."


def test_root_attribute_exception_in_with_block():
    with raises(Exception) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            raise Exception("Error in root with block")

    assert exinfo.value.message == "Error in root with block"


_exception_previous_object_expected_stderr = """Exception validating previously defined object -
  type: <class 'multiconf.test.multiconf_definition_errors_test.inner'>
Stack trace will be misleading!
This happens if there is an error (e.g. missing required attributes) in an object that was not
directly enclosed in a with statement. Objects that are not arguments to a with statement will
not be validated until the next ConfigItem is declared or an outer with statement is exited.
"""

def test_error_freezing_previous_sibling__build(capsys):
    class inner(ConfigBuilder):
        def build(self):
            raise Exception("Error in build")

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            inner()
            # It would be nice if errorline would be previous line, but that is not really possible
            errorline = lineno() + 1
            inner()

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr) == _exception_previous_object_expected_stderr
    assert exinfo.value.message == "Error in build"


def test_error_freezing_previous_sibling__validation(capsys):
    @required('a')
    class inner(ConfigItem):
        pass

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            inner()
            # It would be nice if errorline would be previous line, but that is not really possible
            errorline = lineno() + 1
            inner()

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr) == _exception_previous_object_expected_stderr
    assert exinfo.value.message == "No value given for required attributes: ['a']"


def test_setattr_ref_declared_not_valid_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, valid_envs=[prod]):
            with ConfigItem() as it:
                it.setattr('a', declared_not_valid_env=1)

    assert exinfo.value.message ==  """The env Env('declared_not_valid_env') must be in the (nested) list of valid_envs [Env('prod')]"""


def test_setattr_ref_declared_not_valid_group(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, valid_envs=[prod]):
            with ConfigItem() as it:
                it.setattr('a', declared_not_valid_group=1)

    # TODO: Improve error message
    assert exinfo.value.message ==  """The env Env('declared_not_valid_env') must be in the (nested) list of valid_envs [Env('prod')]"""

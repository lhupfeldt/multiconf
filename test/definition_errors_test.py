# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises, xfail

from .utils.utils import config_error, next_line_num, replace_ids, replace_user_file_line_msg, assert_lines_in, py3_local, total_msg, start_file_line
from .utils.messages import already_printed_msg, exception_previous_object_expected_stderr
from .utils.messages import mc_required_expected, config_error_mc_required_expected
from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException, ConfigDefinitionException, MC_REQUIRED
from multiconf.decorators import nested_repeatables, required
from multiconf.envs import EnvFactory


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


_single_error_on_item_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "%s"
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
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg


@nested_repeatables('RepeatableItems')
class project(ConfigItem):
    pass


class RepeatableItem(RepeatableConfigItem):
    pass


def test_non_env_for_instantiatiation_env():
    @mc_config(ef1_prod)
    def _(_):
        pass

    with raises(ConfigException) as exinfo:
        ef1_prod.config('Why?')

    assert str(exinfo.value) == "EnvFactory: env must be instance of 'Env'; found type 'str': 'Why?'"


def test_env_factory_is_not_an_env_factory():
    with raises(ConfigException) as exinfo:
        @mc_config(1)
        def _(_):
            pass

    assert str(exinfo.value) == "'env_factory' arg must be instance of 'EnvFactory'; found type 'int': 1"


_env_factory_arg_as_envgroup_exp = """'env_factory' arg must be instance of 'EnvFactory'; found type 'EnvGroup': EnvGroup('g_all') {
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
        @mc_config(g_all3)
        def _(_):
            pass

    print(str(exinfo.value))
    assert str(exinfo.value) == _env_factory_arg_as_envgroup_exp


def test_selected_conf_not_from_env_factory():
    another_ef = EnvFactory()
    @mc_config(ef2_pp_prod)
    def _(_):
        pass

    with raises(ConfigException) as exinfo:
        print(another_ef.config(prod3))

    assert str(exinfo.value) == """The selected env Env('prod') must be from the 'env_factory' specified for 'mc_config'."""


def test_mc_config_empty_env_factory():
    empty_ef = EnvFactory()

    with raises(ConfigException) as exinfo:
        @mc_config(empty_ef)
        def _(_):
            pass

    assert str(exinfo.value) == """The specified 'env_factory' is empty. It must have at least one Env."""


def test_assign_to_undefine_env(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', pros="hello", default="hi")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], "No such Env or EnvGroup: 'pros'")
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex % ('pp', '"hi"')


def test_value_not_assigned_to_all_envs(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], mc_required_expected.format(attr='aa', env=pp2))
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex % ('pp', '"MC_REQUIRED"')


_fully_defined = "The attribute 'aa' is already fully defined."

def test_attribute_redefinition_attempt1(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA(aa=0) as cr:
                cr.setattr('aa', prod=1)
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=2)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('prod', 1)

def test_attribute_redefinition_attempt2(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA() as cr:
                cr.setattr('aa', pp=1, prod=3)
                errorline[0] = next_line_num()
                cr.setattr('aa', pp=2, prod=4)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('pp', 1)


def test_attribute_redefinition_attempt3(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA(aa=0) as cr:
                cr.setattr('aa', pp=1)
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=2)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('pp', 1)


def test_attribute_redefinition_attempt4(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA(aa=0) as cr:
                cr.setattr('aa', prod=1)
                errorline[0] = next_line_num()
                cr.setattr('aa', pp=2)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('prod', 1)


def test_attribute_redefinition_attempt5(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA() as cr:
                cr.setattr('aa', pp=1)
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=2)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('pp', 1)


_nested_repeatable_item_not_defined_as_repeatable_in_contained_in_class_expected_ex = """'RepeatableItems': <class 'test.definition_errors_test.RepeatableItem'> is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigItem'"""

def test_nested_repeatable_item_not_defined_as_repeatable_in_contained_in_class():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ConfigItem() as cr:
                RepeatableItem(mc_key=None)

    assert replace_ids(str(exinfo.value), named_as=False) == _nested_repeatable_item_not_defined_as_repeatable_in_contained_in_class_expected_ex


_non_repeatable_but_container_expects_repeatable_expected = """'RepeatableItems': <class 'test.definition_errors_test.%(py3_local)sRepeatableItems'> is not defined as repeatable, but this is defined as a repeatable item in the containing class: {
    "__class__": "project #as: 'project', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "RepeatableItems": {}
}"""

def test_non_repeatable_but_container_expects_repeatable():
    # The following class in not repeatable!
    class RepeatableItems(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with project():
                RepeatableItems()

    assert replace_ids(str(exinfo.value), named_as=False) == _non_repeatable_but_container_expects_repeatable_expected % dict(py3_local=py3_local())


def test_attempt_to_call_contained_item():
    with raises(TypeError) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ConfigItem() as cr:
                ConfigItem()
                cr.ConfigItem(prod="hello")

    assert str(exinfo.value) == "'ConfigItem' object is not callable"


def test_repeated_non_repeatable_item():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ConfigItem() as cr:
                ConfigItem()
                ConfigItem()

    assert str(exinfo.value) == "Repeated non repeatable conf item: 'ConfigItem': <class 'multiconf.multiconf.ConfigItem'>"


def test_nested_repeatable_items_with_repeated_mc_key():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with project():
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
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg

def test_value_defined_through_two_groups(capsys):
    xfail("duplicate?")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        with ItemWithAA(prod3, ef3_dev_prod) as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', default=7, prod=1, g_dev2=2, g_dev_overlap=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline[0]) == _value_defined_through_two_groups_expected % dict(line=errorline[0])
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
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg

def test_value_defined_through_three_groups(capsys):
    xfail("duplicate?")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        with ItemWithAA(prod5, ef5_dev_prod) as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', g_dev_overlap2=7, default=7, prod=1, g_dev2=2, g_dev_overlap1=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline[0]) == _value_defined_through_three_groups_expected % dict(line=errorline[0])
    assert replace_ids(str(exinfo.value), False) == _value_defined_through_three_groups_expected_ex


def test_two_values_defined_through_two_groups(capsys):
    xfail("duplicate?")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        with ItemWithAA(prod4, ef4_dev_prod) as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=1, dev3st=14, pp=33, g_dev2=2, g_dev3=12, g_dev_overlap=3)

    _sout, serr = capsys.readouterr()
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline[0]) == _p_expected.strip() % dict(line=errorline[0])
    assert replace_ids(str(exinfo.value), False) == _p_expected_ex


_assigning_owerwrites_attribute_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1
}""" + already_printed_msg


def test_assigning_owerwrites_attribute(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ItemWithAA() as cr:
                cr.setattr('aa', prod=1)
                errorline[0] = next_line_num()
                cr.aa = 2

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _fully_defined)
    assert replace_ids(str(exinfo.value), named_as=False) == _assigning_owerwrites_attribute_expected_ex


def test_configitem_outside_of_root():
    xfail("TODO ConfigItem outside mc_config?")
    with raises(ConfigException) as exinfo:
        ConfigItem()

    assert str(exinfo.value) == "ConfigItem object must be nested (indirectly) in a 'ConfigItem'"


_group_for_selected_env_expected = """EnvFactory: env must be instance of 'Env'; found type 'EnvGroup': EnvGroup('g_dev3') {
   Env('dev3ct'),
   Env('dev3st')
}"""

def test_using_group_for_selected_env():
    @mc_config(ef3_dev_prod)
    def _(_):
        project()

    with raises(ConfigException) as exinfo:
        ef3_dev_prod.config(g_dev33)

    assert str(exinfo.value) == _group_for_selected_env_expected


def test_double_error_for_configroot_mc_required_missing(capsys):
    class root(ConfigItem):
        def __init__(self):
            super(root, self).__init__()
            self.someattr1 = MC_REQUIRED

    with raises(Exception) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with root():
                raise Exception("Error in root with block")

    _sout, serr = capsys.readouterr()
    assert serr == ""
    print(exinfo.value)
    assert str(exinfo.value) == "Error in root with block"


def test_double_error_for_configroot_required_item_missing(capsys):
    @required('someitem')
    class root(ConfigItem):
        def __init__(self):
            super(root, self).__init__()

    with raises(Exception) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with root():
                raise Exception("Error in root with block")

    _sout, serr = capsys.readouterr()
    assert serr == ""
    print(exinfo.value)
    assert str(exinfo.value) == "Error in root with block"


def test_root_attribute_exception_in_with_block():
    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem():
                raise Exception("Error in root with block")

    assert str(exinfo.value) == "Error in root with block"


def test_mc_init_override_underscore_error(capsys):
    errorline = [None]

    class X(ConfigItem):
        def mc_init(self):
            errorline[0] = next_line_num()
            self.setattr("_a", default="Hello", mc_force=True)

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem():
                X()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_a' on a config item. Atributes starting with '_' cannot be set using item.setattr. Use assignment instead."
    assert ce(errorline[0], msg) == serr


def test_mc_init_override_underscore_mc_error(capsys):
    errorline = [None]

    class X(ConfigItem):
        def mc_init(self):
            errorline[0] = next_line_num()
            self.setattr("_mca", default="Hello", mc_force=True)

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem():
                X()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_mca' on a config item. Atributes starting with '_mc' are reserved for multiconf internal usage."
    assert serr == ce(errorline[0], msg)


_attribute_mc_required_args_partial_set_in_init_unfinished_expected_ex = """There was 1 error when defining item: {
    "__class__": "Requires #as: 'Requires', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "a #no value for current env": true,
    "b": 17
}""" + already_printed_msg


def test_attribute_mc_required_args_partial_set_in_init_unfinished(capsys):
    errorline_setattr = [None]
    errorline_exit_check = [None]

    class Requires(ConfigItem):
        def __init__(self, a=13):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            errorline_setattr[0] = next_line_num()
            self.setattr('a', prod=a)
            self.setattr('b', default=17, prod=2)

        def mc_init(self):
            self.b = 7

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem() as cr:
                errorline_exit_check[0] = next_line_num()
                Requires()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        serr,
        start_file_line(__file__, errorline_exit_check[0]),
        "^ConfigError: The following attribues defined earlier never received a proper value for Env('pp'):",
        '^File "{file}", line {line}'.format(file=__file__, line=errorline_setattr[0]),
        "^ConfigError: Attribute: 'a' did not receive a value for env Env('pp')",
    )

    assert replace_ids(str(exinfo.value), named_as=False) == _attribute_mc_required_args_partial_set_in_init_unfinished_expected_ex


def test_setattr_no_envs(capsys):
    errorline = [None]

    def check(errorline):
        _sout, serr = capsys.readouterr()
        assert_lines_in(
            serr,
            start_file_line(__file__, errorline),
            "^ConfigError: No Env or EnvGroup names specified.",
            # TODO, should we expect multiple errors here?
            # start_file_line(__file__, errorline[0]),
            # config_error_mc_required_expected.format(attr='aa', env=prod2),
        )

    # ConfigItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa')

    check(errorline[0])

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', 1)

    check(errorline[0])

    # RepeatableItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with project():
                with RepeatableItemWithAA(mc_key='a') as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa')

    check(errorline[0])

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with project():
                with RepeatableItemWithAA(mc_key='a') as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa', 1)

    check(errorline[0])


def test_setattr_no_envs_set_unknown(capsys):
    errorline = [None]

    def check(errorline):
        _sout, serr = capsys.readouterr()
        assert_lines_in(
            serr,
            start_file_line(__file__, errorline),
            "^ConfigError: No Env or EnvGroup names specified.",
            # TODO, should we expect multiple errors here?
            # start_file_line(__file__, errorline[0]),
            # config_error_mc_required_expected.format(attr='aa', env=prod2),
        )

    # ConfigItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', mc_set_unknown=True)

    check(errorline[0])

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', 1, mc_set_unknown=True)

    check(errorline[0])

    # RepeatableItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with project():
                with RepeatableItem(mc_key='a') as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa', mc_set_unknown=True)

    check(errorline[0])

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with project():
                with RepeatableItem(mc_key='a') as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa?', 1, mc_set_unknown=True)

    check(errorline[0])


def test_init_line_num(capsys):
    xfail("TODO: init linenumber?")
    errorline = [None]

    class init_overidden1(ConfigItem):
        def __init__(self):
            super(init_overidden1, self).__init__()
            self.a = MC_REQUIRED

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem():
                errorline[0] = next_line_num()
                init_overidden1()
                init_overidden1()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='a', env=prod2),
    )

    class intermediate(init_overidden1):
        pass

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem(prod2, ef2_pp_prod):
                errorline[0] = next_line_num()
                intermediate()
                intermediate()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='a', env=prod2),
    )

    class init_overidden2(intermediate):
        def __init__(self):
            super(init_overidden2, self).__init__()
            self.b = MC_REQUIRED

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem(prod2, ef2_pp_prod):
                errorline[0] = next_line_num()
                init_overidden2()
                init_overidden2()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='a', env=prod2),
        config_error_mc_required_expected.format(attr='b', env=prod2),
    )
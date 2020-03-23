# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises, xfail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException, MC_REQUIRED
from multiconf.decorators import nested_repeatables, required
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num, replace_ids, lines_in, local_func, start_file_line, file_line
from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA
from .utils.messages import already_printed_msg, mc_required_expected, config_error_mc_required_expected, not_repeatable_in_parent_msg
from .utils.messages import config_error_never_received_value_expected


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


@nested_repeatables('RepeatableItems')
class project(ConfigItem):
    pass


class RepeatableItem(RepeatableConfigItem):
    pass


def test_non_env_for_instantiatiation_env():
    @mc_config(ef1_prod, load_now=True)
    def config(_):
        pass

    with raises(ConfigException) as exinfo:
        config('Why?')

    assert str(exinfo.value) == "EnvFactory: env must be instance of 'Env'; found type 'str': 'Why?'"


def test_env_factory_is_not_an_env_factory():
    with raises(ConfigException) as exinfo:
        @mc_config(1, load_now=True)
        def config(_):
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
        def config(_):
            pass

    print(str(exinfo.value))
    assert str(exinfo.value) == _env_factory_arg_as_envgroup_exp


def test_selected_conf_not_from_env_factory():
    another_ef = EnvFactory()
    another_env = another_ef.Env('another_env')

    @mc_config(ef2_pp_prod)
    def config(_):
        pass

    with raises(ConfigException) as exinfo:
        print(config(another_env))

    assert str(exinfo.value) == """The selected env Env('another_env') must be from the 'env_factory' specified for 'mc_config'."""


def test_mc_config_empty_env_factory():
    empty_ef = EnvFactory()

    with raises(ConfigException) as exinfo:
        @mc_config(empty_ef)
        def config(_):
            pass

    assert str(exinfo.value) == """The specified 'env_factory' is empty. It must have at least one Env."""


def test_assign_to_undefine_env(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', pros="hello", default="hi")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], "No such Env or EnvGroup: 'pros'")
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex % ('pp', '"hi"')


def test_assign_to_multiple_undefine_envs(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', pros="hello", peculiar="hej", default="hi")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], "No such Envs or EnvGroups: ['pros', 'peculiar']")
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex % ('pp', '"hi"')


def test_value_not_assigned_to_all_envs(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                cr.setattr('aa', pp=1)
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=2)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('pp', 1)


_single_error_on_item_with_bb_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": 1,
    "bb": 1
}""" + already_printed_msg

def test_setattr_after_getattr(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithAA(1) as cr:
                # Use the default value of aa when setting bb
                cr.setattr('bb', pp=cr.aa, mc_set_unknown=True)
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=2)  # Attempt to override the default value of aa after use

    _sout, serr = capsys.readouterr()
    print(serr)
    exp = "Trying to set attribute 'aa'. Setting attributes is not allowed after value has been used (in order to enforce derived value validity)."
    assert serr.startswith(ce(errorline[0], exp))
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_with_bb_expected_ex


_setattr_after_item_frozen_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": 1
}""" + already_printed_msg

def test_setattr_after_item_frozen(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithAA(1) as cr:
                pass

            errorline[0] = next_line_num()
            cr.setattr('aa', prod=2)  # Attempt to override the default value of aa after item is frozen (with scope is exited)

    _sout, serr = capsys.readouterr()
    exp = "Trying to set attribute 'aa'. Setting attributes is not allowed after item is 'frozen' (with 'scope' is exited)."
    assert serr.startswith(ce(errorline[0], exp))
    assert replace_ids(str(exinfo.value), named_as=False) == _setattr_after_item_frozen_expected_ex


def test_nested_repeatable_item_not_defined_as_repeatable_in_contained_in_class():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                RepeatableItem(mc_key=None)

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='RepeatableItems', repeatable_cls="<class 'test.definition_errors_test.RepeatableItem'>",
        ci_named_as='ConfigItem', ci_cls="<class 'multiconf.multiconf.ConfigItem'>")
    assert replace_ids(str(exinfo.value), named_as=False) == exp


_non_repeatable_but_container_expects_repeatable_expected = """'RepeatableItems': <class 'test.definition_errors_test.%(local_func)sRepeatableItems'> is not defined as repeatable, but this is defined as a repeatable item in the containing class: {
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
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with project():
                RepeatableItems()

    assert replace_ids(str(exinfo.value), named_as=False) == _non_repeatable_but_container_expects_repeatable_expected % dict(local_func=local_func())


def test_attempt_to_call_contained_item():
    with raises(TypeError) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                ConfigItem()
                cr.ConfigItem(prod="hello")

    assert str(exinfo.value) == "'ConfigItem' object is not callable"


def test_repeated_non_repeatable_item():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                ConfigItem()
                ConfigItem()

    assert str(exinfo.value) == "Repeated non repeatable conf item: 'ConfigItem': <class 'multiconf.multiconf.ConfigItem'>"


_nested_repeatable_items_with_repeated_mc_key_expected_ex = """Re-used key 'my_name' in repeated item <class 'test.definition_errors_test.RepeatableItem'> overwrites existing entry in parent:
{
    "__class__": "project #as: 'project', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "RepeatableItems": {
        "my_name": {
            "__class__": "RepeatableItem #as: 'RepeatableItems', id: 0000, not-frozen"
        }
    }
}"""

def test_nested_repeatable_items_with_repeated_mc_key():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with project():
                RepeatableItem(mc_key='my_name')
                RepeatableItem(mc_key='my_name')

    print(exinfo.value)
    assert replace_ids(str(exinfo.value), False) == _nested_repeatable_items_with_repeated_mc_key_expected_ex


_value_defined_through_two_groups_expected = """
ConfigError: Value for Env('dev2ct') is specified more than once, with no single most specific group or direct env:
value: 2, from: EnvGroup('g_dev2') {
   Env('dev2ct'),
   Env('dev2st')
}
value: 3, from: EnvGroup('g_dev_overlap') {
   Env('dev2ct')
}"""

_value_defined_through_two_groups_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "dev2ct"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg

def test_value_defined_through_two_groups(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef3_dev_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', default=7, prod=1, g_dev2=2, g_dev_overlap=3)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(file_line(__file__, errorline[0]))
    assert _value_defined_through_two_groups_expected in serr
    assert replace_ids(str(exinfo.value), False) == _value_defined_through_two_groups_expected_ex


_value_defined_through_three_groups_expected = """
ConfigError: Value for Env('dev2ct') is specified more than once, with no single most specific group or direct env:
value: 2, from: EnvGroup('g_dev2') {
   Env('dev2ct'),
   Env('dev2st')
}
value: 3, from: EnvGroup('g_dev_overlap1') {
   Env('dev2ct')
}
value: 7, from: EnvGroup('g_dev_overlap2') {
   Env('dev2ct')
}""".strip()

_value_defined_through_three_groups_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "dev2ct"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg

def test_value_defined_through_three_groups(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef5_dev_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', g_dev_overlap2=7, default=7, prod=1, g_dev2=2, g_dev_overlap1=3)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(file_line(__file__, errorline[0]))
    assert _value_defined_through_three_groups_expected in serr
    assert replace_ids(str(exinfo.value), False) == _value_defined_through_three_groups_expected_ex


_two_values_defined_through_two_groups_expected1 = """
ConfigError: Value for Env('dev2ct') is specified more than once, with no single most specific group or direct env:
value: 2, from: EnvGroup('g_dev2') {
   Env('dev2ct'),
   Env('dev2st')
}
value: 3, from: EnvGroup('g_dev_overlap') {
   Env('dev2ct'),
   Env('dev3ct')
}"""


_two_values_defined_through_two_groups_expected2 = """
ConfigError: Value for Env('dev3ct') is specified more than once, with no single most specific group or direct env:
value: 12, from: EnvGroup('g_dev3') {
   Env('dev3ct'),
   Env('dev3st')
}
value: 3, from: EnvGroup('g_dev_overlap') {
   Env('dev2ct'),
   Env('dev3ct')
}"""

def test_two_values_defined_through_two_groups(capsys):
    errorline = [None]

    @mc_config(ef4_dev_prod)
    def config(_):
        with ItemWithAA() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=1, dev3st=14, pp=33, g_dev2=2, g_dev3=12, g_dev_overlap=3)

    with raises(ConfigException) as exinfo:
        config.load(error_next_env=True)

    _sout, serr = capsys.readouterr()
    assert serr.startswith(file_line(__file__, errorline[0]))
    assert _two_values_defined_through_two_groups_expected1 in serr
    assert _two_values_defined_through_two_groups_expected2 in serr
    assert replace_ids(str(exinfo.value), False) == "The following envs had errors [Env('dev2ct'), Env('dev3ct')]"


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
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                cr.setattr('aa', prod=1)
                errorline[0] = next_line_num()
                cr.aa = 2

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _fully_defined)
    assert replace_ids(str(exinfo.value), named_as=False) == _assigning_owerwrites_attribute_expected_ex


def test_configitem_outside_of_mc_config():
    # TODO: Explicitly check for this?

    # Need to make sure that the static _mc_hierarchy is set corectly
    del ConfigItem._mc_hierarchy[:]

    with raises(Exception) as exinfo:
        ConfigItem()

    xfail('TODO?')
    assert str(exinfo.value) == "ConfigItem object must be nested (indirectly) in a 'ConfigItem'"


_group_for_selected_env_expected = """EnvFactory: env must be instance of 'Env'; found type 'EnvGroup': EnvGroup('g_dev3') {
   Env('dev3ct'),
   Env('dev3st')
}"""

def test_using_group_for_selected_env():
    @mc_config(ef3_dev_prod)
    def config(_):
        project()

    with raises(ConfigException) as exinfo:
        config(g_dev33)

    assert str(exinfo.value) == _group_for_selected_env_expected


def test_double_error_for_configroot_mc_required_missing(capsys):
    class root(ConfigItem):
        def __init__(self):
            super().__init__()
            self.someattr1 = MC_REQUIRED

    with raises(Exception) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
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
            super().__init__()

    with raises(Exception) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with root():
                raise Exception("Error in root with block")

    _sout, serr = capsys.readouterr()
    assert serr == ""
    print(exinfo.value)
    assert str(exinfo.value) == "Error in root with block"


def test_root_attribute_exception_in_with_block():
    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
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
    "a #no value for Env('pp')": true,
    "b": 17
}""" + already_printed_msg


def test_attribute_mc_required_args_partial_set_in_init_unfinished(capsys):
    errorline_setattr = [None]
    errorline_exit_check = [None]

    class Requires(ConfigItem):
        def __init__(self, a=13):
            super().__init__()
            # Partial assignment is allowed in init
            errorline_setattr[0] = next_line_num()
            self.setattr('a', prod=a)
            self.setattr('b', default=17, prod=2)

        def mc_init(self):
            self.b = 7

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                errorline_exit_check[0] = next_line_num()
                Requires()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline_exit_check[0]),
        config_error_never_received_value_expected.format(env=pp2),
        '^File "{file}", line {line}'.format(file=__file__, line=errorline_setattr[0]),
        "^ConfigError: Attribute: 'a' did not receive a value for env Env('pp')",
    )

    assert replace_ids(str(exinfo.value), named_as=False) == _attribute_mc_required_args_partial_set_in_init_unfinished_expected_ex


def _check_no_env(errorline, capsys):
    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline),
        "^ConfigError: No Env or EnvGroup names specified.",
        # TODO, should we expect multiple errors here?
        # start_file_line(__file__, errorline[0]),
        # config_error_mc_required_expected.format(attr='aa', env=prod2),
    )


def test_setattr_no_envs(capsys):
    errorline = [None]

    # ConfigItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa')

    _check_no_env(errorline[0], capsys)

    # RepeatableItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with project():
                with RepeatableItemWithAA(mc_key='a') as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa')

    _check_no_env(errorline[0], capsys)


def test_setattr_no_envs_set_unknown(capsys):
    errorline = [None]

    # ConfigItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config0(_):
            with ConfigItem() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', mc_set_unknown=True)

    _check_no_env(errorline[0], capsys)

    # RepeatableItem
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config2(_):
            with project():
                with RepeatableItem(mc_key='a') as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa', mc_set_unknown=True)

    _check_no_env(errorline[0], capsys)


def test_setattr_mc_keyword_call_only(capsys):
    errorline = [None]

    # ConfigItem
    with raises(TypeError) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', 1, default=2, prod=3)

    assert "setattr() takes 2 positional arguments but 3 were given" in str(exinfo.value)

    # RepeatableItem
    with raises(TypeError) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config3(_):
            with project():
                with RepeatableItem(mc_key='a') as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa', 1, mc_set_unknown=True, default=2, prod=3)

    assert "setattr() takes 2 positional arguments but 3" in str(exinfo.value)


def test_init_line_num(capsys):
    xfail("TODO: init linenumber?")
    errorline = [None]

    class init_overidden1(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = MC_REQUIRED

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config1(_):
            with ConfigItem():
                errorline[0] = next_line_num()
                init_overidden1()
                init_overidden1()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='a', env=prod2),
    )

    class intermediate(init_overidden1):
        pass

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config2(_):
            with ConfigItem(prod2, ef2_pp_prod):
                errorline[0] = next_line_num()
                intermediate()
                intermediate()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='a', env=prod2),
    )

    class init_overidden2(intermediate):
        def __init__(self):
            super().__init__()
            self.b = MC_REQUIRED

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config3(_):
            with ConfigItem(prod2, ef2_pp_prod):
                errorline[0] = next_line_num()
                init_overidden2()
                init_overidden2()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='a', env=prod2),
        config_error_mc_required_expected.format(attr='b', env=prod2),
    )


def test_mc_init_redefine_item_errors_more_specific_env(capsys):
    errorline = [None]

    class X(ConfigItem):
        def mc_init(self):
            with ItemWithAA() as aai:
                aai.setattr('aa', prod=1)
                errorline[0] = next_line_num()
                aai.setattr('aa', default=2)

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config0(_):
            with X() as x:
                ItemWithAA(aa=7)

    _sout, serr = capsys.readouterr()
    print(_sout)
    print(serr)
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('prod', 1)


def test_mc_init_redefine_item_errors_default(capsys):
    errorline = [None]

    class X(ConfigItem):
        def mc_init(self):
            with ItemWithAA() as aai:
                aai.setattr('aa', default=1)
                errorline[0] = next_line_num()
                aai.setattr('aa', default=2)

    xfail("TODO: This will not raise because the first aai.setattr does not change the value, so value in second aai.setattr is still from __init__")
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config0(_):
            with X() as x:
                ItemWithAA(aa=7)

    _sout, serr = capsys.readouterr()
    print(_sout)
    print(serr)
    assert serr.startswith(ce(errorline[0], _fully_defined).strip())
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_item_expected_ex % ('prod', 1)

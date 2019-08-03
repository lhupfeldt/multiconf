# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException
from multiconf.decorators import nested_repeatables
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num, replace_ids
from .utils.messages import already_printed_msg
from .utils.messages import not_repeatable_in_parent_msg


# ef1
ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

# ef2
ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_single_error_on_project_expected_ex = """There was 1 error when defining item: {
    "__class__": "project #as: 'project', id: 0000, not-frozen",
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


@nested_repeatables('RepeatableItems')
class project(ConfigItem):
    pass


class RepeatableItem(RepeatableConfigItem):
    pass


_nested_item_overrides_simple_attribute_expected_ex = """'ConfigItem' is defined both as simple value and a contained item: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    }
}"""

def test_nested_item_overrides_simple_attribute():
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                cr.setattr('ConfigItem', default="hello", mc_set_unknown=True)
                ConfigItem()

    assert replace_ids(str(exinfo.value), named_as=False) == _nested_item_overrides_simple_attribute_expected_ex


def test_nested_repeatable_item_overrides_simple_attribute_not_contained_in_repeatable():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                # cr.RepeatableItems is just an attribute named like an item
                cr.setattr('RepeatableItems', prod="hello", mc_set_unknown=True)
                RepeatableItem(mc_key=None)

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='RepeatableItems', repeatable_cls="<class 'test.attribute_item_mixup_errors_test.RepeatableItem'>",
        ci_named_as='ConfigItem', ci_cls="<class 'multiconf.multiconf.ConfigItem'>")
    assert replace_ids(str(exinfo.value), named_as=False) == exp


def test_attempt_to_replace_empty_nested_repeatable_by_attribute_assignment(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            # RepeatableItems is just an attribute named like an item
            with project() as cr:
                errorline[0] = next_line_num()
                cr.RepeatableItems = 1

    _sout, serr = capsys.readouterr()
    msg = "'RepeatableItems' is already defined as a nested-repeatable and may not be replaced with an attribute."
    assert serr == ce(errorline[0], msg)
    print(_single_error_on_project_expected_ex % '"RepeatableItems": {}')
    print(replace_ids(str(exinfo.value), named_as=False))
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_project_expected_ex % '"RepeatableItems": {}'


def test_attempt_to_replace_non_empty_nested_repeatable_by_attribute_assignment(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            # RepeatableItems is just an attribute named like an item
            with project() as cr:
                RepeatableItem(mc_key='a')
                errorline[0] = next_line_num()
                cr.RepeatableItems = 1

    _sout, serr = capsys.readouterr()
    msg = "'RepeatableItems' is already defined as a nested-repeatable and may not be replaced with an attribute."
    assert serr == ce(errorline[0], msg)
    assert replace_ids(str(exinfo.value), named_as=False) == _single_error_on_project_expected_ex % ('"RepeatableItems": ' + _repeatable_item_json)


# def nested_repeatable_item_overrides_simple_attribute_contained_in_repeatable(self):
# @todo
#     with raises(ConfigException) as exinfo:
#         @nested_repeatables('children')
#         class root(ConfigItem):
#             pass
#
#         @named_as('children')
#         class rchild(RepeatableItem):
#             pass
#
#         with root(prod1, ef1_prod) as cr:
# TODO: 'cr' is a dict, so this call is not possible, which is fine, but the error message is not good
#             cr.children(prod="hello")
#             rchild()
#     assert str(exinfo.value) == "'children' is defined both as simple value and a contained item: children {\n}"


def test_simple_attribute_attempt_to_override_contained_item(capsys):
    errorline = [None]
    msg = "'ConfigItem' <class 'multiconf.multiconf.ConfigItem'> is already defined and may not be replaced with an attribute."

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                with ConfigItem():
                    pass
                errorline[0] = next_line_num()
                cr.setattr('ConfigItem', prod="hello", mc_set_unknown=True)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], msg)

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                ConfigItem()
                errorline[0] = next_line_num()
                cr.setattr('ConfigItem', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], msg)

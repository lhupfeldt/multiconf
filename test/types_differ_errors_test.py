# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises, xfail

from .utils.utils import next_line_num, replace_ids, assert_lines_in
from .utils.messages import already_printed_msg
from .utils.tstclasses import ItemWithAA

from multiconf import mc_config, ConfigItem, ConfigException
from multiconf.envs import EnvFactory


# ef1
ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

# ef2
ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')


_single_error_on_item_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "%s"
    },
    "aa": %s
}""" + already_printed_msg


class project(ConfigItem):
    pass


def test_attribute_defined_with_different_types_root(capsys):
    xfail("TODO: type check?")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=1, pp="hello")

    _sout, serr = capsys.readouterr()
    fl = start_file_line(__file__, errorline[0])
    assert_lines_in(
        serr,
        (fl + ", prod <%(type_or_class)s 'int'>", fl + ", pp <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex % 1


def test_attribute_defined_with_different_types_root_default(capsys):
    xfail("TODO: type check?")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        with ItemWithAA(prod2, ef2_pp_prod) as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', default="hello", prod=1)

    _sout, serr = capsys.readouterr()
    fl = start_file_line(__file__, errorline[0])
    assert_lines_in(
        serr,
        (fl + ", prod <%(type_or_class)s 'int'>", fl + ", default <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex % 1


_attribute_defined_with_different_types_init_expected_ex = """There was 1 error when defining item: {
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
    xfail("TODO: type check?")
    class root(ConfigItem):
        init_line = 0

        def __init__(self, selected_env, env_factory, a):
            super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)
            root.init_line = next_line_num()
            self.a = a

    with raises(ConfigException) as exinfo:
        with root(prod2, ef2_pp_prod, a="hello") as cr:
            errorline1 = next_line_num()
            cr.setattr('a', default=1)

    _sout, serr1 = capsys.readouterr()
    assert replace_ids(str(exinfo.value), False) == _attribute_defined_with_different_types_init_expected_ex + already_printed_msg

    class item(ConfigItem):
        init_line = 0

        def __init__(self, a):
            super(item, self).__init__()
            item.init_line = next_line_num()
            self.a = a

    with raises(ConfigException) as exinfo:
        with project(prod1, ef1_prod):
            with item(a="hello") as ci:
                errorline2 = next_line_num()
                ci.a = 1

    _sout, serr2 = capsys.readouterr()
    assert replace_ids(str(exinfo.value), named_as=False) == _attribute_defined_with_different_types_item_init_expected_ex + already_printed_msg

    for init_line, errorline, serr in ((root.init_line, errorline1, serr1), (item.init_line, errorline2, serr2)):
        fle = start_file_line(__file__, errorline)
        fli = start_file_line(__file__, initline)

        assert_lines_in(
            __file__, errorline, serr,
            fle + ", default <%(type_or_class)s 'int'>",
            fli + ", default <%(type_or_class)s 'str'>",
            "^ConfigError: Found different value types for property 'a' for different envs",
        )

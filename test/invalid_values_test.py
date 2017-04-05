# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os.path

import pytest
from pytest import raises, mark, xfail  # pylint: disable=no-name-in-module

from multiconf import mc_config, ConfigItem, ConfigException, MC_REQUIRED, MC_TODO
from multiconf.envs import EnvFactory

from .utils.utils import config_error, config_warning, next_line_num, replace_ids, lines_in, start_file_line, file_line, py3_tc
from .utils.messages import already_printed_msg
from .utils.messages import config_error_mc_required_expected
from .utils.messages import mc_required_expected
from .utils.messages import mc_todo_current_env_expected, mc_todo_other_env_expected
from .utils.messages import config_error_mc_todo_current_env_expected
from .utils.tstclasses import ItemWithAA
from .utils.invalid_values_classes import  McRequiredInInitL1, McRequiredInInitL3


_utils = os.path.join(os.path.dirname(__file__), 'utils')


ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')

ef2_prod_pp_dev = EnvFactory()
dev2 = ef2_prod_pp_dev.Env('dev')
pp2 = ef2_prod_pp_dev.Env('pp')
prod2 = ef2_prod_pp_dev.Env('prod')

ef3_prod_pp_tst_dev = EnvFactory()
dev3 = ef3_prod_pp_tst_dev.Env('dev')
tst3 = ef3_prod_pp_tst_dev.Env('tst')
pp3 = ef3_prod_pp_tst_dev.Env('pp')
prod3 = ef3_prod_pp_tst_dev.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)


_attribute_mc_required_expected = mc_required_expected.format(attr='aa', env=prod1)


_mc_required_one_error_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "%(env_name)s"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg


_multiple_errors_expected_ex = """There were %(num_errors)s errors when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "%(env_name)s"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg


def test_attribute_mc_required_env(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_required_mc_force_env(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', default=MC_REQUIRED, mc_force=True)

    # ef1_prod_pp.config(prod1)
    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='pp')


def test_attribute_mc_required_default(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', default=MC_REQUIRED, pp="hello")

    # ef1_prod_pp.config(prod1)
    _sout, serr = capsys.readouterr()
    print(_sout)
    assert serr == ce(errorline[0], _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_required_init(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def config(root):
            with ItemWithAA(aa=MC_REQUIRED) as ci:
                errorline[0] = next_line_num()
                ci.setattr('aa', pp="hello")

    # ef1_prod_pp.config(prod1)
    _sout, serr = capsys.readouterr()
    print(serr)
    print("errorline[0]", errorline[0])
    assert serr == ce(errorline[0], _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_required(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod="hi", pp=MC_REQUIRED)

    # ef1_prod_pp.config(prod1)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], mc_required_expected.format(attr='aa', env=pp1))
    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='pp')


_attribute_mc_required_different_types_expected_ex = """There were 2 errors when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "hi"
}""" + already_printed_msg

def test_attribute_mc_required_different_types(capsys):
    xfail("TODO typecheck")
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp_dev)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', dev=1, prod="hi", pp=MC_REQUIRED)

    # ef2_prod_pp_dev.config(prod2)
    _sout, serr = capsys.readouterr()

    fl = start_file_line(__file__, errorline[0])
    assert lines_in(
        serr,
        ("{fl}, dev <{tc} 'int'>".format(f=fl, tc=py3_tc), "{fl}, prod <{tc} 'str'>".format(f=fl, tc=py3_tc)),
        "^ConfigError: Found different value types for property 'aa' for different envs",
        fl,
        config_error_mc_required_expected.format(attr='aa', env=pp1)
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_different_types_expected_ex


def test_attribute_mc_required_default_all_overridden():
    @mc_config(ef1_prod_pp)
    def config(root):
        with ItemWithAA() as cr:
            # TODO: This should actually not be allowed, it does not make sense!
            cr.setattr('aa', default=MC_REQUIRED, pp="hello", prod="hi")

    cr = ef1_prod_pp.config(prod1).ItemWithAA
    assert cr.aa == "hi"


def test_attribute_mc_required_init_args_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    @mc_config(ef1_prod_pp)
    def config(root):
        with ConfigItem() as cr:
            Requires(aa=3)

    cr = ef1_prod_pp.config(prod1).ConfigItem
    assert cr.Requires.aa == 3

    @mc_config(ef1_prod_pp)
    def config(root):
        with ConfigItem() as cr:
            with Requires() as rq:
                rq.aa = 3

    cr = ef1_prod_pp.config(prod1).ConfigItem
    assert cr.Requires.aa == 3


def test_attribute_mc_required_args_all_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

        def mc_init(self):
            self.aa = 7

    @mc_config(ef1_prod_pp)
    def config(root):
        Requires()

    cr = ef1_prod_pp.config(prod1)
    assert cr.Requires.aa == 7


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('b', default=MC_REQUIRED, prod=2)

        def mc_init(self):
            self.aa = 7
            self.b = 7

    @mc_config(ef1_prod_pp)
    def config(root):
        Requires()
    cr = ef1_prod_pp.config(prod1)

    assert cr.Requires.aa == 7
    assert cr.Requires.b == 2

    cr = ef1_prod_pp.config(pp1)
    assert cr.Requires.aa == 7
    assert cr.Requires.b == 7


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_with():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('b', default=MC_REQUIRED, prod=2)

    @mc_config(ef1_prod_pp)
    def config(root):
        with Requires() as rq:
            rq.aa = 8
            rq.setattr('b', pp=8)

    cr = ef1_prod_pp.config(prod1)
    assert cr.Requires.aa == 8
    assert cr.Requires.b == 2

    cr = ef1_prod_pp.config(pp1)
    assert cr.Requires.aa == 8
    assert cr.Requires.b == 8


def test_attribute_mc_required_args_set_in_init_overridden_in_with():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    @mc_config(ef1_prod_pp)
    def config(root):
        with Requires() as rq:
            rq.aa = 7

    cr = ef1_prod_pp.config(prod1)
    assert cr.Requires.aa == 7

    cr = ef1_prod_pp.config(pp1)
    assert cr.Requires.aa == 7


_attribute_mc_required_requires_expected_ex = """There was 1 error when defining item: {
    "__class__": "Requires #as: 'Requires', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg


def test_attribute_mc_required_init_args_missing_env_value(capsys):
    errorline = [None]
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def config(root):
            with Requires() as rq:
                errorline[0] = next_line_num()
                rq.setattr('aa', prod='hi')

    _sout, serr = capsys.readouterr()
    print(_sout)
    assert serr == ce(errorline[0], mc_required_expected.format(attr='aa', env=pp1))
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_requires_expected_ex


_attribute_mc_required_required_init_arg_missing_with_expected_ex = """There was 1 error when defining item: {{
    "__class__": "{0} #as: '{0}', id: 0000, not-frozen",
    "env": {{
        "__class__": "Env",
        "name": "pp"
    }},
    "aa": "MC_REQUIRED"
}}""" + already_printed_msg

def test_attribute_mc_required_init_args_missing_with(capsys):
    errorline = [None]

    # If the error occures on the last object, and that is not under a with statement, then the line will be the @mc_config
    with raises(ConfigException) as exinfo:
        errorline[0] = next_line_num()
        @mc_config(ef1_prod_pp)
        def _(root):
            McRequiredInInitL1()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: The following attribues defined earlier never received a proper value for Env('pp'):",
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL1')

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def _(root):
            with McRequiredInInitL1():
                errorline[0] = next_line_num()
                pass

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: The following attribues defined earlier never received a proper value for Env('pp'):",
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL1')

    # If the error occures on the last object, and that is not under a with statement, then the line will be the @mc_config
    with raises(ConfigException) as exinfo:
        errorline[0] = next_line_num()
        @mc_config(ef1_prod_pp)
        def _(root):
            McRequiredInInitL3()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: The following attribues defined earlier never received a proper value for Env('pp'):",
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL3')

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def _(root):
            with McRequiredInInitL3():
                errorline[0] = next_line_num()
                pass

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: The following attribues defined earlier never received a proper value for Env('pp'):",
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL3')


def test_attribute_mc_required_init_args_missing_previous_item(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def _(root):
            errorline[0] = next_line_num()
            McRequiredInInitL1()
            McRequiredInInitL3()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        "^ConfigError: The following attribues defined earlier never received a proper value for Env('pp'):",
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL1')


def test_attribute_mc_required_init_assign_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    @mc_config(ef1_prod_pp)
    def config(root):
        Requires(aa=3)

    cr = ef1_prod_pp.config(prod1)
    assert cr.Requires.aa == 3

    @mc_config(ef1_prod_pp)
    def _(_):
        with Requires() as rq:
            rq.aa = 3

    cr = ef1_prod_pp.config(prod1)
    assert cr.Requires.aa == 3


# MC_TODO

_attribute_mc_current_env_todo_expected = mc_todo_current_env_expected.format(attr='aa', env=prod1)
_attribute_mc_todo_other_env_expected = mc_todo_other_env_expected.format(attr='aa', env=prod1)


# MC_TODO - Not Allowed for Current Env

_mc_todo_one_error_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "%(env_name)s"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg


@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env(capsys, allow_todo):
    xfail("TODO implement test")
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, mc_allow_todo=allow_todo)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=MC_TODO, pp="hello")

    # ef1_prod_pp.config(prod1)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_default(capsys, allow_todo):
    xfail("TODO implement test")
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, mc_allow_todo=allow_todo)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', default=MC_TODO, pp="hello")

    # ef1_prod_pp.config(prod1)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_init(capsys, allow_todo):
    errorline = [None]
    if not allow_todo:
        with raises(ConfigException) as exinfo:
            @mc_config(ef1_prod_pp, mc_allow_todo=allow_todo)
            def config(root):
                with ItemWithAA(aa=MC_TODO) as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('aa', pp="hello")

        assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')
    else:
        @mc_config(ef1_prod_pp, mc_allow_todo=allow_todo)
        def config(root):
            with ItemWithAA(aa=MC_TODO) as ci:
                errorline[0] = next_line_num()
                ci.setattr('aa', pp="hello")

        with raises(ConfigException) as exinfo:
            ef1_prod_pp.config(prod1)

        assert str(exinfo.value) == "Trying to get invalid configuration containing MC_TODO"

    _sout, serr = capsys.readouterr()
    xfail("TODO: is a warning")
    assert serr == ce(errorline[0], _attribute_mc_current_env_todo_expected)


_attribute_mc_required_mc_todo_different_types_expected_ex = """There were 3 errors when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_required_mc_todo_different_types(capsys, allow_todo):
    xfail("TODO implement")
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef3_prod_pp_tst_dev, mc_allow_todo=allow_todo)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', dev=1, tst="hello", pp=MC_REQUIRED, prod=MC_TODO)

    # ef3_prod_pp_tst_dev.config(prod3)
    _sout, serr = capsys.readouterr()

    fl = start_file_line(__file__, errorline[0])
    assert lines_in(
        serr,
        ("{fl}, dev <{tc} 'int'>".format(f=fl, tc=py3_tc), "{fl}, tst <{tc} 'str'>".format(f=fl, tc=py3_tc)),
        "^ConfigError: Found different value types for property 'aa' for different envs",
        fl,
        config_error_mc_required_expected.format(attr='aa', env=pp3),
        config_error_mc_todo_current_env_expected.format(attr='aa', env=prod3),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_mc_todo_different_types_expected_ex


# MC_TODO - Not Allowed for Other Envs

def test_attribute_mc_todo_other_env_env(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, mc_allow_todo=False)
        def config(root):
            with ItemWithAA(aa=MC_TODO) as ci:
                errorline[0] = next_line_num()
                ci.setattr('aa', prod=MC_TODO, pp="hello")

    # ef1_prod_pp.config(pp1)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _attribute_mc_todo_other_env_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_todo_other_env_default(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, mc_allow_todo=False)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', default=MC_TODO, pp="hello")

    # ef1_prod_pp.config(pp1)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _attribute_mc_todo_other_env_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_todo_other_env_init(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, mc_allow_todo=False)
        def config(root):
            with ItemWithAA(aa=MC_TODO) as ci:
                errorline[0] = next_line_num()
                ci.setattr('aa', pp="hello")

    # ef1_prod_pp.config(pp1)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], _attribute_mc_todo_other_env_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


# MC_TODO - Allowed Other Envs

@mark.parametrize("allow_current_env_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_env(capsys, allow_current_env_todo):
    xfail("TODO implement test")
    errorline = [None]
    @mc_config(ef1_prod_pp, mc_allow_todo=allow_current_env_todo)
    def _(_):
        with ItemWithAA() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_default_allowed_other_env(capsys):
    xfail("TODO implement test")
    errorline = [None]
    with ItemWithAA(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=False) as cr:
        errorline[0] = next_line_num()
        cr.setattr('aa', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_init_allowed_other_env(capsys):
    xfail("TODO implement test")
    errorline = [None]
    with ConfigItem(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=False):
        with ItemWithAA(aa=MC_TODO) as ci:
            errorline[0] = next_line_num()
            ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_todo_other_env_expected)


# MC_TODO - Allowed Current Envs

_continuing_with_invalid_conf = ". Continuing with invalid configuration!"
_attribute_mc_current_env_todo_allowed_expected = _attribute_mc_current_env_todo_expected + _continuing_with_invalid_conf

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_envs(capsys, allow_todo):
    xfail("TODO implement test")
    errorline = [None]
    with ItemWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        errorline[0] = next_line_num()
        cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_default_allowed_other_envs(capsys):
    xfail("TODO implement test")
    errorline = [None]
    with ItemWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True) as cr:
        errorline[0] = next_line_num()
        cr.setattr('aa', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_init_allowed_other_envs(capsys):
    xfail("TODO implement test")
    errorline = [None]
    with ConfigItem(prod1, ef1_prod_pp, mc_allow_current_env_todo=True):
        with ItemWithAA(aa=MC_TODO) as ci:
            errorline[0] = next_line_num()
            ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_current_env_todo_allowed_expected)


@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env_allowed_current_env_access_error(capsys, allow_todo):
    xfail("TODO implement test")
    errorline = [None]
    """Test that accessing an MC_TODO value after loading results in an exception"""
    with ItemWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        errorline[0] = next_line_num()
        cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_current_env_todo_allowed_expected)

    with raises(AttributeError) as exinfo:
        print(cr.aa)

    assert "Attribute 'aa' MC_TODO is undefined for current env " + repr(prod1) in str(exinfo.value)


@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_override_allowed_other_envs(capsys, allow_todo):
    xfail('TODO')
    errorline = [None]

    @mc_config(ef1_prod_pp, mc_allow_todo=allow_todo)
    def _(_):
        with ItemWithAA() as cr:
            cr.aa = 2
            errorline[0] = next_line_num()
            cr.setattr('aa', default=MC_TODO, mc_force=True)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "ConfigWarning: " + mc_todo_other_env_expected.format(attr='aa', env=pp1),
        "ConfigWarning: " + mc_todo_current_env_expected.format(attr='aa', env=prod1),
    )


_attribute_mc_required_env_in_init_expected_ex = """There were %(num_errors)s errors when defining item: {
    "__class__": "MyRoot #as: 'MyRoot', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "MC_REQUIRED",
    "bb": "MC_REQUIRED"
}""" + already_printed_msg


def test_attribute_setattr_mc_required_force_in_init(capsys):
    errorline = [None]

    class MyRoot(ConfigItem):
        def __init__(self):
            super(MyRoot, self).__init__()
            errorline[0] = next_line_num()
            self.setattr('aa', default=MC_REQUIRED, mc_force=True)
            self.setattr('bb', default=MC_REQUIRED, mc_force=True)

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def _(_):
            MyRoot()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='aa', env=pp1),
        config_error_mc_required_expected.format(attr='bb', env=pp1),
    )

    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_in_init_expected_ex % dict(num_errors=2)


def test_multiple_attributes_mc_required_init_not_set(capsys):
    errorline = [None]
    class ItemWithAAABBCC(ConfigItem):
        def __init__(self):
            super(ItemWithAAABBCC, self).__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED
            self.cc = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def _(_):
            with ConfigItem() as cr:
                errorline[0] = next_line_num()
                ItemWithAAABBCC()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='aa', env=pp1),
        config_error_mc_required_expected.format(attr='bb', env=pp1),
        config_error_mc_required_expected.format(attr='cc', env=pp1),
    )


_multiple_attributes_mc_required_env_expected_ex = """There %(ww)s %(num_errors)s %(err)s when defining item: {
    "__class__": "MyRoot #as: 'MyRoot', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "hello",
    "bb": "MC_REQUIRED"
}""" + already_printed_msg

def test_multiple_attributes_mc_required_env(capsys):
    errorline = [None]

    class MyRoot(ConfigItem):
        def __init__(self):
            super(MyRoot, self).__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp)
        def _(_):
            with MyRoot() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=MC_REQUIRED, pp="hello")
                cr.setattr('bb', prod=1, pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    #assert ce(errorline[0], mc_required_expected.format(attr='aa', env=prod1)) in serr
    assert ce(errorline[0] + 1, mc_required_expected.format(attr='bb', env=pp1)) in serr
    assert replace_ids(str(exinfo.value), False) == _multiple_attributes_mc_required_env_expected_ex % dict(ww='was', num_errors=1, err='error')

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path

from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num, replace_ids, lines_in, start_file_line
from .utils.messages import already_printed_msg, config_error_mc_required_expected, mc_required_expected
from .utils.messages import config_error_never_received_value_expected
from .utils.tstclasses import ItemWithAA
from .utils.invalid_values_classes import  McRequiredInInitL1, McRequiredInInitL3


minor_version = sys.version_info[1]

_utils = os.path.join(os.path.dirname(__file__), 'utils')


ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_attribute_mc_required_expected = mc_required_expected.format(attr='aa', env=prod1)


_mc_required_one_error_expected_ex = """There was 1 error when defining item: {
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
        @mc_config(ef1_prod_pp, load_now=True)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=prod1),
        start_file_line(__file__, errorline[0]),
        '^ConfigError: ' + _attribute_mc_required_expected,
    )

    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_required_mc_force_env(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', default=MC_REQUIRED, mc_force=True)

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
        @mc_config(ef1_prod_pp, load_now=True)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', default=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=prod1),
        start_file_line(__file__, errorline[0]),
        '^ConfigError: ' + _attribute_mc_required_expected,
    )

    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_required_default_resolved_with_default_value_in_mc_init(capsys):
    class ItemWithAAMcInitResolve(ItemWithAA):
        def mc_init(self):
            super().mc_init()
            self.aa = 'Hi'

    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        with ItemWithAAMcInitResolve() as cr:
            cr.setattr('aa', default=MC_REQUIRED, pp="hello")

    cfg = config(pp1)
    assert cfg.ItemWithAAMcInitResolve.aa == 'hello'

    cfg = config(prod1)
    assert cfg.ItemWithAAMcInitResolve.aa == 'Hi'


def test_attribute_mc_required_default_resolved_with_default_env_specific_value_in_mc_init(capsys):
    class ItemWithAAMcInitResolve(ItemWithAA):
        def mc_init(self):
            super().mc_init()
            self.setattr('aa', prod='Hi')

    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        with ItemWithAAMcInitResolve() as cr:
            cr.setattr('aa', default=MC_REQUIRED, pp="hello")

    cfg = config(pp1)
    assert cfg.ItemWithAAMcInitResolve.aa == 'hello'

    cfg = config(prod1)
    assert cfg.ItemWithAAMcInitResolve.aa == 'Hi'


def test_attribute_mc_required_init(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(root):
            with ItemWithAA(aa=MC_REQUIRED) as ci:
                errorline[0] = next_line_num()
                ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    print(serr)
    print("errorline[0]", errorline[0])
    assert serr == ce(errorline[0], _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='prod')


def test_attribute_mc_required_in_with(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(root):
            with ItemWithAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod="hi", pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp1),
        start_file_line(__file__, errorline[0]),
        '^ConfigError: ' + mc_required_expected.format(attr='aa', env=pp1),
    )

    assert replace_ids(str(exinfo.value), False) == _mc_required_one_error_expected_ex % dict(env_name='pp')


def test_attribute_mc_required_in_with_default_all_overridden():
    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            # TODO: This should actually not be allowed, it does not make sense!
            cr.setattr('aa', default=MC_REQUIRED, pp="hello", prod="hi")

    cr = config(prod1).ItemWithAA
    assert cr.aa == "hi"


def test_attribute_mc_required_init_args_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__()
            self.aa = aa

    @mc_config(ef1_prod_pp, load_now=True)
    def config1(root):
        with ConfigItem() as cr:
            Requires(aa=3)

    cr = config1(prod1).ConfigItem
    assert cr.Requires.aa == 3

    @mc_config(ef1_prod_pp, load_now=True)
    def config2(root):
        with ConfigItem() as cr:
            with Requires() as rq:
                rq.aa = 3

    cr = config2(prod1).ConfigItem
    assert cr.Requires.aa == 3


def test_attribute_mc_required_args_all_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__()
            self.aa = aa

        def mc_init(self):
            self.aa = 7

    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        Requires()

    cr = config(prod1)
    assert cr.Requires.aa == 7


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('b', default=MC_REQUIRED, prod=2)

        def mc_init(self):
            self.aa = 7
            self.b = 7

    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        Requires()
    cr = config(prod1)

    assert cr.Requires.aa == 7
    assert cr.Requires.b == 2

    cr = config(pp1)
    assert cr.Requires.aa == 7
    assert cr.Requires.b == 7


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_with():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('b', default=MC_REQUIRED, prod=2)

    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        with Requires() as rq:
            rq.aa = 8
            rq.setattr('b', pp=8)

    cr = config(prod1)
    assert cr.Requires.aa == 8
    assert cr.Requires.b == 2

    cr = config(pp1)
    assert cr.Requires.aa == 8
    assert cr.Requires.b == 8


def test_attribute_mc_required_args_set_in_init_overridden_in_with():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__()
            self.aa = aa

    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        with Requires() as rq:
            rq.aa = 7

    cr = config(prod1)
    assert cr.Requires.aa == 7

    cr = config(pp1)
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
            super().__init__()
            self.aa = aa

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
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
        errorline[0] = next_line_num() + (1 if minor_version > 7 else 0)
        @mc_config(ef1_prod_pp, load_now=True)
        def config(root):
            McRequiredInInitL1()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp1),
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    exp = _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL1')
    got = replace_ids(str(exinfo.value), False)
    assert got == exp

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config0(root):
            with McRequiredInInitL1():
                errorline[0] = next_line_num()
                pass

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp1),
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL1')

    # If the error occures on the last object, and that is not under a with statement, then the line will be the @mc_config
    with raises(ConfigException) as exinfo:
        errorline[0] = next_line_num() + (1 if minor_version > 7 else 0)
        @mc_config(ef1_prod_pp, load_now=True)
        def config1(root):
            McRequiredInInitL3()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp1),
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL3')

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config2(root):
            with McRequiredInInitL3():
                errorline[0] = next_line_num()
                pass

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp1),
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL3')


def test_attribute_mc_required_init_args_missing_previous_item(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(root):
            errorline[0] = next_line_num()
            McRequiredInInitL1()
            McRequiredInInitL3()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        config_error_never_received_value_expected.format(env=pp1),
        '^File "{}/invalid_values_classes.py", line 8'.format(_utils),
        mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_required_init_arg_missing_with_expected_ex.format('McRequiredInInitL1')


def test_attribute_mc_required_init_assign_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__()
            self.aa = aa

    @mc_config(ef1_prod_pp, load_now=True)
    def config(root):
        Requires(aa=3)

    cr = config(prod1)
    assert cr.Requires.aa == 3

    @mc_config(ef1_prod_pp, load_now=True)
    def config(_):
        with Requires() as rq:
            rq.aa = 3

    cr = config(prod1)
    assert cr.Requires.aa == 3


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
            super().__init__()
            errorline[0] = next_line_num()
            self.setattr('aa', default=MC_REQUIRED, mc_force=True)
            self.setattr('bb', default=MC_REQUIRED, mc_force=True)

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(_):
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
            super().__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED
            self.cc = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(_):
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



def test_multiple_attributes_mc_required_mc_init_not_set(capsys):
    errorlines = [None, None]
    class ItemWithAAABBCC(ConfigItem):
        def __init__(self):
            super().__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED
            self.cc = MC_REQUIRED

        def mc_init(self):
            super().__init__()
            errorlines[0] = next_line_num()
            self.setattr('aa', default=MC_REQUIRED)
            self.setattr('bb', default=MC_REQUIRED, pp='Hello')
            errorlines[1] = next_line_num()
            self.cc = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                ItemWithAAABBCC()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorlines[0]),
        config_error_mc_required_expected.format(attr='aa', env=pp1),
        start_file_line(__file__, errorlines[1]),
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
            super().__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(_):
            with MyRoot() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=MC_REQUIRED, pp="hello")
                cr.setattr('bb', prod=1, pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    #assert ce(errorline[0], mc_required_expected.format(attr='aa', env=prod1)) in serr
    assert ce(errorline[0] + 1, mc_required_expected.format(attr='bb', env=pp1)) in serr
    assert replace_ids(str(exinfo.value), False) == _multiple_attributes_mc_required_env_expected_ex % dict(ww='was', num_errors=1, err='error')

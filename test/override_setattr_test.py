# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigException
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num, replace_ids
from .utils.messages import already_printed_msg, mc_required_expected
from .utils.tstclasses import ItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


class MeSetterItem(ItemWithAA):
    def setme(self, name, mc_overwrite_property=False, mc_set_unknown=False, mc_force=False, **mevalues):
        super().setattr(
            name, mc_overwrite_property=mc_overwrite_property, mc_set_unknown=mc_set_unknown, mc_force=mc_force,
            mc_error_info_up_level=3, **mevalues)


def test_override_setattr():
    @mc_config(ef, load_now=True)
    def config(root):
        with MeSetterItem() as ci:
            ci.setme('aa', prod="hi", pp="hello")

    cr = config(prod).MeSetterItem
    assert cr.aa == "hi"
    cr = config(pp).MeSetterItem
    assert cr.aa == "hello"


_override_setattr1_expected_ex = """There was 1 error when defining item: {
    "__class__": "MeSetterItem #as: 'MeSetterItem', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "hello"
}""" + already_printed_msg


def test_override_setattr_error1(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(root):
            with MeSetterItem() as ci:
                errorline[0] = next_line_num()
                ci.setme('aa', pros="hello", prod="hi", pp="hello")

    _sout, serr = capsys.readouterr()
    print(serr)
    assert serr == ce(errorline[0], "No such Env or EnvGroup: 'pros'")
    assert replace_ids(str(exinfo.value), False) == _override_setattr1_expected_ex


_override_setattr2_expected_ex = """There was 1 error when defining item: {
    "__class__": "MeSetterItem #as: 'MeSetterItem', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg


def test_override_setattr_error2(capsys):
    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(root):
            with MeSetterItem() as ci:
                errorline[0] = next_line_num()
                ci.setme('aa', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], mc_required_expected.format(attr='aa', env=pp))
    assert replace_ids(str(exinfo.value), False) == _override_setattr2_expected_ex

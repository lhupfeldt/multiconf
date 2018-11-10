# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, MC_REQUIRED, ConfigException
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from utils.utils import py37_no_exc_comma, replace_ids


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


@nested_repeatables('someitems')
class root(ConfigItem):
    def __init__(self, aa=None):
        super().__init__()
        if aa is not None:
            self.aa = aa


@named_as('someitems')
@nested_repeatables('someitems')
class NestedRepeatable(RepeatableConfigItem):
    def __init__(self, mc_key, aa=MC_REQUIRED):
        super().__init__(mc_key=mc_key)
        self.aa = aa

    def mc_init(self):
        self.aa = 17


def test_json_no_freeze_before_setattr():
    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa=0):
            with NestedRepeatable(mc_key='a', aa=7) as ci:
                print(ci)
                ci.setattr('aa', prod=1, pp=2)

    cr = config(prod).root
    assert cr.someitems['a'].aa == 1

    cr = config(pp).root
    assert cr.someitems['a'].aa == 2


def test_json_no_freeze_after_setattr():
    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa=0):
            with NestedRepeatable(mc_key='a', aa=7) as ci:
                ci.setattr('aa', prod=1, pp=2)
                print(ci)

    cr = config(prod).root
    assert cr.someitems['a'].aa == 1

    cr = config(pp).root
    assert cr.someitems['a'].aa == 2


def test_json_no_freeze_before_setattr_mc_required():
    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa=0):
            with NestedRepeatable(mc_key='a') as ci:
                print(ci)
                ci.setattr('aa', prod=1, pp=2)

    cr = config(prod).root
    assert cr.someitems['a'].aa == 1

    cr = config(pp).root
    assert cr.someitems['a'].aa == 2


def test_json_no_freeze_after_setattr_mc_required():
    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa=0):
            with NestedRepeatable(mc_key='a') as ci:
                ci.setattr('aa', prod=1, pp=2)
                print(ci)

    cr = config(prod).root
    assert cr.someitems['a'].aa == 1

    cr = config(pp).root
    assert cr.someitems['a'].aa == 2


def test_json_no_freeze_no_setattr():
    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa=0):
            with NestedRepeatable(mc_key='a', aa=7) as ci:
                print(ci)

    cr = config(prod).root
    assert cr.someitems['a'].aa == 7

    cr = config(pp).root
    assert cr.someitems['a'].aa == 7


def test_json_no_freeze_no_setattr_mc_required():
    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa=0):
            with NestedRepeatable(mc_key='a') as ci:
                print(ci)

    cr = config(prod).root
    assert cr.someitems['a'].aa == 17

    cr = config(pp).root
    assert cr.someitems['a'].aa == 17


def test_json_no_freeze_after_setattr_property():
    class Xx(ConfigItem):
        def __init__(self, bb=MC_REQUIRED):
            self.bb = bb

        def mc_init(self):
            self.bb = 3

        @property
        def aa(self):
            return self.bb


    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa=0):
            with Xx() as xx:
                print(xx)

            with NestedRepeatable(mc_key='a') as ci:
                ci.setattr('aa', prod=1, pp=2)
                print(ci)

    cr = config(prod).root
    assert cr.someitems['a'].aa == 1

    cr = config(pp).root
    assert cr.someitems['a'].aa == 2

    assert cr.Xx.aa == 3


json_no_freeze_after_setattr_property_side_effect_error_exp1 = """{
    "__class__": "Xx #as: 'xxxx', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "bb": "MC_REQUIRED",
    "cc": 1,
    "aa #json_error trying to handle property method": "ConfigApiException(\\"Trying to set attribute 'cc'. Setting attributes is not allowed after configuration is loaded or while doing json dump (print) (in order to enforce derived value validity).\\"%(comma)s)"
}""" % dict(comma=py37_no_exc_comma)

json_no_freeze_after_setattr_property_side_effect_error_exp2 = """{
    "__class__": "NestedRepeatable #as: 'xxxx', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": 2,
    "someitems": {}
}"""

def test_json_no_freeze_after_setattr_property_side_effect_error(capsys):
    class Xx(ConfigItem):
        def __init__(self, bb=MC_REQUIRED):
            self.bb = bb
            self.cc = 1

        def mc_init(self):
            self.bb = 3

        @property
        def aa(self):
            self.cc = 2
            return self.bb

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with root(aa=0):
                with Xx() as xx:
                    print(xx.json(compact=True))

                with NestedRepeatable(mc_key='a') as ci:
                    ci.setattr('aa', prod=1, pp=2)
                    print(ci)

    sout, _ = capsys.readouterr()
    sout = replace_ids(sout)
    print('--- got exception ---')
    print(exinfo.value)
    print('--- got sout ---')
    print(sout)
    print('--- exp1 ---')
    print(json_no_freeze_after_setattr_property_side_effect_error_exp1)
    print('--- exp2 ---')
    print(json_no_freeze_after_setattr_property_side_effect_error_exp2)
    print('------')
    assert json_no_freeze_after_setattr_property_side_effect_error_exp1 in sout
    assert json_no_freeze_after_setattr_property_side_effect_error_exp2 in sout

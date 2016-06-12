# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from .. import ConfigRoot, ConfigItem, ConfigBuilder, RepeatableConfigItem, ConfigException, MC_REQUIRED
from ..decorators import nested_repeatables, strict_setattr
from ..envs import EnvFactory
from .utils.utils import replace_ids, config_error, lineno

ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_pp = EnvFactory()
pp2 = ef2_prod_pp.Env('pp')
prod2 = ef2_prod_pp.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


@nested_repeatables('RepeatableRelaxedItems', 'RepeatableStrictItems')
@strict_setattr()
class strict_project(ConfigRoot):
    def __init__(self, selected_env, env_factory):
        super(strict_project, self).__init__(selected_env=selected_env, env_factory=env_factory)
        self.a = None
        self.b = MC_REQUIRED


@nested_repeatables('RepeatableRelaxedItems', 'RepeatableStrictItems')
class relaxed_project(ConfigRoot):
    pass


class RelaxedItem(ConfigItem):
    pass


class RepeatableRelaxedItem(RepeatableConfigItem):
    pass


@strict_setattr()
class StrictItem(ConfigItem):
    def __init__(self):
        super(StrictItem, self).__init__()
        self.x = MC_REQUIRED
        self.y = None


@strict_setattr()
class RepeatableStrictItem(RepeatableConfigItem):
    def __init__(self, mc_key):
        super(RepeatableStrictItem, self).__init__(mc_key=mc_key)
        self.x = None
        self.y = MC_REQUIRED


@strict_setattr()
class BuilderStrictItem(ConfigBuilder):
    def __init__(self):
        super(BuilderStrictItem, self).__init__()
        self.x = MC_REQUIRED
        self.y = None

    def build(self):
        super(BuilderStrictItem, self).build()
        with StrictItem() as si:
            si.x = self.x
        with RelaxedItem() as ri:
            ri.c = self.y


def test_setattr_strict_ok():
    with strict_project(prod2, ef2_prod_pp) as sp:
        sp.a = 1
        sp.setattr('b', default=2)

        with StrictItem() as si:
            si.x = 1
            si.setattr('y', default='yes')

        with RepeatableStrictItem('a') as rsi:
            rsi.x = 1
            rsi.setattr('y', default='yes')

    assert sp.a == 1
    assert sp.b == 2
    assert si.x == 1
    assert si.y == 'yes'
    assert rsi.x == 1
    assert rsi.y == 'yes'


def test_setunknown_strict_ok():
    with strict_project(prod2, ef2_prod_pp) as sp:
        sp.b = 1
        sp.setattr('c?', default=2)

        with StrictItem() as si:
            si.x = 1
            si.setattr('z?', default='yes')

        with RepeatableStrictItem('a') as rsi:
            rsi.y = 1
            rsi.setattr('z?', default='yes')

    assert sp.c == 2
    assert si.z == 'yes'
    assert rsi.z == 'yes'


def test_setattr_strict_builder_ok():
    with strict_project(prod2, ef2_prod_pp) as sp:
        sp.a = 1
        sp.setattr('b', default=2)

        with BuilderStrictItem() as bsi:
            bsi.x = 1
            bsi.setattr('y', default='yes')

    assert bsi.x == 1
    assert bsi.y == 'yes'
    assert sp.StrictItem.x == 1
    assert sp.RelaxedItem.c == 'yes'


def test_setunknown_strict_builder_ok():
    with strict_project(prod2, ef2_prod_pp) as sp:
        sp.b = 1
        sp.setattr('c?', default=2)

        with BuilderStrictItem() as bsi:
            bsi.x = 1
            bsi.setattr('z?', default='yes')

    assert bsi.x == 1
    assert bsi.z == 'yes'
    assert sp.StrictItem.x == 1
    assert sp.RelaxedItem.z == 'yes'


_setattr_strict_bad_expected_root = """
All attributes must be defined in __init__ or set with the '?' postfix. Atempting to set attribute 'c' which does not exist on item: {
    "__class__": "strict_project #as: 'xxxx', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": null,
    "b": "MC_REQUIRED",
    "RepeatableRelaxedItems": {},
    "RepeatableStrictItems": {}
}""".strip()

_setattr_strict_bad_expected_nested = """
All attributes must be defined in __init__ or set with the '?' postfix. Atempting to set attribute 'z' which does not exist on item: {
    "__class__": "StrictItem #as: 'xxxx', id: 0000, not-frozen",
    "x": "MC_REQUIRED",
    "y": null
}""".strip()

_setattr_strict_bad_expected_repeatable_nested = """
All attributes must be defined in __init__ or set with the '?' postfix. Atempting to set attribute 'z' which does not exist on item: {
    "__class__": "RepeatableStrictItem #as: 'xxxx', id: 0000, not-frozen",
    "x": null,
    "y": "MC_REQUIRED"
}""".strip()

def test_setattr_strict_bad(capsys):
    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            errorline = lineno() + 1
            sp.c = 1

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setattr_strict_bad_expected_root)

    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            errorline = lineno() + 1
            sp.setattr('c', default=1)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setattr_strict_bad_expected_root)

    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            with StrictItem() as si:
                errorline = lineno() + 1
                si.z = 1

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setattr_strict_bad_expected_nested)

    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            with StrictItem() as si:
                errorline = lineno() + 1
                si.setattr('z', prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setattr_strict_bad_expected_nested)

    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            with RepeatableStrictItem('a') as rsi:
                errorline = lineno() + 1
                rsi.z = 1

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setattr_strict_bad_expected_repeatable_nested)

    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            with RepeatableStrictItem('b') as rsi:
                errorline = lineno() + 1
                rsi.setattr('z', prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setattr_strict_bad_expected_repeatable_nested)


_setunknown_strict_bad_expected_root = """
Atempting to use '?' postfix to set attribute 'b'  which exists on item: {
    "__class__": "strict_project #as: 'xxxx', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": null,
    "b": "MC_REQUIRED",
    "RepeatableRelaxedItems": {},
    "RepeatableStrictItems": {}
}""".strip()

_setunknown_strict_bad_expected_nested = """
Atempting to use '?' postfix to set attribute 'y'  which exists on item: {
    "__class__": "StrictItem #as: 'xxxx', id: 0000, not-frozen",
    "x": "MC_REQUIRED",
    "y": null
}""".strip()

_setunknown_strict_bad_expected_repeatable_nested = """
Atempting to use '?' postfix to set attribute 'y'  which exists on item: {
    "__class__": "RepeatableStrictItem #as: 'xxxx', id: 0000, not-frozen",
    "x": null,
    "y": "MC_REQUIRED"
}""".strip()

def test_setunknown_strict_bad(capsys):
    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            errorline = lineno() + 1
            sp.setattr('b?', default=1)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setunknown_strict_bad_expected_root)

    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            with StrictItem() as si:
                errorline = lineno() + 1
                si.setattr('y?', prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setunknown_strict_bad_expected_nested)

    with raises(ConfigException) as exinfo:
        with strict_project(prod2, ef2_prod_pp) as sp:
            with RepeatableStrictItem('b') as rsi:
                errorline = lineno() + 1
                rsi.setattr('y?', prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline, _setunknown_strict_bad_expected_repeatable_nested)

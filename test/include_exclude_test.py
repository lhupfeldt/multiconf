# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, assert_lines_in
from .utils.compare_json import compare_json

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import required, repeat, nested_repeatables

from ..envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
dev3 = ef.Env('dev3')
g_dev12 = ef.EnvGroup('g_dev12', dev1, dev2)
g_dev23 = ef.EnvGroup('g_dev23', dev2, dev3)
g_dev13 = ef.EnvGroup('g_dev13', dev1, dev3)
g_dev12_3 = ef.EnvGroup('g_dev12_3', g_dev12, dev3)
pp = ef.Env('pp')
prod = ef.Env('prod')
g_ppr = ef.EnvGroup('g_ppr', pp, prod)


@required('anattr, anotherattr')
class item(ConfigItem):
    pass


_include_exclude_for_configitem_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": 1,
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude_test.item'>": true
}"""

def test_include_for_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_include=[dev1, pp]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


def test_include_missing_for_configitem(capsys):
    def conf(env, errorline):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_include=[dev1, pp]) as it:
                errorline.append(lineno() + 1)
                it.setattr('anattr', g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)
        return cr

    errorline = []
    with raises(ConfigException) as exinfo:
        conf(prod, errorline)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], "Attribute: 'anattr' did not receive a value for env Env('pp')")
    assert "There were 1 errors when defining attribute 'anattr' on object" in str(exinfo.value)


def test_exclude_for_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_exclude=[dev2, prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


@required('anattr, anotherattr')
@repeat()
class ritem(ConfigItem):
    pass


@nested_repeatables('ritems')
class root(ConfigRoot):
    pass


_include_exclude_for_configitem_repeatable_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": 1,
    "ritems": {}
}"""

def test_include_for_configitem_repeatable():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_include=[dev1, pp]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert cr.ritems == {}
    compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_exclude_for_configitem_repeatable():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_exclude=[dev2, prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert cr.ritems == {}
    compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_exclude_for_nested_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1


def test_exclude_for_repeatable_nested_configitem():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_exclude=[dev2, dev3, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)
                    with item() as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

            with ritem(id='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

            with ritem(id='c', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev3=0, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev3=0, pp=2)

        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33
    assert 'c' not in cr.ritems
    assert len(cr.ritems) == 1

    cr = conf(dev1)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert 'c' in cr.ritems
    assert cr.ritems['c'].anattr == 2
    assert cr.ritems['c'].item.anattr == 2
    assert cr.ritems['c'].item.anotherattr == 1
    assert len(cr.ritems) == 2


def test_exclude_for_repeatable_nested_excludes_configitem():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev3=0, pp=2)
                with item(mc_exclude=[pp, dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)
                    with item(mc_exclude=[dev2]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

            with ritem(id='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                with item(mc_exclude=[pp]) as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert len(cr.ritems) == 1

    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = conf(dev1)
    assert cr.a == 1
    assert len(cr.ritems) == 1

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].item.item.anattr == 2
    assert 'b' not in cr.ritems

    cr = conf(pp)
    assert cr.a == 1
    assert len(cr.ritems) == 2

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 1
    assert not cr.ritems['a'].item
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 1
    assert not cr.ritems['b'].item

    cr = conf(dev2)
    assert cr.a == 1
    assert len(cr.ritems) == 1

    assert 'a' not in cr.ritems
    with raises(KeyError):
        _ = cr.ritems['a']
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 2
    assert cr.ritems['b'].anotherattr == 3
    assert cr.ritems['b'].item.anattr == 2
    assert cr.ritems['b'].item.anotherattr == 1

    cr = conf(dev3)
    assert cr.a == 1
    assert len(cr.ritems) == 1

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 0
    assert not cr.ritems['a'].item
    assert 'b' not in cr.ritems
    with raises(KeyError):
        _ = cr.ritems['b']


def test_child_includes_excluded(capsys):
    with raises(ConfigException) as exinfo:
        with root(prod, ef):
            with ritem(id='a', mc_exclude=[g_dev12_3, prod]):
                errorline = lineno() + 1
                with item(mc_include=[dev2, prod]) as it1:
                    it1.x = 7

    assert "There were 2 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    print(serr)
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: Env 'dev2' is excluded at an outer level",
        "^%(lnum)s",
        "^ConfigError: Env 'prod' is excluded at an outer level"
    )


def test_exclude_include_overlapping_for_configitem(capsys):
    """Test that most specifig group/env wins"""

    with raises(ConfigException) as exinfo:
        # No most specific
        with ConfigRoot(prod, ef):
            errorline = lineno() + 1
            item(mc_exclude=[dev1], mc_include=[dev1, pp])

    assert "There were 1 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Env 'dev1' is specified in both include and exclude, with no single most specific group or direct env:\n    from: Env('dev1')")

    with raises(ConfigException) as exinfo:
        # No most specific
        with ConfigRoot(prod, ef):
            errorline = lineno() + 1
            item(mc_exclude=[pp, dev1], mc_include=[dev1])

    assert "There were 1 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Env 'dev1' is specified in both include and exclude, with no single most specific group or direct env:\n    from: Env('dev1')")

    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev12]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1, dev3=0)
                it.setattr('anotherattr', default=111)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.a == 1
    assert not cr.item

    cr = conf(dev2)
    assert cr.a == 1
    assert not cr.item

    cr = conf(dev3)
    assert cr.a == 1
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 0
    assert cr.item.anotherattr == 111

    cr = conf(pp)
    assert cr.a == 1
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_resolved_with_include_for_configitem():
    """Test that most specifig group/env wins"""

    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_include=[g_dev12, pp, dev2], mc_exclude=[g_dev23]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1, dev2=0)
                it.setattr('anotherattr', default=111)
        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert not cr.item

    cr = conf(dev2)
    assert cr.item
    assert cr.item.b == 0

    cr = conf(dev3)
    assert not cr.item

    cr = conf(pp)
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_resolved_with_exclude_for_configitem():
    """Test that most specifig group/env wins"""

    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_include=[g_dev12, pp], mc_exclude=[dev2, g_dev23]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1)
                it.setattr('anotherattr', default=111)
        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert not cr.item

    cr = conf(dev2)
    assert not cr.item

    cr = conf(dev3)
    assert not cr.item

    cr = conf(pp)
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


def test_exclude_include_disjunct_for_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            # Allowed but unnecessary 'mc_exclude'
            with item(mc_include=[g_dev12_3], mc_exclude=[prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', dev1=3, dev2=17, dev3=0, prod=1111)
                it.setattr('anotherattr', default=111)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.a == 1
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 3
    assert cr.item.anotherattr == 111

    cr = conf(dev2)
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 17
    assert cr.item.anotherattr == 111

    cr = conf(dev3)
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 0
    assert cr.item.anotherattr == 111

    cr = conf(pp)
    assert not cr.item

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises, xfail

from .utils.utils import config_error, lineno, assert_lines_in
from utils.messages import mc_required_current_env_expected, mc_required_other_env_expected
from .utils.compare_json import compare_json
from .utils.tstclasses import RootWithAA

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigException, MC_REQUIRED
from ..decorators import named_as, nested_repeatables, required
from ..config_errors import caller_file_line

from ..envs import EnvFactory


def ce(line_num, serr, *lines):
    assert config_error(__file__, line_num, *lines) in serr


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


class item(ConfigItem):
    def __init__(self, mc_include=None, mc_exclude=None):
        super(item, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anattr = MC_REQUIRED
        self.anotherattr = MC_REQUIRED
        self.b = None


class anitem(ConfigItem):
    xx = 1


class anotheritem(ConfigItem):
    xx = 2


@named_as('item')
@required('anitem, anotheritem')
class decorated_item(ConfigItem):
    pass


_include_exclude_for_configitem_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1,
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude_test.item'>": true
}"""

_include_exclude_for_decorated_configitem_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1,
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude_test.decorated_item'>": true
}"""

def test_include_for_configitem_with_mc_required():
    def conf(env):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            with item(mc_include=[dev1, pp]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


def test_include_for_configitem_with_required_decorator():
    def conf(env):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            with decorated_item(mc_include=[dev1, pp]) as it:
                anitem()
                anotheritem()
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_decorated_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.anitem.xx == 1
    assert cr.item.anotheritem.xx == 2


def test_exclude_in_init_and_mc_select_envs_reexclude(capsys):
    def conf(env):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            with item(mc_exclude=[dev2, prod]) as it:
                it.mc_select_envs(exclude=[prod])  # Excluding again is ignored (to avoid extra checking)
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


def test_include_missing_for_configitem(capsys):
    def conf(env, errorline):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            with item(mc_include=[dev1, pp]) as it:
                print("it:", id(it))
                errorline.append(lineno() + 1)
                it.setattr('anattr', g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)
        return cr

    errorline = []
    with raises(ConfigException) as exinfo:
        conf(prod, errorline)

    _sout, serr = capsys.readouterr()
    ce(errorline[0], serr, mc_required_other_env_expected.format(attr='anattr', env=pp))
    assert "There was 1 error when defining item" in str(exinfo.value)


def test_exclude_for_configitem():
    def conf(env):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            with item(mc_exclude=[dev2, prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


class ritem(RepeatableConfigItem):
    def __init__(self, name, mc_include=None, mc_exclude=None):
        super(ritem, self).__init__(mc_key=name, mc_include=mc_include, mc_exclude=mc_exclude)
        self.name = name
        self.anattr = MC_REQUIRED
        self.anotherattr = MC_REQUIRED


@named_as('ritems')
@required('anitem, anotheritem')
class decorated_ritem(RepeatableConfigItem):
    def __init__(self, name, mc_exclude=None, mc_include=None):
        super(decorated_ritem, self).__init__(mc_key=name, mc_exclude=mc_exclude, mc_include=mc_include)
        self.name = name


@nested_repeatables('ritems')
class root(RootWithAA):
    pass


_include_exclude_for_configitem_repeatable_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1,
    "ritems": {}
}"""

def test_include_for_configitem_repeatable_with_mc_required():
    def conf(env):
        with root(env, ef) as cr:
            cr.aa = 1
            with ritem(name='a', mc_include=[dev1, pp]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert cr.ritems == {}
    compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_include_for_configitem_repeatable_with_required_decorater():
    def conf(env):
        with root(env, ef) as cr:
            cr.aa = 1
            with decorated_ritem(name='a', mc_include=[dev1, pp]) as it:
                anitem()
                anotheritem()
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert cr.ritems == {}
    compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.ritems['a'].anitem.xx == 1
    assert cr.ritems['a'].anotheritem.xx == 2


def test_exclude_for_configitem_repeatable():
    def conf(env):
        with root(env, ef) as cr:
            cr.aa = 1
            with ritem(name='a', mc_exclude=[dev2, prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert cr.ritems == {}
    compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_exclude_for_nested_configitem():
    def conf(env):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1


def test_exclude_for_repeatable_nested_configitem():
    def conf(env):
        with root(env, ef) as cr:
            cr.aa = 1
            with ritem(name='a', mc_exclude=[dev2, dev3, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)
                    with item() as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

            with ritem(name='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

            with ritem(name='c', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev3=0, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev3=0, pp=2)

        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33
    assert 'c' not in cr.ritems
    assert len(cr.ritems) == 1

    cr = conf(dev1)
    assert cr.aa == 1
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
            cr.aa = 1
            with ritem(name='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev3=0, pp=2)
                with item(mc_exclude=[pp, dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)
                    with item(mc_exclude=[dev2]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

            with ritem(name='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                with item(mc_exclude=[pp]) as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert len(cr.ritems) == 1

    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = conf(dev1)
    assert cr.aa == 1
    assert len(cr.ritems) == 1

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].item.item.anattr == 2
    assert 'b' not in cr.ritems

    cr = conf(pp)
    assert cr.aa == 1
    assert len(cr.ritems) == 2

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 1
    assert not cr.ritems['a'].item
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 1
    assert not cr.ritems['b'].item

    cr = conf(dev2)
    assert cr.aa == 1
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
    assert cr.aa == 1
    assert len(cr.ritems) == 1

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 0
    assert not cr.ritems['a'].item
    assert 'b' not in cr.ritems
    with raises(KeyError):
        _ = cr.ritems['b']


def test_child_includes_excluded_init(capsys):
    with raises(ConfigException) as exinfo:
        with root(prod, ef):
            with ritem(name='a', mc_exclude=[g_dev12_3, prod]):
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


def test_child_includes_excluded_mc_select_envs():
    with root(prod, ef, aa=1) as cr:
        with ritem(name='a', mc_exclude=[g_dev12_3, prod]):
            with item() as it1:
                it1.mc_select_envs(include=[dev2, prod])  # TODO This is ignored because it is already determined in __init__ that object if excluded
                it1.x = 7

    xfail("TODO: Ideally should give same error as 'test_child_includes_excluded_init'")


def test_exclude_include_overlapping_for_configitem(capsys):
    """Test that most specifig group/env wins"""

    def conf(env):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            with item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev12]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1, dev3=0)
                it.setattr('anotherattr', default=111)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.aa == 1
    assert not cr.item

    cr = conf(dev2)
    assert cr.aa == 1
    assert not cr.item

    cr = conf(dev3)
    assert cr.aa == 1
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 0
    assert cr.item.anotherattr == 111

    cr = conf(pp)
    assert cr.aa == 1
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_ambiguous_single_env_init(capsys):
    """Test include/exclude ambiguity for direct env specification. See include_exclude2_test.py for groups."""

    with raises(ConfigException) as exinfo:
        # No most specific
        with RootWithAA(prod, ef):
            errorline = lineno() + 1
            item(mc_exclude=[dev1], mc_include=[dev1, pp])

    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    ce(errorline, serr, "Env 'dev1' is specified in both include and exclude, with no single most specific group or direct env:\n    from: Env('dev1')")

    with raises(ConfigException) as exinfo:
        # No most specific
        with RootWithAA(prod, ef):
            errorline = lineno() + 1
            item(mc_exclude=[pp, dev1], mc_include=[dev1])

    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    ce(errorline, serr, "Env 'dev1' is specified in both include and exclude, with no single most specific group or direct env:\n    from: Env('dev1')")


def test_exclude_include_overlapping_ambiguous_and_includes_excluded_init(capsys):
    """Test include/exclude ambiguity and already exclude double error"""
    with raises(ConfigException) as exinfo:
        with root(prod, ef):
            with ritem(name='a', mc_exclude=[g_dev12_3, prod]):
                errorline = lineno() + 1
                with item(mc_exclude=[dev2], mc_include=[dev2, prod]) as it1:
                    it1.x = 7

    assert "There were 3 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    print(serr)
    assert_lines_in(
        __file__, errorline, serr,
        "^ConfigError: Env 'dev2' is specified in both include and exclude, with no single most specific group or direct env:",
        "^%(lnum)s",
        "^ConfigError: Env 'dev2' is excluded at an outer level",
        "^%(lnum)s",
        "^ConfigError: Env 'prod' is excluded at an outer level"
    )


def test_exclude_include_overlapping_resolved_with_include_for_configitem():
    """Test that most specifig group/env wins"""

    def conf(env):
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
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
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
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
        with RootWithAA(env, ef) as cr:
            cr.aa = 1
            # Allowed but unnecessary 'mc_exclude'
            with item(mc_include=[g_dev12_3], mc_exclude=[prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', dev1=3, dev2=17, dev3=0, prod=1111)
                it.setattr('anotherattr', default=111)
        return cr

    cr = conf(prod)
    assert cr.aa == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert cr.aa == 1
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


def test_exclude_include_overlapping_for_configitem_with_overridden_mc_select_envs(capsys):
    """Test error is shown correctly if mc_select_envs id overridden"""
    class Item(ConfigItem):
        def mc_select_envs(self, include=None, exclude=None):
            mc_caller_file_name, mc_caller_line_num = caller_file_line()
            super(Item, self).mc_select_envs(include, exclude, mc_caller_file_name, mc_caller_line_num)

    with raises(ConfigException) as exinfo:
        # No most specific
        with RootWithAA(prod, ef):
            with Item() as it:
                errorline = lineno() + 1
                it.mc_select_envs(exclude=[dev1], include=[dev1, pp])

    print("errorline:", errorline)
    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    ce(errorline, serr, "Env 'dev1' is specified in both include and exclude, with no single most specific group or direct env:\n    from: Env('dev1')")


def test_exclude_include_overlapping_ambiguous_and_includes_excluded_init_overridden_file_line(capsys):
    """Test include/exclude ambiguity and already exclude double error giving correct file:line when __init__ is overridden"""
    class iitem(ConfigItem):
        def __init__(self, mc_include, mc_exclude):
            super(iitem, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)

    with raises(ConfigException) as exinfo:
        with root(prod, ef):
            errorline = lineno() + 1
            iitem(mc_exclude=[dev2], mc_include=[dev2, prod])

    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    print(serr)
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: Env 'dev2' is specified in both include and exclude, with no single most specific group or direct env:",
    )

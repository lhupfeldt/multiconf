# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import fail, raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException, ConfigExcludedAttributeError, MC_REQUIRED
from multiconf.decorators import named_as, nested_repeatables, required
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num
from .utils.messages import mc_required_expected
from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithAA

from .include_exclude_classes import McSelectOverrideItem, McSelectOverrideItem2


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


exp_dev1_ambiguous = """Env('dev1') is specified in both include and exclude, with no single most specific group or direct env:
 - from exclude: Env('dev1')
 - from include: Env('dev1')"""


class item(ConfigItem):
    def __init__(self, mc_include=None, mc_exclude=None):
        super().__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anattr = MC_REQUIRED
        self.anotherattr = MC_REQUIRED
        self.b = None


class anitem(ConfigItem):
    xx = 1


class anotheritem(ConfigItem):
    xx = 2


@named_as('item')
@required('anitem', 'anotheritem')
class decorated_item(ConfigItem):
    pass


_include_exclude_for_configitem_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1,
    "item": false,
    "item #Excluded: <class 'test.include_exclude_test.item'>": true
}"""

_include_exclude_for_configitem_all_envs_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "aa": 1,
    "item": {
        "__class__": "item",
        "__id__": 0000,
        "#item does not exist in": "Env('dev2'), Env('dev3'), Env('prod')",
        "anattr": {
            "dev1": 2,
            "dev2": 2,
            "dev3": 2,
            "pp": 1,
            "prod": "MC_REQUIRED"
        },
        "anattr #multiconf attribute": true,
        "anotherattr": {
            "dev1": 1,
            "dev2": "MC_REQUIRED",
            "dev3": "MC_REQUIRED",
            "pp": 2,
            "prod": "MC_REQUIRED"
        },
        "anotherattr #multiconf attribute": true,
        "b": null
    }
}"""

def test_include_for_configitem_with_mc_required():
    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with item(mc_include=[dev1, pp]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True,
                        expected_all_envs_json=_include_exclude_for_configitem_all_envs_expected_json)

    cr = config(dev1).ItemWithAA
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


_include_exclude_for_decorated_configitem_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1,
    "item": false,
    "item #Excluded: <class 'test.include_exclude_test.decorated_item'>": true
}"""

def test_include_for_configitem_with_required_decorator():
    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with decorated_item(mc_include=[dev1, pp]) as it:
                anitem()
                anotheritem()
        return cr

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_decorated_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.item.anitem.xx == 1
    assert cr.item.anotheritem.xx == 2


def test_exclude_in_init_and_mc_select_envs_reexclude():
    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with item(mc_exclude=[dev2, prod]) as it:
                it.mc_select_envs(exclude=[prod])  # Excluding again is ignored (to avoid extra checking)
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)
        return cr

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


def test_include_missing_for_configitem(capsys):
    errorline = []

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAA() as cr:
                cr.aa = 1
                with item(mc_include=[dev1, pp]) as it:
                    print("it:", id(it))
                    errorline.append(next_line_num())
                    it.setattr('anattr', g_dev12_3=2)
                    it.setattr('anotherattr', dev1=1, pp=2)

    _sout, serr = capsys.readouterr()
    ce(errorline[0], serr, mc_required_expected.format(attr='anattr', env=pp))
    assert "There was 1 error when defining item" in str(exinfo.value)


def test_exclude_for_configitem():
    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with item(mc_exclude=[dev2, prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)
        return cr

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


class ritem(RepeatableConfigItem):
    def __init__(self, mc_key, mc_include=None, mc_exclude=None):
        super().__init__(mc_key=mc_key, mc_include=mc_include, mc_exclude=mc_exclude)
        self.name = mc_key
        self.anattr = MC_REQUIRED
        self.anotherattr = MC_REQUIRED


@named_as('ritems')
@required('anitem', 'anotheritem')
class decorated_ritem(RepeatableConfigItem):
    def __init__(self, mc_key, mc_exclude=None, mc_include=None):
        super().__init__(mc_key=mc_key, mc_exclude=mc_exclude, mc_include=mc_include)
        self.name = mc_key


@nested_repeatables('ritems')
class root(ItemWithAA):
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
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=1):
            with ritem('a', mc_include=[dev1, pp]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, pp=2)

    cr = config(prod).root
    assert cr.aa == 1
    assert cr.ritems == {}
    for key, val in cr.ritems.items():
        fail("There should not be any items")
    for key in cr.ritems:
        fail("There should not be any keys")
    for val in cr.ritems.values():
        fail("There should not be any values")
    assert compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = config(dev1).root
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_include_for_configitem_repeatable_with_required_decorater():
    @mc_config(ef, load_now=True)
    def config(rt):
        with root() as cr:
            cr.aa = 1
            with decorated_ritem('a', mc_include=[dev1, pp]) as it:
                anitem()
                anotheritem()
        return cr

    cr = config(prod).root
    assert cr.aa == 1
    assert cr.ritems == {}
    assert compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = config(dev1).root
    assert cr.ritems['a'].anitem.xx == 1
    assert cr.ritems['a'].anotheritem.xx == 2


def test_exclude_for_configitem_repeatable():
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=1):
            with ritem('a', mc_exclude=[dev2, prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('anotherattr', dev1=1, dev3=0, pp=2)

    cr = config(prod).root
    assert cr.aa == 1
    assert cr.ritems == {}
    assert compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = config(dev1).root
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_exclude_for_nested_configitem():
    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)
        return cr

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1


def test_exclude_for_repeatable_nested_configitem():
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=1):
            with ritem('a', mc_exclude=[dev2, dev3, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)
                    with item() as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

            with ritem('b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

            with ritem('c', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev3=0, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev3=0, pp=2)

    cr = config(prod).root
    assert cr.aa == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33
    assert 'c' not in cr.ritems
    assert len(cr.ritems) == 1

    cr = config(dev1).root
    assert cr.aa == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert 'c' in cr.ritems
    assert cr.ritems['c'].anattr == 2
    assert cr.ritems['c'].item.anattr == 2
    assert cr.ritems['c'].item.anotherattr == 1
    assert len(cr.ritems) == 2


def test_exclude_for_repeatable_nested_excludes_configitem():
    @mc_config(ef, load_now=True)
    def config(rt):
        with root() as cr:
            cr.aa = 1
            with ritem('a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev3=0, pp=2)
                with item(mc_exclude=[pp, dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)
                    with item(mc_exclude=[dev2]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

            with ritem('b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                with item(mc_exclude=[pp]) as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

        return cr

    cr = config(prod).root
    assert cr.aa == 1
    assert len(cr.ritems) == 1

    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = config(dev1).root
    assert cr.aa == 1
    assert len(cr.ritems) == 1

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].item.item.anattr == 2
    assert 'b' not in cr.ritems

    cr = config(pp).root
    assert cr.aa == 1
    assert len(cr.ritems) == 2

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 1
    assert not cr.ritems['a'].item
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 1
    assert not cr.ritems['b'].item

    cr = config(dev2).root
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

    cr = config(dev3).root
    assert cr.aa == 1
    assert len(cr.ritems) == 1

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 0
    assert not cr.ritems['a'].item
    assert 'b' not in cr.ritems
    with raises(KeyError):
        _ = cr.ritems['b']


def test_exclude_include_overlapping_for_configitem(capsys):
    """Test that most specifig group/env wins"""

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev12]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1, dev3=0)
                it.setattr('anotherattr', default=111)
        return cr

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.aa == 1
    assert not cr.item

    cr = config(dev2).ItemWithAA
    assert cr.aa == 1
    assert not cr.item

    cr = config(dev3).ItemWithAA
    assert cr.aa == 1
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 0
    assert cr.item.anotherattr == 111

    cr = config(pp).ItemWithAA
    assert cr.aa == 1
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_ambiguous_single_env_init(capsys):
    """Test include/exclude ambiguity for direct env specification. See include_exclude2_test.py for groups."""
    errorline = [None]

    with raises(ConfigException) as exinfo:
        # No most specific
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAA(aa=0):
                errorline[0] = next_line_num()
                item(mc_exclude=[dev1], mc_include=[dev1, pp])

    sout, _serr = capsys.readouterr()
    assert sout == ""

    assert exp_dev1_ambiguous in str(exinfo.value)

    with raises(ConfigException) as exinfo:
        # No most specific
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAA(aa=0):
                errorline[0] = next_line_num()
                item(mc_exclude=[pp, dev1], mc_include=[dev1])

    assert exp_dev1_ambiguous in str(exinfo.value)


def test_exclude_include_overlapping_ambiguous_and_includes_excluded_init(capsys):
    """Test include/exclude ambiguity with repeatable item

    Including an env which was excluded on a parent, on a child, is ignored - no mc checks are done on excluded objects or children.
    """

    errorline = [None]
    exp = "Env('dev2') is specified in both include and exclude, with no single most specific group or direct env:"

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(rt):
            with root(aa=1):
                with ritem('a', mc_exclude=[prod]) as ri:
                    ri.anattr = 1
                    ri.anotherattr = 2
                    errorline[0] = next_line_num()
                    item(mc_exclude=[dev2], mc_include=[dev2, prod])

    sout, _serr = capsys.readouterr()
    assert sout == ""

    assert exp in str(exinfo.value)


def test_exclude_include_overlapping_resolved_with_include_for_configitem():
    """Test that most specifig group/env wins"""

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with item(mc_include=[g_dev12, pp, dev2], mc_exclude=[g_dev23]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1, dev2=0)
                it.setattr('anotherattr', default=111)
        return cr

    cr = config(prod).ItemWithAA
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.item

    cr = config(dev2).ItemWithAA
    assert cr.item
    assert cr.item.b == 0

    cr = config(dev3).ItemWithAA
    assert not cr.item

    cr = config(pp).ItemWithAA
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_resolved_with_exclude_for_configitem():
    """Test that most specifig group/env wins"""

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            with item(mc_include=[g_dev12, pp], mc_exclude=[dev2, g_dev23]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1)
                it.setattr('anotherattr', default=111)
        return cr

    cr = config(prod).ItemWithAA
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.item

    cr = config(dev2).ItemWithAA
    assert not cr.item

    cr = config(dev3).ItemWithAA
    assert not cr.item

    cr = config(pp).ItemWithAA
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


def test_exclude_include_disjunct_for_configitem():
    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 1
            # Allowed but unnecessary 'mc_exclude'
            with item(mc_include=[g_dev12_3], mc_exclude=[prod]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', dev1=3, dev2=17, dev3=0, prod=1111)
                it.setattr('anotherattr', default=111)
        return cr

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1).ItemWithAA
    assert cr.aa == 1
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 3
    assert cr.item.anotherattr == 111

    cr = config(dev2).ItemWithAA
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 17
    assert cr.item.anotherattr == 111

    cr = config(dev3).ItemWithAA
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.b == 0
    assert cr.item.anotherattr == 111

    cr = config(pp).ItemWithAA
    assert not cr.item


def test_exclude_include_overlapping_for_configitem_with_overridden_mc_select_envs(capsys):
    """Test error is shown correctly if mc_select_envs id overridden"""
    errorline = [None]

    with raises(ConfigException) as exinfo:
        # No most specific
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAA():
                with McSelectOverrideItem() as it:
                    errorline[0] = next_line_num()
                    it.mc_select_envs(exclude=[dev1], include=[dev1, pp])

    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    print(serr)

    ce(errorline[0], serr, exp_dev1_ambiguous)

    with raises(ConfigException) as exinfo:
        # No most specific
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAA():
                with McSelectOverrideItem2() as it:
                    errorline[0] = next_line_num()
                    it.mc_select_envs(exclude=[dev1], include=[dev1, pp])

    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    print(serr)

    ce(errorline[0], serr, exp_dev1_ambiguous)


def test_exclude_include_overlapping_ambiguous_and_includes_excluded_init_overridden_file_line():
    """Test include/exclude ambiguity and with overriden __init__ alled from within another __init__
    Not very interresting as there is no resolution of file:line in this scenario, but it that is later implemented, then this would ab important test.
    """

    class iitem(ConfigItem):
        def __init__(self, mc_include, mc_exclude):
            super().__init__(mc_include=mc_include, mc_exclude=mc_exclude)

    with raises(ConfigException) as exinfo:
        class X():
            def __init__(self):
                iitem(mc_exclude=[dev2], mc_include=[dev2, prod])

        @mc_config(ef, load_now=True)
        def config(rt):
            with root(aa=1):
                X()

    exp = "Env('dev2') is specified in both include and exclude, with no single most specific group or direct env:"
    assert exp in str(exinfo.value)


def test_exclude__getattr__():
    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem() as cr:
            with item(mc_exclude=[dev2]) as it:
                it.anattr = 1
                it.anotherattr = 2

    cr = config(prod).ConfigItem
    assert cr.item
    assert cr.item.anattr

    cr = config(dev2).ConfigItem
    assert not cr.item
    with raises(ConfigExcludedAttributeError) as exinfo:
        _ = cr.item.anattr
    exp = "Accessing attribute 'anattr' for Env('dev2') on an excluded config item: Excluded: <class 'test.include_exclude_test.item'>"
    assert exp in str(exinfo.value)


def test_exclude_getattr_env():
    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem() as cr:
            with item(mc_exclude=[dev2]) as it:
                it.anattr = 1
                it.anotherattr = 2

    cr = config(prod).ConfigItem
    assert cr.item
    with raises(ConfigExcludedAttributeError) as exinfo:
        _ = cr.item.getattr('anattr', dev2)
    exp = "Accessing attribute 'anattr' for Env('dev2') on an excluded config item: Excluded: <class 'test.include_exclude_test.item'>"
    assert exp in str(exinfo.value)

    cr = config(dev2).ConfigItem
    assert not cr.item
    with raises(ConfigExcludedAttributeError) as exinfo:
        _ = cr.item.getattr('anattr', dev2)
    exp = "Accessing attribute 'anattr' for Env('dev2') on an excluded config item: Excluded: <class 'test.include_exclude_test.item'>"
    assert exp in str(exinfo.value)


def test_exclude_during_load__getattr__():
    with raises(ConfigExcludedAttributeError):
        @mc_config(ef, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                with item(mc_exclude=[dev2]) as it:
                    it.anattr = 1
                    it.anotherattr = 2
                    with item(mc_exclude=[dev2]) as it:
                        it.anattr = 1
                        it.anotherattr = 2

            assert cr.item.item.anattr


def test_root_no_mc_select_envs():
    """Test that root does not have mc_select_envs (it does not make sense to exclude everything)"""

    with raises(AttributeError) as exinfo:
        @mc_config(ef, load_now=True)
        def config(rt):
            rt.mc_select_envs(exclude=[dev1])

    assert "'McConfigRoot' object has no attribute 'mc_select_envs'" in str(exinfo.value)


def test_mc_select_envs_on_frozen_item(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAA(1) as it1:
                it1.mc_select_envs(exclude=[prod])

            with ConfigItem() as it2:
                errorline[0] = next_line_num()
                it1.mc_select_envs(exclude=[prod])  # Use 'it1' by mistake

    _sout, serr = capsys.readouterr()
    ce(errorline[0], serr, "Calling 'mc_select_envs' on a frozen item.")

    assert "There was 1 error when defining item" in str(exinfo.value)
    assert "ItemWithAA" in str(exinfo.value)

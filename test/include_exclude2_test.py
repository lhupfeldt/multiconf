# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException, ConfigExcludedAttributeError, MC_REQUIRED, McInvalidValue
from multiconf.decorators import required, named_as, nested_repeatables
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num, file_line
from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
dev3 = ef.Env('dev3')
dev4 = ef.Env('dev4')
dev5 = ef.Env('dev5')
g_dev12 = ef.EnvGroup('g_dev12', dev1, dev2)
g_dev34 = ef.EnvGroup('g_dev23', dev3, dev4)
g_dev12_3 = ef.EnvGroup('g_dev12_3', g_dev12, dev3)
g_dev2_34 = ef.EnvGroup('g_dev2_34', dev2, g_dev34)
pp = ef.Env('pp')
prod = ef.Env('prod')
g_ppr = ef.EnvGroup('g_ppr', pp, prod)


class item(ConfigItem):
    def __init__(self, anattr=MC_REQUIRED, mc_include=None, mc_exclude=None):
        super().__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anattr = anattr
        self.anotherattr = None
        self.b = None


@named_as('item')
@required('anitem')
class decorated_item(ConfigItem):
    xx = 3

    def __init__(self, mc_include=None, mc_exclude=None):
        super().__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anotherattr = MC_REQUIRED


_include_exclude_for_configitem_expected_json = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "item": false,
    "item #Excluded: <class 'test.include_exclude2_test.item'>": true
}"""


def test_exclude_include_overlapping_groups_excluded_resolved_with_mc_required():
    @mc_config(ef, load_now=True)
    def config(_):
        """Covers exclude resolve branch"""
        with item(mc_include=[g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34, dev3]) as it:
            it.setattr('anattr', pp=1, g_dev12_3=2)
            it.setattr('b', pp=1, dev2=0)
            it.setattr('anotherattr', default=111, dev5=7)

    cr = config(prod)
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1)
    assert cr.item

    cr = config(dev2)
    assert cr.item
    assert cr.item.b == 0

    cr = config(dev3)
    assert not cr.item

    cr = config(dev4)
    assert not cr.item

    cr = config(pp)
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


_include_exclude_for_configitem_required_decorator_expected_json = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "item": false,
    "item #Excluded: <class 'test.include_exclude2_test.decorated_item'>": true
}"""


def test_exclude_include_overlapping_groups_excluded_resolved_with_required_decorator():
    class anitem(ConfigItem):
        xx = 222

    @mc_config(ef, load_now=True)
    def config(_):
        """Covers exclude resolve branch"""
        with decorated_item(mc_include=[g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34, dev3]) as it:
            anitem()
            it.setattr('anotherattr', default=111, dev5=7)

    cr = config(prod)
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_required_decorator_expected_json, test_excluded=True)

    cr = config(dev1)
    assert cr.item

    cr = config(dev2)
    assert cr.item

    cr = config(dev3)
    assert not cr.item

    cr = config(dev4)
    assert not cr.item

    cr = config(pp)
    assert cr.item.xx == 3
    assert cr.item.anitem.xx == 222
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_groups_included_resolved():
    @mc_config(ef, load_now=True)
    def config(_):
        """Covers include resolve branch"""
        with item(mc_include=[dev3, g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34]) as it:
            it.setattr('anattr', pp=1, g_dev12_3=2, dev5=117, g_ppr=4)

    cr = config(prod)
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = config(dev1)
    assert cr.item

    cr = config(dev2)
    assert cr.item

    cr = config(dev3)
    assert cr.item

    cr = config(dev4)
    assert not cr.item

    cr = config(pp)
    assert cr.item
    assert cr.item.anattr == 1


_exclude_include_overlapping_groups_excluded_unresolved_expected_ex1 = """
ConfigException: Env('dev2') is specified in both include and exclude, with no single most specific group or direct env:
 - from exclude: EnvGroup('g_dev2_34') {
   Env('dev2'),
   EnvGroup('g_dev23') {
      Env('dev3'),
      Env('dev4')
   }
}
 - from include: EnvGroup('g_dev12_3') {
   EnvGroup('g_dev12') {
      Env('dev1'),
      Env('dev2')
   },
   Env('dev3')
}
Error in config for Env('dev2') above.

""".lstrip()

_exclude_include_overlapping_groups_excluded_unresolved_expected_ex2 = """
ConfigException: Env('dev3') is specified in both include and exclude, with no single most specific group or direct env:
 - from exclude: EnvGroup('g_dev23') {
   Env('dev3'),
   Env('dev4')
}
 - from include: EnvGroup('g_dev12_3') {
   EnvGroup('g_dev12') {
      Env('dev1'),
      Env('dev2')
   },
   Env('dev3')
}
Error in config for Env('dev3') above.

""".lstrip()

def test_exclude_include_overlapping_groups_excluded_unresolved_init(capsys):
    errorline = [None]

    @mc_config(ef)
    def config(_):
        errorline[0] = next_line_num()
        item(anattr=1, mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34])
    with raises(ConfigException):
        config.load(error_next_env=True)

    _sout, serr = capsys.readouterr()
    assert _exclude_include_overlapping_groups_excluded_unresolved_expected_ex1 in serr
    assert serr.endswith(_exclude_include_overlapping_groups_excluded_unresolved_expected_ex2)


_exclude_include_overlapping_groups_excluded_unresolved_init_reversed_ex = """
Env('dev2') is specified in both include and exclude, with no single most specific group or direct env:
 - from exclude: EnvGroup('g_dev12_3') {
   EnvGroup('g_dev12') {
      Env('dev1'),
      Env('dev2')
   },
   Env('dev3')
}
 - from include: EnvGroup('g_dev2_34') {
   Env('dev2'),
   EnvGroup('g_dev23') {
      Env('dev3'),
      Env('dev4')
   }
}""".strip()

def test_exclude_include_overlapping_groups_excluded_unresolved_init_reversed():
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            errorline[0] = next_line_num()
            item(anattr=1, mc_include=[g_dev34, g_dev2_34], mc_exclude=[g_dev12_3, pp])

    assert _exclude_include_overlapping_groups_excluded_unresolved_init_reversed_ex in str(exinfo.value)


_exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs_expected = """
ConfigError: Env('dev2') is specified in both include and exclude, with no single most specific group or direct env:
 - from exclude: EnvGroup('g_dev2_34') {
   Env('dev2'),
   EnvGroup('g_dev23') {
      Env('dev3'),
      Env('dev4')
   }
}
 - from include: EnvGroup('g_dev12_3') {
   EnvGroup('g_dev12') {
      Env('dev1'),
      Env('dev2')
   },
   Env('dev3')
}
""".strip()

def test_exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with item(anattr=1) as it:
                errorline[0] = next_line_num()
                it.mc_select_envs(include=[g_dev12_3, pp], exclude=[g_dev34, g_dev2_34])

    _sout, serr = capsys.readouterr()
    assert serr.startswith(file_line(__file__, errorline[0]))
    assert _exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs_expected in serr
    assert "There was 1 error when defining item" in str(exinfo.value)


_exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs_reversed_expected = """
ConfigError: Env('dev2') is specified in both include and exclude, with no single most specific group or direct env:
 - from exclude: EnvGroup('g_dev12_3') {
   EnvGroup('g_dev12') {
      Env('dev1'),
      Env('dev2')
   },
   Env('dev3')
}
 - from include: EnvGroup('g_dev2_34') {
   Env('dev2'),
   EnvGroup('g_dev23') {
      Env('dev3'),
      Env('dev4')
   }
}
""".strip()

def test_exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs_reversed(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with item(anattr=1) as it:
                errorline[0] = next_line_num()
                it.mc_select_envs(include=[g_dev34, g_dev2_34], exclude=[g_dev12_3, pp])

    _sout, serr = capsys.readouterr()
    assert serr.startswith(file_line(__file__, errorline[0]))
    assert _exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs_reversed_expected in serr


def test_exclude_include_overlapping_groups_dev3_finally_resolved_dev2_unresolved():
    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            item(anattr=1, mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34, dev3])

    expected = "Env('dev2') is specified in both include and exclude, with no single most specific group or direct env:"
    assert expected in str(exinfo.value)


def test_exclude_include_overlapping_groups_dev3_dev2_finally_resolved():
    @mc_config(ef, load_now=True)
    def config(_):
        with item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34, dev3, dev2]) as it:
            it.setattr('anattr', g_dev12_3=123, pp=1)


def test_exclude_include_error_before_exclude(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with item() as it:
                errorline[0] = next_line_num()
                it.setattr('_a', default=7)
                it.mc_select_envs(exclude=[prod])

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_a' on a config item. Atributes starting with '_' cannot be set using item.setattr. Use assignment instead."
    assert ce(errorline[0], msg) == serr


def test_exclude_include_iter_all(capsys):
    @nested_repeatables('RepeatableItems')
    class item(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with item():
            with RepeatableItemWithAA(mc_key=1, aa=1) as r1:
                ItemWithAA(aa=11)
            with RepeatableItemWithAA(mc_key=2, aa=2) as r2:
                r2.mc_select_envs(exclude=[prod])
                ItemWithAA(aa=12)

    _sout, serr = capsys.readouterr()
    cr = config(pp)
    for key, rit in cr.item.RepeatableItems.all_items.items():
        assert rit.aa == key
        assert rit.ItemWithAA.aa == 10 + key

    cr = config(prod)
    for key, rit in cr.item.RepeatableItems.all_items.items():
        if key == 1:
            assert rit.aa == 1
            assert rit.ItemWithAA.aa == 11
        if key == 2:
            with raises(ConfigExcludedAttributeError) as exinfo:
                errorline = next_line_num()
                rit.ItemWithAA.aa

    exinfo.value == "Accessing attribute 'aa' for Env('prod') on an excluded config item: Excluded: <class 'test.utils.tstclasses.ItemWithAA'>"


def test_exclude_include_iter_2_level_all_env_attr_items(capsys):
    """Test iteration over repeatable with excludede items and usage of `env_attr_items` where first defined env is excluded"""

    @nested_repeatables('RepItemsOuter')
    class item(ConfigItem):
        pass

    @named_as('RepItemsOuter')
    @nested_repeatables('RepItemsMiddle')
    class RepItemsOuter(RepeatableItemWithAA):
        pass

    @named_as('RepItemsMiddle')
    @nested_repeatables('RepItemsInner')
    class RepItemsMiddle(RepeatableItemWithAA):
        pass

    @named_as('RepItemsInner')
    class RepItemsInner(RepeatableItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with item():
            with RepItemsOuter(mc_key=1, aa=11) as r2:
                r2.mc_select_envs(exclude=[dev1])
                with RepItemsMiddle(mc_key=2, aa=22):
                    with RepItemsInner(mc_key=3, aa=33):
                        with ItemWithAA(aa=44):
                            ItemWithAA(aa=55)

    def _test(cr):
        for keyo, rito in cr.item.RepItemsOuter.all_items.items():
            print('rito:', bool(rito))
            for keym, ritm in rito.RepItemsMiddle.all_items.items():
                print('ritm:', bool(ritm))
                for keyi, riti in ritm.RepItemsInner.all_items.items():
                    print('riti:', bool(riti))
                    for env, val in riti.attr_env_items('aa'):
                        # print(env, val)
                        assert val == McInvalidValue.MC_NO_VALUE if env == dev1 else 33

                    for env, val in riti.ItemWithAA.attr_env_items('aa'):
                        # print(env, val)
                        assert val == McInvalidValue.MC_NO_VALUE if env == dev1 else 44

    _sout, serr = capsys.readouterr()
    _test(config(pp))
    _test(config(prod))

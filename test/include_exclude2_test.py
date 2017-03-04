# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises, xfail

from .utils.utils import config_error, next_line_num, assert_lines_in
from .utils.compare_json import compare_json

from multiconf import mc_config, ConfigItem, ConfigException, MC_REQUIRED
from multiconf.decorators import required, named_as

from multiconf.envs import EnvFactory

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
        super(item, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anattr = anattr
        self.anotherattr = None
        self.b = None


@named_as('item')
@required('anitem')
class decorated_item(ConfigItem):
    xx = 3

    def __init__(self, mc_include=None, mc_exclude=None):
        super(decorated_item, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anotherattr = MC_REQUIRED


_include_exclude_for_configitem_expected_json = """{
    "__class__": "_ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "item": false,
    "item #Excluded: <class 'test.include_exclude2_test.item'>": true
}"""


def test_exclude_include_overlapping_groups_excluded_resolved_with_mc_required():
    @mc_config(ef)
    def conf(_):
        """Covers exclude resolve branch"""
        with item(mc_include=[g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34, dev3]) as it:
            it.setattr('anattr', pp=1, g_dev12_3=2)
            it.setattr('b', pp=1, dev2=0)
            it.setattr('anotherattr', default=111, dev5=7)

    cr = ef.config(prod)
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = ef.config(dev1)
    assert cr.item

    cr = ef.config(dev2)
    assert cr.item
    assert cr.item.b == 0

    cr = ef.config(dev3)
    assert not cr.item

    cr = ef.config(dev4)
    assert not cr.item

    cr = ef.config(pp)
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111


_include_exclude_for_configitem_required_decorator_expected_json = """{
    "__class__": "_ConfigRoot",
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

    @mc_config(ef)
    def conf(_):
        """Covers exclude resolve branch"""
        with decorated_item(mc_include=[g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34, dev3]) as it:
            anitem()
            it.setattr('anotherattr', default=111, dev5=7)

    cr = ef.config(prod)
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_required_decorator_expected_json, test_excluded=True)

    cr = ef.config(dev1)
    assert cr.item

    cr = ef.config(dev2)
    assert cr.item

    cr = ef.config(dev3)
    assert not cr.item

    cr = ef.config(dev4)
    assert not cr.item

    cr = ef.config(pp)
    assert cr.item.xx == 3
    assert cr.item.anitem.xx == 222
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_groups_included_resolved():
    @mc_config(ef)
    def conf(_):
        """Covers include resolve branch"""
        with item(mc_include=[dev3, g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34]) as it:
            it.setattr('anattr', pp=1, g_dev12_3=2, dev5=117, g_ppr=4)

    cr = ef.config(prod)
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = ef.config(dev1)
    assert cr.item

    cr = ef.config(dev2)
    assert cr.item

    cr = ef.config(dev3)
    assert cr.item

    cr = ef.config(dev4)
    assert not cr.item

    cr = ef.config(pp)
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

    with raises(ConfigException) as exinfo:
        @mc_config(ef, error_next_env=True)
        def _(_):
            errorline[0] = next_line_num()
            item(anattr=1, mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34])

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
        @mc_config(ef)
        def _(_):
            errorline[0] = next_line_num()
            item(anattr=1, mc_include=[g_dev34, g_dev2_34], mc_exclude=[g_dev12_3, pp])

    assert _exclude_include_overlapping_groups_excluded_unresolved_init_reversed_ex in str(exinfo.value)


def test_exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs(capsys):
    xfail("TODO implement test")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with item(anattr=1) as it:
                errorline[0] = next_line_num()
                it.mc_select_envs(include=[g_dev12_3, pp], exclude=[g_dev34, g_dev2_34])

    assert "There were 2 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    assert _exclude_include_overlapping_groups_excluded_unresolved_expected_ex % dict(file=__file__, line=errorline[0]) in serr


def test_exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs_reversed(capsys):
    xfail("TODO implement test")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with item(anattr=1) as it:
                errorline[0] = next_line_num()
                it.mc_select_envs(include=[g_dev34, g_dev2_34], exclude=[g_dev12_3, pp])

    assert "There were 2 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    assert _exclude_include_overlapping_groups_excluded_unresolved_expected_ex % dict(file=__file__, line=errorline[0]) in serr


def test_exclude_include_overlapping_groups_dev3_finally_resolved_dev2_unresolved(capsys):
    xfail("TODO implement test")
    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            item(anattr=1, mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34, dev3])

    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    expected = "ConfigError: Env 'dev2' is specified in both include and exclude, with no single most specific group or direct env:"
    assert expected in serr


def test_exclude_include_overlapping_groups_dev3_dev2_finally_resolved():
    @mc_config(ef)
    def _(_):
        with item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34, dev3, dev2]) as it:
            it.setattr('anattr', g_dev12_3=123, pp=1)


def test_exclude_include_error_before_exclude(capsys):
    xfail("TODO implement test")
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with item() as it:
                errorline[0] = next_line_num()
                it.setattr('_a', 7)
                it.mc_select_envs(exclude=[prod])
                raise Exception()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_a' on a config item. Atributes starting with '_' can not be set using item.setattr. Use assignment instead."
    assert ce(errorline[0], msg) == serr

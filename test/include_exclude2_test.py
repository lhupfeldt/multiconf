# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, assert_lines_in
from .utils.compare_json import compare_json

from .. import ConfigRoot, ConfigItem, ConfigException, MC_REQUIRED
from ..decorators import required, named_as

from ..envs import EnvFactory

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
    def __init__(self, mc_include=None, mc_exclude=None):
        super(item, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anattr = MC_REQUIRED
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
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude2_test.item'>": true
}"""


def test_exclude_include_overlapping_groups_excluded_resolved_with_mc_required():
    def conf(env):
        """Covers exclude resolve branch"""
        with ConfigRoot(env, ef) as cr:
            with item(mc_include=[g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34, dev3]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1, dev2=0)
                it.setattr('anotherattr', default=111, dev5=7)
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


_include_exclude_for_configitem_required_decorator_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude2_test.decorated_item'>": true
}"""


def test_exclude_include_overlapping_groups_excluded_resolved_with_required_decorator():
    class anitem(ConfigItem):
        xx = 222

    def conf(env):
        """Covers exclude resolve branch"""
        with ConfigRoot(env, ef) as cr:
            with decorated_item(mc_include=[g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34, dev3]) as it:
                anitem()
                it.setattr('anotherattr', default=111, dev5=7)
        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_required_decorator_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert not cr.item

    cr = conf(dev2)
    assert cr.item

    cr = conf(dev3)
    assert not cr.item

    cr = conf(pp)
    assert cr.item.xx == 3
    assert cr.item.anitem.xx == 222
    assert cr.item.anotherattr == 111


def test_exclude_include_overlapping_groups_included_resolved():
    def conf(env):
        """Covers include resolve branch"""
        with ConfigRoot(env, ef) as cr:
            with item(mc_include=[dev3, g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2, dev5=117, g_ppr=4)
        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert not cr.item

    cr = conf(dev2)
    assert cr.item

    cr = conf(dev3)
    assert cr.item

    cr = conf(dev4)
    assert not cr.item

    cr = conf(pp)
    assert cr.item
    assert cr.item.anattr == 1


exclude_include_overlapping_groups_excluded_unresolved = """
File "%(file)s", line %(line)d
ConfigError: Env 'dev2' is specified in both include and exclude, with no single most specific group or direct env:
    from: EnvGroup('g_dev12_3') {
     EnvGroup('g_dev12') {
       Env('dev1'),
       Env('dev2')
  },
     Env('dev3')
}
    from: EnvGroup('g_dev2_34') {
     Env('dev2'),
     EnvGroup('g_dev23') {
       Env('dev3'),
       Env('dev4')
  }
}
File "%(file)s", line %(line)d
ConfigError: Env 'dev3' is specified in both include and exclude, with no single most specific group or direct env:
    from: EnvGroup('g_dev23') {
     Env('dev3'),
     Env('dev4')
}
    from: EnvGroup('g_dev12_3') {
     EnvGroup('g_dev12') {
       Env('dev1'),
       Env('dev2')
  },
     Env('dev3')
}
    from: EnvGroup('g_dev2_34') {
     Env('dev2'),
     EnvGroup('g_dev23') {
       Env('dev3'),
       Env('dev4')
  }
}
""".strip()

def test_exclude_include_overlapping_groups_excluded_unresolved(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            errorline = lineno() + 1
            item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34])

    print(str(exinfo.value))
    assert "There were 2 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    print(serr)
    expected = exclude_include_overlapping_groups_excluded_unresolved % dict(file=__file__, line=errorline)
    print('---------------------')
    print(expected)
    assert expected in serr


def test_exclude_include_overlapping_groups_excluded_unresolved_reversed(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            errorline = lineno() + 1
            item(mc_include=[g_dev34, g_dev2_34], mc_exclude=[g_dev12_3, pp])

    assert "There were 2 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    assert exclude_include_overlapping_groups_excluded_unresolved % dict(file=__file__, line=errorline) in serr


def test_exclude_include_overlapping_groups_excluded_unresolved_mc_select_envs(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with item() as it:
                errorline = lineno() + 1
                it.mc_select_envs(include=[g_dev12_3, pp], exclude=[g_dev34, g_dev2_34])

    assert "There were 2 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    assert exclude_include_overlapping_groups_excluded_unresolved % dict(file=__file__, line=errorline) in serr


def test_exclude_include_overlapping_groups_excluded_unresolved_reversed_mc_select_envs(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with item() as it:
                errorline = lineno() + 1
                it.mc_select_envs(include=[g_dev34, g_dev2_34], exclude=[g_dev12_3, pp])
                raise Exception()

    assert "There were 2 errors when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    assert exclude_include_overlapping_groups_excluded_unresolved % dict(file=__file__, line=errorline) in serr


def test_exclude_include_overlapping_groups_dev3_finally_resolved_dev2_unresolved(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34, dev3])

    assert "There was 1 error when defining item" in str(exinfo.value)
    _sout, serr = capsys.readouterr()
    expected = "ConfigError: Env 'dev2' is specified in both include and exclude, with no single most specific group or direct env:"
    assert expected in serr


def test_exclude_include_overlapping_groups_dev3_dev2_finally_resolved():
    with ConfigRoot(prod, ef):
        item(mc_include=[g_dev12_3, pp], mc_exclude=[g_dev34, g_dev2_34, dev3, dev2])


def test_exclude_include_error_before_exclude(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with item() as it:
                errorline = lineno() + 1
                it.setattr('_a', 7)
                it.mc_select_envs(exclude=[prod])
                raise Exception()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_a' on a config item. Atributes starting with '_' can not be set using item.setattr. Use assignment instead."
    assert ce(errorline, msg) == serr

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException, MC_REQUIRED
from multiconf.decorators import nested_repeatables
from multiconf.envs import EnvFactory

from .utils.utils import replace_ids, config_error, next_line_num
from .utils.messages import setattr_not_defined_in_init_expected


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_pp = EnvFactory()
pp2 = ef2_prod_pp.Env('pp')
prod2 = ef2_prod_pp.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


@nested_repeatables('RepeatableStrictItems')
class strict_project(ConfigItem):
    def __init__(self):
        super().__init__()
        self.a = None
        self.b = MC_REQUIRED


class StrictItem(ConfigItem):
    def __init__(self):
        super().__init__()
        self.x = MC_REQUIRED
        self.y = None


class RepeatableStrictItem(RepeatableConfigItem):
    def __init__(self, mc_key):
        super().__init__(mc_key=mc_key)
        self.x = None
        self.y = MC_REQUIRED


def test_setunknown_strict_ok():
    @mc_config(ef2_prod_pp, load_now=True)
    def config(root):
        with strict_project() as sp:
            sp.b = 1
            sp.setattr('c', mc_set_unknown=True, default=2)

            with StrictItem() as si:
                si.x = 1
                si.setattr('z', mc_set_unknown=True, default='yes')

            with RepeatableStrictItem('a') as rsi:
                rsi.y = 1
                rsi.setattr('z', mc_set_unknown=True, default='yes')
        return sp, si, rsi

    cfg = config(prod2)
    sp, si, rsi = cfg.mc_config_result
    assert sp.c == 2
    assert si.z == 'yes'
    assert rsi.z == 'yes'


def test_setattr_strict_bad(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                errorline[0] = next_line_num()
                sp.c = 1

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], setattr_not_defined_in_init_expected.format('c'))

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                errorline[0] = next_line_num()
                sp.setattr('c', default=1)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], setattr_not_defined_in_init_expected.format('c'))

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                with StrictItem() as si:
                    errorline[0] = next_line_num()
                    si.z = 1

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], setattr_not_defined_in_init_expected.format('z'))

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                with StrictItem() as si:
                    errorline[0] = next_line_num()
                    si.setattr('z', prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], setattr_not_defined_in_init_expected.format('z'))

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                with RepeatableStrictItem('a') as rsi:
                    errorline[0] = next_line_num()
                    rsi.z = 1

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], setattr_not_defined_in_init_expected.format('z'))

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                with RepeatableStrictItem('b') as rsi:
                    errorline[0] = next_line_num()
                    rsi.setattr('z', prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], setattr_not_defined_in_init_expected.format('z'))


_setunknown_strict_bad_expected = """Attempting to use 'mc_set_unknown' to set attribute '{}' which already exists."""

def test_setunknown_strict_bad(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                errorline[0] = next_line_num()
                sp.setattr('b', mc_set_unknown=True, default=1)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], _setunknown_strict_bad_expected.format('b'))

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                with StrictItem() as si:
                    errorline[0] = next_line_num()
                    si.setattr('y', mc_set_unknown=True, prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], _setunknown_strict_bad_expected.format('y'))

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(root):
            with strict_project() as sp:
                with RepeatableStrictItem('b') as rsi:
                    errorline[0] = next_line_num()
                    rsi.setattr('y', mc_set_unknown=True, prod=1, default=2)

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], _setunknown_strict_bad_expected.format('y'))

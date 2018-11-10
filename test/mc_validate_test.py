# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException, MC_REQUIRED
from multiconf.decorators import nested_repeatables
from multiconf.envs import EnvFactory

from .utils.messages import setattr_not_defined_in_init_expected, config_error_mc_required_expected
from .utils.tstclasses import ItemWithAA
from .utils.utils import config_error, next_line_num, replace_ids, lines_in, start_file_line


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
ef.EnvGroup('g_prod_like', prod, pp)


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


@nested_repeatables('children')
class nc_aa_root(ItemWithAA):
    pass


def test_mc_validate_assignment():
    @nested_repeatables('children')
    class root(ItemWithAA):
        def mc_validate(self):
            self.aa = 7

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            pass

    rt = config(prod).root
    assert rt.aa == 7


def test_mc_validate_mc_set_unknown():
    @nested_repeatables('children')
    class root(ConfigItem):
        def mc_validate(self):
            self.setattr('y', default=7, mc_set_unknown=True)

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            pass

    rt = config(prod).root
    assert rt.y == 7


def test_mc_validate_assign_attribute_not_defined_in_init(capsys):
    errorline = [None]

    class item(ConfigItem):
        def mc_validate(self):
            errorline[0] = next_line_num()
            self.aa = 7

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with ConfigItem():
                item()

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], setattr_not_defined_in_init_expected.format('aa'))


def test_user_mc_validate_error():
    class item(ConfigItem):
        def mc_validate(self):
            raise Exception("Error in item mc_validate")

    with raises(Exception) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with ConfigItem():
                item()

    assert str(exinfo.value) == "Error in item mc_validate"


def test_mc_required_attribute_resolved_after_mc_validate(capsys):
    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

        def mc_init(self):
            super().mc_init()
            self.abcd = 7

        def mc_validate(self):
            super().mc_validate()
            self.ijkl = 7

    @mc_config(ef, load_now=True)
    def config(_):
        with item() as ii:
            ii.setattr('efgh', default=7)

    it = config(prod).item
    assert it.abcd == 7
    assert it.efgh == 7
    assert it.ijkl == 7


def test_mc_required_attribute_missing_after_mc_validate(capsys):
    errorline = [None]

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED
            errorline[0] = next_line_num()
            self.mnop = MC_REQUIRED

        def mc_init(self):
            super().mc_init()
            self.abcd = 7

        def mc_validate(self):
            super().mc_validate()
            self.ijkl = 7

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with item() as ii:
                ii.setattr('efgh', default=7)

    _sout, serr = capsys.readouterr()
    print(serr)
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='mnop', env=pp),
    )

    assert 'abcd' not in serr
    assert 'efgh' not in serr
    assert 'ijkl' not in serr

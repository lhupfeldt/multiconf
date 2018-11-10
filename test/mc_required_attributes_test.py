# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, MC_REQUIRED, ConfigException
from multiconf.envs import EnvFactory

from .utils.utils import next_line_num, line_num, lines_in, start_file_line, local_func
from .utils.messages import config_error_mc_required_expected


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


def test_required_attributes_inherited_ok():
    class root(ConfigItem):
        def __init__(self):
            super().__init__()
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

    class root2(root):
        def __init__(self):
            super().__init__()
            self.someattr2 = MC_REQUIRED
            self.someotherattr2 = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config(_):
        with root2() as cr:
            cr.anattr = 1
            cr.anotherattr = 2
            cr.someattr2 = 3
            cr.someotherattr2 = 4

    cr = config(prod).root2

    assert cr.anattr == 1
    assert cr.anotherattr == 2
    assert cr.someattr2 == 3
    assert cr.someotherattr2 == 4


def test_required_attributes_inherited_missing(capsys):
    errorline1 = [None]
    errorline2 = [None]
    errorline3 = [None]
    errorline_exit = [None]

    class root(ConfigItem):
        def __init__(self):
            super().__init__()
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

    class root2(root):
        def __init__(self):
            super().__init__()
            self.someattr2 = MC_REQUIRED
            self.someotherattr2 = MC_REQUIRED

    @mc_config(ef)
    def config(_):
        with root2() as cr:
            errorline1[0] = next_line_num()
            cr.setattr('anattr', prod=1)
            errorline2[0] = next_line_num()
            cr.setattr('someattr2', prod=3)
            errorline3[0] = next_line_num()
            cr.setattr('someotherattr2', pp=4)
            errorline_exit[0] = line_num()

    with raises(ConfigException):
        config.load(error_next_env=True)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline1[0]),
        config_error_mc_required_expected.format(attr='anattr', env=pp),
        start_file_line(__file__, errorline2[0]),
        config_error_mc_required_expected.format(attr='someattr2', env=pp),
        start_file_line(__file__, errorline3[0]),
        config_error_mc_required_expected.format(attr='someotherattr2', env=prod),
        # 'anotherattr' will not be verified because it might get a value in mc_init
        # which is not called when there are errors in 'with' block
    )


def test_multiple_required_attributes_missing_for_configitem(capsys):
    errorline1 = [None]
    errorline_exit = [None]

    class root(ConfigItem):
        pass

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with root():
                with item() as ii:
                    errorline1[0] = next_line_num()
                    ii.setattr('efgh', prod=7)
                    errorline_exit[0] = line_num()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline1[0]),
        config_error_mc_required_expected.format(attr='efgh', env=pp),
        # remaining will not be checked
    )


def test_error_freezing_previous_sibling__validation(capsys):
    class inner(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = MC_REQUIRED

    with raises(Exception) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with ConfigItem():
                inner()
                inner()

    # This error is generated before the MC_REQUIRED check, ok as long as we get en error
    exp = "Repeated non repeatable conf item: 'inner': <class 'test.mc_required_attributes_test.{}inner'>"
    assert str(exinfo.value) == exp.format(local_func())

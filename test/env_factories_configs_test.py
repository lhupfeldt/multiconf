# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


# Test that different configurations can use different EnvFactories without interference, i.e,
# there is no unintended static information in the envs module

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.messages import already_printed_msg
from .utils.utils import next_line_num, lines_in, start_file_line, replace_ids


def _names(groups):
    return [gg.name for gg in groups]


def _lookup_order(env):
    act = []
    for gg in env.lookup_order:
        act.append((gg.name, _names(gg.ambiguous[env.name])))
    return act


class item(ConfigItem):
    def __init__(self):
        super().__init__()
        self.aa = MC_REQUIRED
        self.bb = MC_REQUIRED

    def mc_init(self):
        # TODO
        self.bb = 111


def test_env_factories_ef1():
    ef = EnvFactory()

    dev1 = ef.Env('dev1')
    dev2 = ef.Env('dev2')
    g_dev = ef.EnvGroup('g_dev', dev1, dev2)

    pp = ef.Env('pp')
    prod = ef.Env('prod')

    @mc_config(ef, load_now=True)
    def config(root):
        with item() as it:
            it.setattr('aa', default=13)

    cfg = config(prod)
    assert cfg.item.aa == 13
    cfg = config(dev1)
    assert cfg.item.aa == 13

    @mc_config(ef, load_now=True)
    def config(root):
        with item() as it:
            it.setattr('aa', dev1=1, dev2=2, pp=3, prod=4)
    cfg = config(dev1)

    assert cfg.item.aa == 1
    assert cfg.item.bb == 111


_env_factories_ef1_errors_expected_ex = """There was 1 error when defining item: {
    "__class__": "item #as: 'item', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "dev1"
    },
    "aa": 1,
    "bb": "MC_REQUIRED"
}""" + already_printed_msg

def test_env_factories_ef1_errors(capsys):
    ef = EnvFactory()

    dev1 = ef.Env('dev1')
    dev2 = ef.Env('dev2')
    g_dev = ef.EnvGroup('g_dev', dev1, dev2)

    pp = ef.Env('pp')
    prod = ef.Env('prod')

    errorline = [None]
    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(root_conf):
            with item() as it:
                errorline[0] = next_line_num()
                it.setattr('aa', dev1=1, dev2=2, g_prod=4)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: No such Env or EnvGroup: 'g_prod'",
    )
    assert replace_ids(str(exinfo.value), False) == _env_factories_ef1_errors_expected_ex

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(root_conf):
            with item() as it:
                errorline[0] = next_line_num()
                it.setattr('aa', dev1=1, dev2=2, dev3=3, pp=4, prod=5)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: No such Env or EnvGroup: 'dev3'",
    )


def test_env_factories_ef2():
    ef = EnvFactory()

    dev1 = ef.Env('dev1')
    dev2 = ef.Env('dev2')
    dev3 = ef.Env('dev3')
    g_dev = ef.EnvGroup('g_dev', dev1, dev2, dev3)

    pp = ef.Env('pp')
    prod = ef.Env('prod')
    g_prod = ef.EnvGroup('g_prod', pp, prod)

    @mc_config(ef, load_now=True)
    def config(root):
        with item() as it:
            it.setattr('aa', default=13)

    conf = config(prod)
    assert conf.item.aa == 13

    @mc_config(ef)
    def config(root):
        with ConfigItem():
            with item() as it:
                it.setattr('aa', dev1=1, g_dev=7, g_prod=17)

    config.load()

    conf = config(prod)
    it = conf.ConfigItem.item
    assert it.aa == 17
    assert it.bb == 111

    conf = config(dev1)
    it = conf.ConfigItem.item
    assert it.aa == 1
    assert it.bb == 111

    conf = config(dev2)
    assert conf.ConfigItem.item.aa == 7

    conf = config(dev3)
    assert conf.ConfigItem.item.aa == 7


_env_factories_ef2_errors_expected_ex = """There was 1 error when defining item: {
    "__class__": "item #as: 'item', id: 0000",
    "aa": 1,
    "bb": 111
}""" + already_printed_msg

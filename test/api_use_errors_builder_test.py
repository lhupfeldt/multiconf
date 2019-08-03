# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigBuilder, ConfigException
from multiconf.envs import EnvFactory

from .utils.utils import api_error, config_error, next_line_num


ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


def capie(line_num, *lines):
    return api_error(__file__, line_num, *lines)


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def test_setattr_to_attribute_underscore_attribute_builder(capsys):
    errorline = [None]

    class CB(ConfigBuilder):
        def mc_build(self):
            pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with CB() as ci:
                errorline[0] = next_line_num()
                ci.setattr('_b', default=7)

    _sout, serr = capsys.readouterr()
    exp = """Trying to set attribute '_b' on a config item. Atributes starting with '_' cannot be set using item.setattr. Use assignment instead."""
    assert serr == ce(errorline[0], exp)

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigException
from multiconf.envs import EnvFactory

from .utils.utils import next_line_num, replace_ids, config_error


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


def test_setattr_root():
    @mc_config(ef, load_now=True)
    def config(root):
        root.setattr('aa', default=1, prod=2, mc_set_unknown=True)

    cr = config(prod)
    assert cr.aa == 2

    cr = config(pprd)
    assert cr.aa == 1


_setattr_strict_bad_expected = """All attributes must be defined in __init__ or set with 'mc_set_unknown'. Attempting to set attribute '{}' which does not exist."""

def test_assignment_root(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(root):
            errorline[0] = next_line_num()
            root.aa = 1

    _sout, serr = capsys.readouterr()
    assert replace_ids(serr) == ce(errorline[0], _setattr_strict_bad_expected.format('aa'))


def test_env_root():
    @mc_config(ef, load_now=True)
    def config(root):
        pass

    cr = config(prod)
    assert cr.env == prod


_repr_root_expected = """{
    "__class__": "McConfigRoot #as: 'McConfigRoot', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 2
}"""

def test_repr_root():
    @mc_config(ef, load_now=True)
    def config(root):
        root.setattr('aa', default=1, prod=2, mc_set_unknown=True)

    cr = config(prod)
    assert replace_ids(repr(cr), False) == _repr_root_expected

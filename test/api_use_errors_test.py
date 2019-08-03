# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException, ConfigApiException
from multiconf.envs import EnvFactory

from .utils.utils import api_error, config_error, next_line_num


ef2_prod_pp = EnvFactory()
pp2 = ef2_prod_pp.Env('pp')
prod2 = ef2_prod_pp.Env('prod')


_expected_ex_msg = "An error was detected trying to get attribute '%s' on class 'inner'"
_extra_stderr = """
    - You did not initailize the parent class (parent __new__ method has not been called)."""


def capie(line_num, *lines):
    return api_error(__file__, line_num, *lines)


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


class root(ConfigItem):
    pass


def test_setattr_multiconf_private_attribute(capsys):
    errorline = [None]

    class inner(ConfigItem):
        pass

    msg = """Trying to set attribute '_mc_whatever' on a config item. Atributes starting with '_mc' are reserved for multiconf internal usage."""

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with root() as cr:
                errorline[0] = next_line_num()
                cr.setattr('_mc_whatever', default=1)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], msg)

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with root() as cr:
                with inner() as ci:
                    ci.setattr('b', default=1, mc_set_unknown=True)
                    errorline[0] = next_line_num()
                    ci.setattr('_mc_whatever', default=1)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], msg)


def test_setattr_to_attribute_underscore_attribute(capsys):
    errorline = [None]

    msg = """Trying to set attribute '_b' on a config item. Atributes starting with '_' cannot be set using item.setattr. Use assignment instead."""
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with ConfigItem():
                with ConfigItem() as ci:
                    errorline[0] = next_line_num()
                    ci.setattr('_b', default=7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], msg)


def test_setattr_to_attribute_underscore_attribute_root(capsys):
    errorline = [None]

    msg = """Trying to set attribute '_b' on a config item. Atributes starting with '_' cannot be set using item.setattr. Use assignment instead."""
    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with ConfigItem() as cr:
                errorline[0] = next_line_num()
                cr.setattr('_b', default=7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], msg)


def test_getattr_repr_error():
    class X(ConfigItem):
        def __repr__(self):
            raise Exception("Bad repr")

    with raises(AttributeError) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with ConfigItem():
                x = X()
                _ = x.a

    assert "X' object has no attribute 'a'" in str(exinfo.value)


def test_load_only_allowed_once():
    @mc_config(ef2_prod_pp, load_now=True)
    def config(_):
        pass

    with raises(ConfigApiException) as exinfo:
        config.load()

    assert "Configuration can only be loaded once." in str(exinfo.value)

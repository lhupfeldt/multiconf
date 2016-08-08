# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from .utils.utils import api_error, config_error, lineno

from .. import ConfigRoot, ConfigItem, ConfigBuilder, RepeatableConfigItem, ConfigApiException, ConfigException
from ..decorators import nested_repeatables
from ..envs import EnvFactory

ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_pp = EnvFactory()
pp2 = ef2_prod_pp.Env('pp')
prod2 = ef2_prod_pp.Env('prod')


_expected_ex_msg = "An error was detected trying to get attribute '%s' on class 'inner'"
_extra_stderr = """
    - You did not initailize the parent class (parent __init__ method has not been called)."""


def capie(line_num, *lines):
    return api_error(__file__, line_num, *lines)


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass


class RepeatableItem(RepeatableConfigItem):
    pass


def test_find_contained_in_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass

        class inner(ConfigItem):
            def __init__(self):
                global inner_errorline
                # Error: find_contained_in must not be called before parent __init__
                inner_errorline = lineno() + 1
                self.find_contained_in('a')

        with root(prod2, ef2_prod_pp):
            inner()

    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % 'find_contained_in'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert str(exinfo.value) == eex


def test_property_method_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass

        class inner(ConfigItem):
            def __init__(self):
                global inner_errorline
                # Error: env must not be called before parent __init__
                inner_errorline = lineno() + 1
                print(self.env)

        with root(prod2, ef2_prod_pp):
            inner()

    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % 'env'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert str(exinfo.value) == eex


def test_undefined_method_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass

        class inner(ConfigItem):
            def __init__(self):
                global inner_errorline
                inner_errorline = lineno() + 1
                self.ttt('')

        with root(prod2, ef2_prod_pp):
            inner()

    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % 'ttt'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert str(exinfo.value) == eex


def test_undefined_property_method_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass

        class inner(ConfigItem):
            def __init__(self):
                global inner_errorline
                inner_errorline = lineno() + 1
                self.ttt

        with root(prod2, ef2_prod_pp):
            inner()

    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % 'ttt'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert str(exinfo.value) == eex


def test_setattr_multiconf_private_attribute(capsys):
    class root(ConfigRoot):
        pass

    class inner(ConfigItem):
        pass

    msg = """Trying to set attribute '_mc_whatever' on a config item. Atributes starting with '_mc' are reserved for multiconf internal usage."""

    with raises(ConfigException) as exinfo:
        with root(prod2, ef2_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('_mc_whatever', default=1)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, msg)

    with raises(ConfigException) as exinfo:
        with root(prod2, ef2_prod_pp) as cr:
            with inner() as ci:
                ci.b = 1
                errorline = lineno() + 1
                ci.setattr('_mc_whatever', default=1)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, msg)


def test_setattr_to_attribute_underscore_attribute(capsys):
    msg = """Trying to set attribute '_b' on a config item. Atributes starting with '_' can not be set using item.setattr. Use assignment instead."""
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod):
            with ConfigItem() as ci:
                errorline = lineno() + 1
                ci.setattr('_b', default=7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, msg)


def test_setattr_to_attribute_underscore_attribute_root(capsys):
    msg = """Trying to set attribute '_b' on a config item. Atributes starting with '_' can not be set using item.setattr. Use assignment instead."""
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod) as cr:
            errorline = lineno() + 1
            cr.setattr('_b', default=7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, msg)


def test_setattr_to_attribute_underscore_attribute_builder(capsys):
    msg = """Trying to set attribute '_b' on a config item. Atributes starting with '_' can not be set using item.setattr. Use assignment instead."""

    class CB(ConfigBuilder):
        def build(self):
            pass

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod):
            with CB() as ci:
                errorline = lineno() + 1
                ci.setattr('_b', default=7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, msg)


def test_getattr_repr_error():
    class X(ConfigItem):
        def __repr__(self):
            raise Exception("Bad repr")

    with raises(AttributeError) as exinfo:
        with ConfigRoot(prod2, ef2_prod_pp):
            x = X()
            _ = x.a

    assert "X'> has no attribute 'a'" in str(exinfo.value)
    assert "X'> has no attribute 'a'" in str(exinfo.value)

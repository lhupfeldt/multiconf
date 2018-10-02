# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, InvalidUsageException, ConfigException
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import next_line_num, replace_multiconf_file_line_msg, config_error, file_line, lines_in
from .utils.utils import local_func
from .utils.tstclasses import ItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
g_p = ef.EnvGroup('g_p', pp, prod)

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def test_validate_properties_property_method():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    cr = config(prod)
    assert cr.num_invalid_property_usage == 0


def test_validate_properties_property_attribute_method_override():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            with Nested() as nn:
                nn.setattr("m", mc_overwrite_property=True, default=7)

    cr = config(prod).ItemWithAA
    assert cr.someitem.m == 7
    assert cr.num_invalid_property_usage == 0


def test_validate_properties_property_method_raises_InvalidUsageException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise InvalidUsageException("No m now")

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    cr = config(prod)
    assert cr.num_invalid_property_usage == 2


_validate_properties_property_method_raises_exception_expected_stderr = """
ConfigError: Exception validating @property 'm' on item <class 'test.validate_properties_test.%(local_func)sNested'> in Env('pp').
Traceback (most recent call last):
  File "fake_multiconf_dir/multiconf.py", line 999, in _mc_validate_properties
    val = getattr(self, key)
  %(file_line)s, in m
    raise Exception("Something is wrong")
Exception: Something is wrong
""".lstrip()

def test_validate_properties_property_method_raises_exception(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            errorline[0] = next_line_num()
            raise Exception("Something is wrong")

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAA() as it:
                it.setattr('aa', default=1, prod=0)
                Nested()

    _sout, serr = capsys.readouterr()
    assert replace_multiconf_file_line_msg(serr) == _validate_properties_property_method_raises_exception_expected_stderr % (
        dict(local_func=local_func(), file_line=file_line(__file__, errorline[0])))
    assert str(exinfo.value) == "Error validating @property methods for Env('pp')"


def test_validate_properties_property_method_on_repeatable_raises_exception(capsys):
    errorline = [None]

    @named_as('someitems')
    class RNested(RepeatableConfigItem):
        @property
        def m(self):
            errorline[0] = next_line_num()
            raise Exception("Something is wrong")

    @nested_repeatables('someitems')
    class ItemWithAAAndSomeItems(ItemWithAA):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(rt):
            with ItemWithAAAndSomeItems() as it:
                it.setattr('aa', default=1, prod=0)
                RNested('a')
                RNested('b')

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        # Once for each repeated item
        'Exception: Something is wrong',
        'Exception: Something is wrong',
    )

    assert str(exinfo.value) == "Error validating @property methods for Env('pp')"


def test_validate_properties_dir_error(capsys):
    """multiconf does not depend on dir(obj), but only on dir(cls)"""
    errorline = [None]

    @named_as('someitem')
    class Nested(ItemWithAA):
        def __dir__(self):
            errorline[0] = next_line_num()
            raise Exception('Error in dir()')

        @property
        def c(self):
            return "show-me"

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            with Nested() as nn:
                nn.aa = 2

    nn = config(pp).ItemWithAA.someitem
    assert nn.c == "show-me"


def test_mc_validate_has_method():
    class item(ConfigItem):
        def hello(self):
            raise Exception("Error in hello")

        def hi(self, there):
            raise Exception("Error in hello " + there)

    @mc_config(ef, load_now=True)
    def config(_):
        item()

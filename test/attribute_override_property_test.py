# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, re, traceback

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException, MC_REQUIRED

from multiconf.decorators import named_as
from multiconf.envs import EnvFactory

from .utils.utils import py3_local, config_error, next_line_num


major_version = sys.version_info[0]


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


def test_attribute_overrides_property_method():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef)
    def _(_):
        with Nested() as nn:
            nn.setattr('m', default=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def _(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def _(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 1


def test_attribute_overrides_property_method_not_existing(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with Nested() as nn:
                errorline[0] = next_line_num()
                nn.setattr('m', default=7, mc_overwrite_property=True)

    sout, serr = capsys.readouterr()
    assert sout == ''
    assert serr == ce(errorline[0], "'mc_overwrite_property' is True but no property named 'm' exists.")


def test_attribute_overrides_property_method_is_regular_method(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        def m(self):
            return 2

        @property
        def n(self):
            return 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with Nested() as nn:
                nn.setattr('n', default=7, mc_overwrite_property=True)
                errorline[0] = next_line_num()
                nn.setattr('m', default=7, mc_overwrite_property=True)

    _sout, serr = capsys.readouterr()
    msg = re.sub(r"m at [^>]*>", "m at 1234>", str(serr))
    expected = "'mc_overwrite_property' specified but existing attribute 'm' with value '<function %(py3_local)sm at 1234>' is not a @property." % \
               dict(py3_local=py3_local('Nested.'))
    assert msg == ce(errorline[0], expected)


def test_attribute_clash_property_method_error_in_with_block(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self):
            super(Nested, self).__init__()

        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with Nested() as nn:
                errorline[0] = next_line_num()
                nn.setattr('m', default=7)

    _sout, serr = capsys.readouterr()
    exp = "The attribute 'm' clashes with a @property or method and 'mc_overwrite_property' is False."
    assert serr == ce(errorline[0], exp)


def test_attribute_clash_property_method_error_in_init_def(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self, m=None):
            super(Nested, self).__init__()
            errorline[0] = next_line_num()
            self.m = m

        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            Nested(m=7)

    _sout, serr = capsys.readouterr()
    print(serr)
    exp = "The attribute 'm' clashes with a @property or method. Use item.setattr with mc_overwrite_property=True if overwrite intended."
    assert serr == ce(errorline[0], exp)


def test_attribute_overrides_property_method_failing():
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            errorline[0] = next_line_num()
            raise Exception("bad property method")

    @mc_config(ef)
    def _(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def _(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    with raises(ConfigException) as exinfo:
        print(cr.someitem.m)

    origin_line_exp = 'raise Exception("bad property method")'

    if major_version >= 3:
        origin = traceback.extract_tb(exinfo.value.__cause__.__traceback__)[-1]
        assert origin.filename == __file__
        assert origin.lineno == errorline[0]
        assert origin.line == origin_line_exp

    exp = "Attribute 'm' is defined as a multiconf attribute and as a @property method but value is undefined for Env('prod') and @property method call failed"
    exp += " with: Exception: bad property method"
    assert exp in str(exinfo.value)

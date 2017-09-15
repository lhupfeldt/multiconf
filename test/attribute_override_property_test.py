# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, re, traceback

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException

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


def test_attribute_overrides_property_method_ok():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef)
    def _0(_):
        with Nested() as nn:
            nn.setattr('m', default=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def _1(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def _2(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 1


def test_attribute_overrides_property_inherited_method():
    @named_as('someitem')
    class NestedBase(ConfigItem):
        @property
        def m(self):
            return 1

    class Nested(NestedBase):
        pass

    @mc_config(ef)
    def _0(_):
        with Nested() as nn:
            nn.setattr('m', default=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def _1(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def _2(_):
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

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with Nested() as nn:
                errorline[0] = next_line_num()
                nn.setattr('m', default=7, mc_overwrite_property=True)

    _sout, serr = capsys.readouterr()
    if major_version >= 3:
        msg = re.sub(r"m at [^>]*>", "m at 1234>", str(serr))
        expected = "'mc_overwrite_property' specified but existing attribute 'm' with value '<function %(py3_local)sNested.m at 1234>' is not a @property." % \
                   dict(py3_local=py3_local())
    else:
        msg = serr
        expected = "'mc_overwrite_property' specified but existing attribute 'm' with value '<unbound method Nested.m>' is not a @property."
    assert msg == ce(errorline[0], expected)


def test_setattr_replace_property_in_with_not_allowed(capsys):
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


def test_assigment_replace_property_in_init_not_allowed(capsys):
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


def test_assigment_replace_property_in_with_not_allowed(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def mm(self):
            return 1

    with raises(Exception) as exinfo:
        @mc_config(ef)
        def _(_):
            with Nested() as nn:
                errorline[0] = next_line_num()
                nn.mm = 7

    _sout, serr = capsys.readouterr()
    exp = "The attribute 'mm' clashes with a @property or method. Use item.setattr with mc_overwrite_property=True if overwrite intended."
    assert serr == ce(errorline[0], exp)


def test_assigment_replace_mc_property_wrapper_not_allowed(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def mm(self):
            return 1

    with raises(Exception) as exinfo:
        @mc_config(ef)
        def _(_):
            with Nested() as nn:
                nn.setattr('mm', prod=3, mc_overwrite_property=True)
                errorline[0] = next_line_num()
                nn.mm = 7

    _sout, serr = capsys.readouterr()
    exp = "The attribute 'mm' is already fully defined."
    assert serr == ce(errorline[0], exp)


def test_attribute_overrides_failing_property_method():
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            errorline[0] = next_line_num()
            raise Exception("bad property method")

    @mc_config(ef, validate_properties=False)
    def _0(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef, validate_properties=False)
    def _1(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    with raises(AttributeError) as exinfo:
        print(cr.someitem.m)

    origin_line_exp = 'raise Exception("bad property method")'

    if major_version >= 3:
        # TODO
        # print('XXX __context__', dir(exinfo.value.__context__))
        # print('XXX __cause__', dir(exinfo.value.__cause__))

        # ctx = exinfo.value.__context__
        # while True:
        #     if not ctx.__context__:
        #         break
        #     ctx = ctx.__context__
        #     print('ctx:', ctx.__traceback__)

        # tb = traceback.extract_tb(ctx.__traceback__)
        # for origin in tb:
        #     print(origin)
        # origin = tb[-1]
        # filename, lineno, function_name, line = origin
        # assert filename == __file__
        # assert lineno == errorline[0]
        # assert function_name == 'm'
        # assert line == origin_line_exp
        pass

    exp = "Object of type: <class 'test.attribute_override_property_test.%(py3_local)sNested'> has no attribute 'm'." % dict(py3_local=py3_local())
    exp += " Attribute 'm' is defined as a multiconf attribute and as a @property method but value is undefined for Env('prod') and @property method call failed with: Exception: bad property method"
    print(exp)
    ex = str(exinfo.value)
    print(ex)
    assert exp in ex


def test_attribute_overrides_property_method_raising_attribute_error():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            """This raises AttributeError, a common scenario when calling a @property during config load"""
            print("test_attribute_overrides_property_method_raising_attribute_error, @property m, raises AttributeError.")
            return self.i_dont_have_this_attribute

    @mc_config(ef, validate_properties=False)
    def _1(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = ef.config(prod)
    assert cr.someitem.m == 7

    @mc_config(ef, validate_properties=False)
    def _2(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    nn = ef.config(prod).someitem
    with raises(AttributeError) as exinfo:
        mmm = nn.m
        print(mmm)

    ex_msg = str(exinfo.value)
    print(ex_msg)
    assert "Attribute 'm' is defined as a multiconf attribute and as a @property method" in ex_msg
    assert "value is undefined for Env('prod') and @property method call failed" in ex_msg
    assert "AttributeError: 'Nested' object has no attribute 'i_dont_have_this_attribute'" in ex_msg

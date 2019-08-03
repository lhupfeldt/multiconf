# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, re, traceback

# pylint: disable=E0611
from pytest import raises, xfail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException

from multiconf.decorators import named_as, nested_repeatables
from multiconf.envs import EnvFactory

from .utils.utils import local_func, py37_no_exc_comma, config_error, next_line_num, replace_ids


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


def test_attribute_overrides_property_method_config_item_ok():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef, load_now=True)
    def config0(_):
        with Nested() as nn:
            nn.setattr('m', default=7, mc_overwrite_property=True)

    cr = config0(prod)
    assert cr.someitem.m == 7

    @mc_config(ef, load_now=True)
    def config1(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = config1(prod)
    assert cr.someitem.m == 7

    @mc_config(ef, load_now=True)
    def config2(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    cr = config2(prod)
    assert cr.someitem.m == 1


def test_attribute_overrides_property_method_repeatable_config_item_ok():
    @named_as('someitems')
    class Rep(RepeatableConfigItem):
        @property
        def m(self):
            return 1

    @named_as('root')
    @nested_repeatables('someitems')
    class Root(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config0(_):
        with Root():
            with Rep('r1') as rr:
                rr.setattr('m', default=7, mc_overwrite_property=True)
            Rep('r2')

    cr = config0(prod).root
    assert cr.someitems['r1'].m == 7
    assert cr.someitems['r2'].m == 1

    @mc_config(ef, load_now=True)
    def config1(_):
        with Root():
            with Rep('r1') as rr:
                rr.setattr('m', prod=7, mc_overwrite_property=True)
            Rep('r2')

    cr = config1(prod).root
    assert cr.someitems['r1'].m == 7
    assert cr.someitems['r2'].m == 1

    @mc_config(ef, load_now=True)
    def config2(_):
        with Root():
            with Rep('r1') as rr:
                rr.setattr('m', pp=7, mc_overwrite_property=True)
            Rep('r2')

    cr = config2(prod).root
    assert cr.someitems['r1'].m == 1
    assert cr.someitems['r2'].m == 1


def test_attribute_overrides_property_inherited_method():
    @named_as('someitem')
    class NestedBase(ConfigItem):
        @property
        def m(self):
            return 1

    class Nested(NestedBase):
        pass

    @mc_config(ef, load_now=True)
    def config0(_):
        with Nested() as nn:
            nn.setattr('m', default=7, mc_overwrite_property=True)

    cr = config0(prod)
    assert cr.someitem.m == 7

    @mc_config(ef, load_now=True)
    def config1(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = config1(prod)
    assert cr.someitem.m == 7

    @mc_config(ef, load_now=True)
    def config2(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    cr = config2(prod)
    assert cr.someitem.m == 1


def test_attribute_overrides_property_method_not_existing(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
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
        @mc_config(ef, load_now=True)
        def config(_):
            with Nested() as nn:
                errorline[0] = next_line_num()
                nn.setattr('m', default=7, mc_overwrite_property=True)

    _sout, serr = capsys.readouterr()
    msg = re.sub(r"m at [^>]*>", "m at 1234>", str(serr))
    expected = "'mc_overwrite_property' specified but existing attribute 'm' with value '<function %(local_func)sNested.m at 1234>' is not a @property." % \
               dict(local_func=local_func())
    assert msg == ce(errorline[0], expected)


def test_setattr_replace_property_in_with_not_allowed(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self):
            super().__init__()

        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
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
            super().__init__()
            errorline[0] = next_line_num()
            self.m = m

        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
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
        @mc_config(ef, load_now=True)
        def config(_):
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
        @mc_config(ef, load_now=True)
        def config2(_):
            with Nested() as nn:
                nn.setattr('mm', prod=3, mc_overwrite_property=True)
                errorline[0] = next_line_num()
                nn.mm = 7

    _sout, serr = capsys.readouterr()
    exp = "The attribute 'mm' clashes with a @property or method. Use item.setattr with mc_overwrite_property=True if overwrite intended."
    assert serr == ce(errorline[0], exp)
    xfail("Not an ideal error message")


def test_replace_mc_property_wrapper_not_allowed(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def mm(self):
            return 1

    with raises(Exception) as exinfo:
        @mc_config(ef, load_now=True)
        def config2(_):
            with Nested() as nn:
                nn.setattr('mm', prod=3, mc_overwrite_property=True)
                errorline[0] = next_line_num()
                nn.setattr('mm', prod=7, mc_overwrite_property=True)

    _sout, serr = capsys.readouterr()
    exp = "The attribute 'mm' is already fully defined."
    assert serr == ce(errorline[0], exp)


_attribute_overrides_failing_property_method_exp = """{
    "__class__": "NestedBadM #as: 'someitem', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "m #no value for Env('prod')": true,
    "m #json_error trying to handle property method": "Exception('bad property method'%(comma)s)"
}, object of type: <class 'test.attribute_override_property_test.%(local_func)sNestedBadM'> has no attribute 'm'.
""".strip()

def test_attribute_overrides_failing_property_method():
    errorline = [None]

    @named_as('someitem')
    class NestedBadM(ConfigItem):
        @property
        def m(self):
            errorline[0] = next_line_num()
            raise Exception("bad property method")

    @mc_config(ef)
    def config0(_):
        with NestedBadM() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = config0.load(validate_properties=False)(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def config1(_):
        with NestedBadM() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    cr = config1.load(validate_properties=False)(prod)
    with raises(AttributeError) as exinfo:
        print(cr.someitem.m)

    origin_line_exp = 'raise Exception("bad property method")'

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

    exp = _attribute_overrides_failing_property_method_exp % dict(local_func=local_func(), comma=py37_no_exc_comma)
    exp += " Attribute 'm' is defined as a multiconf attribute and as a @property method but value is undefined for Env('prod') and @property method call failed with: Exception('bad property method'{comma})".format(comma=py37_no_exc_comma)

    print('exp:', exp)
    got = replace_ids(str(exinfo.value), named_as=False)
    print('got:', got)
    assert exp in got

    xfail("TODO: improve message, improve json")


def test_attribute_overrides_property_method_raising_attribute_error():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            """This raises AttributeError, a common scenario when calling a @property during config load"""
            print("test_attribute_overrides_property_method_raising_attribute_error, @property m, raises AttributeError.")
            return self.i_dont_have_this_attribute

    @mc_config(ef)
    def config1(_):
        with Nested() as nn:
            nn.setattr('m', prod=7, mc_overwrite_property=True)

    cr = config1.load(validate_properties=False)(prod)
    assert cr.someitem.m == 7

    @mc_config(ef)
    def config2(_):
        with Nested() as nn:
            nn.setattr('m', pp=7, mc_overwrite_property=True)

    nn = config2.load(validate_properties=False)(prod).someitem
    with raises(AttributeError) as exinfo:
        mmm = nn.m
        print(mmm)

    ex_msg = str(exinfo.value)
    print(ex_msg)
    assert "Attribute 'm' is defined as a multiconf attribute and as a @property method" in ex_msg
    assert "value is undefined for Env('prod') and @property method call failed" in ex_msg
    assert """AttributeError("'Nested' object has no attribute 'i_dont_have_this_attribute'"%(comma)s)""" % dict(comma=py37_no_exc_comma) in ex_msg


def test_attribute_overrides_property_method_using_mc_set_unknown_repeated_env(capsys):
    errorline = [None]

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with Nested() as nn:
                errorline[0] = next_line_num()
                nn.setattr('m', pp=7, mc_overwrite_property=True)
                nn.setattr('m', pp=17, mc_set_unknown=True)

    sout, serr = capsys.readouterr()
    exp = "Attempting to use 'mc_set_unknown' to overwrite a an existing @property 'm'."
    assert exp in serr
    assert not sout

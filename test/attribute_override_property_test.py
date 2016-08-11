# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re

# pylint: disable=E0611
from pytest import raises, xfail

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException, MC_REQUIRED

from ..decorators import named_as, strict_setattr
from ..envs import EnvFactory

from .utils.utils import py3_local, config_error, lineno


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

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr('m!', default=7)
    assert cr.someitem.m == 7

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr('m!', prod=7)
    assert cr.someitem.m == 7

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr('m!', pp=7)
    assert cr.someitem.m == 1


def test_attribute_overrides_property_method_strict():
    @named_as('someitem')
    @strict_setattr()
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr('m!', default=7)
    assert cr.someitem.m == 7

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr('m!', prod=7)
    assert cr.someitem.m == 7

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr('m!', pp=7)
    assert cr.someitem.m == 1


def test_attribute_overrides_property_method_not_existing(capsys):
    @named_as('someitem')
    class Nested(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with Nested() as nn:
                errorline = lineno() + 1
                nn.setattr('m!', default=7)

    sout, serr = capsys.readouterr()
    assert sout == ''
    assert serr == ce(errorline, "m! specifies overriding a property method, but no property named 'm' exists.")


def test_attribute_overrides_property_method_is_regular_method(capsys):
    @named_as('someitem')
    class Nested(ConfigItem):
        def m(self):
            return 2

        @property
        def n(self):
            return 2

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with Nested() as nn:
                nn.setattr('n!', default=7)
                errorline = lineno() + 1
                nn.setattr('m!', default=7)

    _sout, serr = capsys.readouterr()
    msg = re.sub(r"m at [^>]*>", "m at 1234>", str(serr))
    expected = "m! specifies overriding a property method, but attribute 'm' with value '<function %(py3_local)sm at 1234>' is not a property." % \
               dict(py3_local=py3_local('Nested.'))
    assert msg == ce(errorline, expected)


def test_attribute_clash_property_method_error_in_with_block(capsys):
    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self):
            super(Nested, self).__init__()

        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with Nested() as nn:
                errorline = lineno() + 1
                nn.setattr('m', default=7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "The attribute 'm' (not ending in '!') clashes with a property or method")


def test_attribute_clash_property_method_error_in_init_def(capsys):
    init_call_errorline = lineno() + 5
    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self, m=None):
            super(Nested, self).__init__()
            self.m = m

        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            Nested(m=7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(init_call_errorline, "The attribute 'm' (not ending in '!') clashes with a property or method")


def test_attribute_overrides_property_method_failing():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise Exception("bad property method")

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr('m!', prod=7)
    assert cr.someitem.m == 7

    with ConfigRoot(prod, ef):
        with Nested() as nn:
            nn.setattr('m!', pp=7)

    with raises(AttributeError) as exinfo:
        print(nn.m)

    assert "Attribute 'm' is defined as muticonf attribute and as property method, but value is undefined for env Env('prod') and method call failed" in str(exinfo.value)


def test_attribute_overrides_property_method_builder():
    @named_as('n1')
    class Nested1(ConfigItem):
        @property
        def m(self):
            return 1

    @named_as('n2')
    class Nested2(ConfigItem):
        @property
        def m(self):
            return 1

    class NestedBuilder(ConfigBuilder):
        def build(self):
            Nested1()
            Nested2()

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', default=7)
    assert cr.n1.m == 7
    assert cr.n2.m == 7

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', prod=7)
    assert cr.n1.m == 7
    assert cr.n2.m == 7

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', pp=7)
    assert cr.n1.m == 1
    assert cr.n2.m == 1


def test_attribute_overrides_property_no_property_mix_builder():
    """We have one @property, so overriding with '!' is ok"""

    @named_as('n1')
    class Nested1(ConfigItem):
        @property
        def m(self):
            return 1

    @named_as('n2')
    class Nested2(ConfigItem):
        m = MC_REQUIRED

    @strict_setattr()
    @named_as('n3')
    class Nested3(ConfigItem):
        m = 13

    @named_as('n4')
    class Nested4(ConfigItem):
        def __init__(self):
            super(Nested4, self).__init__()
            self.m = 23

    @named_as('n5')
    class Nested5(ConfigItem):
        def __init__(self):
            super(Nested5, self).__init__()
            self.m = MC_REQUIRED

        def mc_init(self):
            super(Nested5, self).mc_init()
            self.m = 24

    class NestedBuilder(ConfigBuilder):
        def build(self):
            Nested1()
            Nested2()
            Nested3()
            Nested4()
            Nested5()

    # Validate 'm' values without override
    with ConfigRoot(prod, ef) as cr:
        Nested1()
        Nested2()
        Nested3()
        Nested4()
        Nested5()
    assert cr.n1.m == 1
    assert hasattr(cr.n2, 'm')
    assert cr.n3.m == 13
    assert cr.n4.m == 23
    assert cr.n5.m == 24

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', default=7)
    assert cr.n1.m == 7
    assert cr.n2.m == 7
    assert cr.n3.m == 7
    assert cr.n4.m == 7
    assert cr.n5.m == 7

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', prod=7)
    assert cr.n1.m == 7
    assert cr.n2.m == 7
    assert cr.n3.m == 7
    assert cr.n4.m == 7
    assert cr.n5.m == 7

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', pp=7)
    assert cr.n1.m == 1
    assert hasattr(cr.n2, 'm')
    assert cr.n3.m == 13
    assert cr.n4.m == 23
    assert cr.n5.m == 24


def test_attribute_overrides_property_inherited_builder():
    """
    Test overriding an inherited property method in builder
    """

    class NestedBase1(ConfigItem):
        @property
        def m(self):
            return 1

    class NestedBase(NestedBase1):
        pass

    @named_as('n1')
    class Nested1(NestedBase):
        pass

    @named_as('n2')
    class Nested2(ConfigItem):
        pass

    class NestedBuilder(ConfigBuilder):
        def build(self):
            Nested1()
            Nested2()

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', default=7)
    assert cr.n1.m == 7
    assert cr.n2.m == 7

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', prod=7)
    assert cr.n1.m == 7
    assert cr.n2.m == 7

    with ConfigRoot(prod, ef) as cr:
        with NestedBuilder() as nn:
            nn.setattr('m!', pp=7)
    assert cr.n1.m == 1
    assert not hasattr(cr.n2, 'm')


def test_attribute_overrides_errors_builder():
    @named_as('n1')
    class Nested1(ConfigItem):
        m = 222
        n = 1

    @named_as('n2')
    class Nested2(ConfigItem):
        pass

    @named_as('n3')
    class Nested3(ConfigItem):
        def m(self):
            return 1

    class NestedBuilder(ConfigBuilder):
        def build(self):
            Nested1()
            Nested2()
            Nested3()

    expected_ex_header = "The following {sing_plu} found when setting values on items from build()\n"

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef) as cr:
            with NestedBuilder() as nn:
                nn.setattr('m!', default=7)
    expected_ex = expected_ex_header.format(sing_plu="error was") + \
                  "  m! specifies overriding a property method, but attribute 'm' with value '222' is not a property."
    assert str(exinfo.value) == expected_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef) as cr:
            with NestedBuilder() as nn:
                nn.setattr('m!', prod=7)
                nn.setattr('n!', default=333)
    expected_ex = expected_ex_header.format(sing_plu="errors were") + \
                  "  m! specifies overriding a property method, but attribute 'm' with value '222' is not a property.\n" \
                  "  n! specifies overriding a property method, but attribute 'n' with value '1' is not a property."
    assert str(exinfo.value) == expected_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef) as cr:
            with NestedBuilder() as nn:
                nn.setattr('m!', pp=7)
    expected_ex = expected_ex_header.format(sing_plu="error was") + \
                  "  m! specifies overriding a property method, but attribute 'm' with value '222' is not a property."
    assert str(exinfo.value) == expected_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef) as cr:
            with NestedBuilder() as nn:
                nn.setattr('y!', pp=7)
    expected_ex = expected_ex_header.format(sing_plu="error was") + \
                  "  y! specifies overriding a property method, but no property named 'y' exists."
    assert str(exinfo.value) == expected_ex


def test_static_attribute_overrides_mc_attribute_inherited_builder():
    """
    Test static (simple python) attribute overriding an inherited mc attribute
    """

    class NestedBase1(ConfigItem):
        def __init__(self):
            super(NestedBase1, self).__init__()
            self.m = 1

    class NestedBase(NestedBase1):
        pass

    xfail("TODO?: Allow static member to override mc attribute")

    @named_as('n1')
    class Nested1(NestedBase):
        m = 2

    with ConfigRoot(prod, ef) as cr:
        Nested1()
    assert cr.n1.m == 2

    with ConfigRoot(prod, ef) as cr:
        with Nested1() as nn:
            nn.setattr('m', prod=7)
    assert cr.n1.m == 7

    with ConfigRoot(prod, ef) as cr:
        with Nested1() as nn:
            nn.setattr('m!', pp=7)
    assert cr.n1.m == 1
    assert not hasattr(cr.n2, 'm')

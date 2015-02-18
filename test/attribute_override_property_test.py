# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .. import ConfigRoot, ConfigItem, ConfigException

from ..decorators import named_as
from ..envs import EnvFactory


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


def test_attribute_overrides_property_method_not_existing():
    @named_as('someitem')
    class Nested(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with Nested() as nn:
                nn.setattr('m!', default=7)

    assert "m! specifies overriding a property method, but no property named 'm' exists" in str(exinfo.value)


def test_attribute_overrides_property_method_is_regular_method():
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
                nn.setattr('m!', default=7)

    assert "m! specifies overriding a property method, but 'm' is not a property" in str(exinfo.value)


def test_attribute_clash_property_method():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 2

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with Nested() as nn:
                nn.setattr('m', default=7)

    assert "The attribute 'm' (not ending in '!') clashes with a property or method" in str(exinfo.value)

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            Nested(m=7)

    assert "The attribute 'm' (not ending in '!') clashes with a property or method" in str(exinfo.value)


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

    print(str(exinfo.value))
    assert "Attribute 'm' is defined as muticonf attribute and as property method, but value is undefined for env Env('prod') and method call failed" in str(exinfo.value)

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import ConfigItem
from multiconf.decorators import named_as, nested_repeatables, ConfigDefinitionException
from multiconf.envs import EnvFactory


def test_decorator_arg_is_keyword_in_nested_repeatables_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @nested_repeatables('a', 'b', 'def', 'c')
        class root(ConfigItem):
            pass

    assert str(exinfo.value) == "'def' is not a valid identifier."


def test_decorator_arg_not_a_valid_identifier_in_named_as_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @named_as('a-b')
        class root(ConfigItem):
            pass

    assert str(exinfo.value) == "'a-b' is not a valid identifier."


def test_decorator_arg_is_a_keyword_in_named_as_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @named_as('class')
        class root(ConfigItem):
            pass

    assert str(exinfo.value) == "'class' is not a valid identifier."

#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import fail, dummy
from .utils import config_error, config_warning, lineno

from .. import ConfigRoot, ConfigItem, ConfigException, NoAttributeException
from ..decorators import required, required_if, optional, nested_repeatables, ConfigDefinitionException
from ..envs import EnvFactory

ef = EnvFactory()

dev2ct = ef.Env('dev2ct')
dev2st = ef.Env('dev2st')
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3ct')
dev3st = ef.Env('dev3st')
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)

class DecoratorsErrorsTest(unittest.TestCase):
    def required_attributes_missing_for_configroot_test(self):
        try:
            @required('someattr1, someattr2')
            class root(ConfigRoot):
                pass

            with root(prod, [prod]):
                pass
            fail ("Expected exception")
        except ConfigException as ex:
            assert ex.message == "No value given for required attributes: ['someattr1', 'someattr2']"

    def required_attributes_missing_for_configitem_test(self):
        try:
            class root(ConfigRoot):
                pass

            @required('abcd, efgh, ijkl')
            class item(ConfigItem):
                pass

            with root(prod, [prod]):
                with item() as ii:
                    ii.setattr('efgh', prod=7)

            fail ("Expected exception")
        except ConfigException as ex:
            assert ex.message == "No value given for required attributes: ['abcd', 'ijkl']"

    def required_if_optional_attributes_missing_test(self):
        try:
            class root(ConfigRoot):
                pass

            @required_if('abcd', 'efgh, ijkl')
            class item(ConfigItem):
                pass

            with root(prod, [prod]):
                with item() as ii:
                    ii.setattr('abcd', prod=1)

            fail ("Expected exception")
        except ConfigException as ex:
            assert ex.message == "Missing required_if attributes. Condition attribute: 'abcd'==1, missing: ['efgh', 'ijkl']"

    def required_if_condition_attribute_missing_test(self):
        class root(ConfigRoot):
            pass

        @required_if('abcd', 'efgh, ijkl')
        class item(ConfigItem):
            pass

        with root(prod, [prod]):
            item()
        # The above code is valid, the condition attribute i not mandatory
        assert 1 == 1

    def optional_attribute_accessed_for_env_where_not_specified_test(self):
        @optional('a')
        class root(ConfigRoot):
            pass

        try:
            with root(prod, [prod, dev2ct]) as cr:
                cr.setattr('a', dev2ct=18)

            print cr.a
            fail ("Expected exception")
        except NoAttributeException  as ex:
            assert ex.message == "Attribute 'a' undefined for env Env('prod')"

    def decorator_arg_not_a_valid_identifier_in_required_decorator_test(self):
        try:
            @required('a, a-b, b, 99')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "['a-b', '99'] are not valid identifiers"

    def decorator_arg_is_keyword_in_nested_repeatables_decorator_test(self):
        try:
            @nested_repeatables('a, b, def, c')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "'def' is not a valid identifier"

    def decorator_args_are_keywords_in_required_decorator_test(self):
        try:
            @required('a, class, b, 99')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "['class', '99'] are not valid identifiers"

    def decorator_arg_not_a_valid_identifier_in_required_if_decorator_test(self):
        try:
            @required_if('-a', 'a, a-b, b, 99')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "['-a', 'a-b', '99'] are not valid identifiers"

    def required_attributes_inherited_missing_test(self):
        @required('anattr, anotherattr')
        class root(ConfigRoot):
            pass

        @required('someattr2, someotherattr2')
        class root2(root):
            pass

        try:
            with root2(prod, [prod]) as cr:
                cr.setattr('anattr', prod=1)
                cr.setattr('someattr2', prod=3)
                cr.setattr('someotherattr2', prod=4)
            fail ("Expected exception")
        except ConfigException as ex:
            assert ex.message == "No value given for required attributes: ['anotherattr']"

    def required_attributes_inherited_redefined_test(self):
        with dummy.dummy_io('stdin not used') as d_io:
            @required('anattr, anotherattr')
            class root(ConfigRoot):
                pass

            errorline = lineno() + 2
            @required('anattr, someotherattr2')
            class root2(root):
                pass

        _sout, serr = d_io
        assert serr == cw(errorline, "Attribute name: 'anattr' re-specified as 'required' on class: 'root2' , was already inherited from a super class.")

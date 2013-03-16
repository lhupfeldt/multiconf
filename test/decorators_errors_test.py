#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import test, fail, dummy
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
    @test("required attributes missing - configroot")
    def _a(self):
        try:
            @required('someattr1, someattr2')
            class root(ConfigRoot):
                pass

            with root(prod, [prod]):
                pass
            fail ("Expected exception")
        except ConfigException as ex:
            assert ex.message == "No value given for required attributes: ['someattr1', 'someattr2']"

    @test("required attributes missing - configitem")
    def _b(self):
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


    @test("required_if - optional attributes missing")
    def _c(self):
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

    @test("required_if - condition attribute missing")
    def _c2(self):
        class root(ConfigRoot):
            pass

        @required_if('abcd', 'efgh, ijkl')
        class item(ConfigItem):
            pass

        with root(prod, [prod]):
            item()
        # The above code is valid, the condition attribute i not mandatory
        assert 1 == 1

    @test("optional attribute accessed for env where not specified")
    def _d(self):
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

    @test("decorator arg not a valid identifier - required")
    def _e(self):
        try:
            @required('a, a-b, b, 99')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "['a-b', '99'] are not valid identifiers"

    @test("decorator arg is keyword - nested_repeatables")
    def _e2(self):
        try:
            @nested_repeatables('a, b, def, c')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "'def' is not a valid identifier"

    @test("decorator args are keywords - required")
    def _e3(self):
        try:
            @required('a, class, b, 99')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "['class', '99'] are not valid identifiers"

    @test("decorator arg not a valid identifier - required_if")
    def _f(self):
        try:
            @required_if('-a', 'a, a-b, b, 99')
            class root(ConfigRoot):
                pass
            fail ("Expected exception")
        except ConfigDefinitionException  as ex:
            assert ex.message == "['-a', 'a-b', '99'] are not valid identifiers"


    @test("required attributes - inherited, missing")
    def _g(self):
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

    @test("required attributes - inherited, redefined")
    def _h(self):
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

#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno

from multiconf import ConfigRoot, ConfigItem, ConfigException
from multiconf.envs import Env, EnvGroup
from multiconf.decorators import *

dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
g_dev2 = EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = Env('dev3CT')
dev3st = Env('dev3ST')
g_dev3 = EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = EnvGroup('g_dev', g_dev2, g_dev3)

pp = Env('pp')
prod = Env('prod')
g_prod = EnvGroup('g_prod', pp, prod)

valid_envs = EnvGroup('g_all', g_dev, g_prod)

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


@repeat()
class RepeatableItem(ConfigItem):
    pass

    
class ErrorsTest(unittest.TestCase):
    @test("valid_envs arg as EnvGroup")
    def _a(self):
        ok (lazy(ConfigRoot, prod, valid_envs)).raises(ConfigException)

    @test("valid_envs arg as str")
    def _b(self):
        ok (lazy(ConfigRoot, prod, "abc")).raises(ConfigException)

    @test("valid_envs arg contains non Env")
    def _c(self):
        ok (lazy(ConfigRoot, prod, [g_prod, 'a'])).raises(ConfigException)

    @test("selected_conf not in valid_envs")
    def _d(self):
        ok (lazy(ConfigRoot, prod, [dev3ct, dev3st])).raises(ConfigException)

    @test("assign to undefine env")
    def _e(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod]) as cr:
                    errorline = lineno() + 1
                    cr.a(pros="hello", prod="hi")
                fail ("Expected exception")
        except ConfigException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "No such Env or EnvGroup: 'pros'")
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("value not assigned to all envs")
    def _f(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod, pp]) as cr:
                    errorline = lineno() + 1
                    cr.a(prod="hello")
                fail ("Expected exception")
        except ConfigException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "Attribute: 'a' did not receive a value for env Env('pp')")
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("property defined with different types")
    def _g(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod, pp]) as cr:
                    errorline = lineno() + 1
                    cr.a(prod=1, pp="hello")
                fail ("Expected exception")
        except ConfigException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "Found different types of property 'a' for different envs: <type 'int'> previously found types: [<type 'str'>]")
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("property redefined")
    def _g(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod]) as cr:
                    cr.a(prod=1)
                    errorline = lineno() + 1
                    cr.a(prod=2)
                fail ("Expected exception")
        except ConfigException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "Redefined attribute 'a'")
            ok (ex.message) == "Attribute redefinition error: 'a'"

    @test("nested item overrides simple property")
    def _h(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                cr.ConfigItem(prod="hello")
                ConfigItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "'ConfigItem' is defined both as simple value and a contained item: ConfigItem {\n}"

    @test("nested repeatable item overrides simple property - not contained in repeatable")
    def _i(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                cr.RepeatableItems(prod="hello")
                RepeatableItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "'RepeatableItems': RepeatableItems {\n} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"

    #@test("nested repeatable item overrides simple property - contained in repeatable")
    #@todo
    #def _i2(self):
    #    try:
    #        @nested_repeatables('children')
    #        class root(ConfigRoot):
    #            pass
    #
    #        @named_as('children')
    #        class rchild(RepeatableItem):
    #            pass
    #
    #        with root(prod, [prod]) as cr:
    #            # TODO
    #            #cr.children(prod="hello")
    #            rchild()
    #        fail ("Expected exception")
    #    except ConfigException as ex:
    #        ok (ex.message) == "'children' is defined both as simple value and a contained item: children {\n}"

    @test("simple property overrides contained item")
    def _j(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod]) as cr:
                    ConfigItem()
                    errorline = lineno() + 1
                    cr.ConfigItem(prod="hello")
                fail ("Expected exception")
        except ConfigException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "Redefined attribute 'ConfigItem'")
            ok (ex.message) == "Attribute redefinition error: 'ConfigItem'"

    @test("repeated non-repeatable item")
    def _k(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                ConfigItem()
                errorline = lineno() + 1
                ConfigItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Repeated non repeatable conf item: 'ConfigItem'"


if __name__ == '__main__':
    unittest.main()

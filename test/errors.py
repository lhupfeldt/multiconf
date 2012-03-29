#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import unittest
from oktest import ok, test, fail, todo

from multiconf.multiconf import ConfigRoot, ConfigItem, ConfigException
from multiconf.envs import Env, EnvGroup

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

def lazy(*args):
    return lambda: args[0](*args[1:])

class ErrorsTest(unittest.TestCase):
    @test("valid_envs arg as EnvGroup")
    def _0(self):
        ok (lazy(ConfigRoot, prod, valid_envs)).raises(ConfigException)

    @test("valid_envs arg as str")
    def _1(self):
        ok (lazy(ConfigRoot, prod, "abc")).raises(ConfigException)

    @test("valid_envs arg contaings non Env")
    def _2(self):
        ok (lazy(ConfigRoot, prod, [g_prod, 'a'])).raises(ConfigException)

    @test("selected_conf not in valid_envs")
    def _3(self):
        ok (lazy(ConfigRoot, prod, [dev3ct, dev3st])).raises(ConfigException)

    @test("assign to undefine env")
    def _4(self):
        try:
            with ConfigRoot(prod, [prod, pp]) as cr:
                cr.pros.a = "hello"
            fail ("Expected exception")
        except ConfigException as ex:
            # TODO message!
            ok (ex.message) == "pros"

    @test("value not assigned to all confs")
    def _5(self):
        try:
            with ConfigRoot(prod, [prod, pp]) as cr:
                cr.prod.a = "hello"
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Attribute: 'a' did not receive a value for Env('pp')"

    @test("nested item overrides simple property")
    def _6(self):
        try:
            with ConfigRoot(prod, [prod, pp]) as cr:
                cr.prod.ConfigItem = "hello"
                ConfigItem(repeat=False)
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "'ConfigItem' is defined both as simple value and a contained item ConfigItem {\n}"

    @test("nested repeatable item overrides simple property")
    def _7(self):
        try:
            with ConfigRoot(prod, [prod, pp]) as cr:
                cr.prod.ConfigItems = "hello"
                ConfigItem(repeat=True)
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "'ConfigItems' is defined both as simple value and a contained item ConfigItem {\n}"
    
    @test("simple property overrides contained item")
    @todo
    def _8(self):
        try:
            with ConfigRoot(prod, [prod, pp]) as cr:
                ConfigItem(repeat=False)
                cr.prod.ConfigItem = "hello"
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "'ConfigItem' is defined both as simple value and a contained item ConfigItem {\n}"

    @test("property defined with different types")
    def _9(self):
        try:
            with ConfigRoot(prod, [prod, pp]) as cr:
                cr.pp.a = "hello"
                cr.prod.a = 1
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Found different types of property 'a' for different envs: <type 'str'> previous type: <type 'int'>"

if __name__ == '__main__':
    unittest.main()

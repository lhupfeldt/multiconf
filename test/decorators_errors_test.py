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

from multiconf import ConfigRoot, ConfigItem, ConfigException, NoAttributeException
from multiconf.decorators import required, required_if, optional
from multiconf.envs import Env, EnvGroup

dev2ct = Env('dev2ct')
dev2st = Env('dev2st')
g_dev2 = EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = Env('dev3ct')
dev3st = Env('dev3st')
g_dev3 = EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = EnvGroup('g_dev', g_dev2, g_dev3)

pp = Env('pp')
prod = Env('prod')
g_prod = EnvGroup('g_prod', pp, prod)

valid_envs = EnvGroup('g_all', g_dev, g_prod)

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

class DecoratorsTest(unittest.TestCase):
    @test("required attributes missing - configroot")
    def _a(self):
        try:
            @required('someattr1, someattr2')
            class root(ConfigRoot):
                pass

            with root(prod, [prod]) as cr:
                pass
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "No value given for required attributes: ['someattr1', 'someattr2']"

    @test("required attributes missing - configitem")
    def _b(self):
        try:
            class root(ConfigRoot):
                pass

            @required('abcd, efgh, ijkl')
            class item(ConfigItem):
                pass

            with root(prod, [prod]) as cr:
                with item(True) as ii:
                    ii.efgh(prod=7)

            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "No value given for required attributes: ['abcd', 'ijkl']"


    @test("required_if attributes missing")
    def _c(self):
        try:
            class root(ConfigRoot):
                pass

            @required_if('abcd', 'efgh, ijkl')
            class item(ConfigItem):
                pass

            with root(prod, [prod]) as cr:
                with item(True) as ii:
                    ii.abcd(prod=1)

            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Missing required_if attributes. Condition attribute: 'abcd'==1, missing: ['efgh', 'ijkl']"

    @test("optional attribute accessed for env where not specified")
    def _d(self):
        @optional('a')
        class root(ConfigRoot):
            pass

        try:
            with root(prod, [prod, dev2ct]) as cr:
                cr.a(dev2ct=18)

            print cr.a
            fail ("Expected exception")
        except NoAttributeException  as ex:
            ok (ex.message) == "Attribute 'a' undefined for env Env('prod')"


if __name__ == '__main__':
    unittest.main()

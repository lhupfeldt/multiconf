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

from multiconf.multiconf import ConfigRoot, ConfigItem, ConfigException, required, required_if
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
    def _a(self):
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
    def _a(self):
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


if __name__ == '__main__':
    unittest.main()

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
from multiconf.decorators import *
from multiconf.envs import Env, EnvGroup

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

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

class DecoratorsTest(unittest.TestCase):
    @test("required attributes - configroot")
    def _a(self):
        @required('anattr, anotherattr')
        class root(ConfigRoot):
            pass

        with root(prod, [prod]) as cr:
            cr.anattr(prod=1)
            cr.anotherattr(prod=2)
        ok (cr.anattr) == 1
        ok (cr.anotherattr) == 2

    @test("required attributes - configitem")
    def _b(self):
        class root(ConfigRoot):
            pass

        @required('a, b')
        class item(ConfigItem):
            pass

        with root(prod, [prod]) as cr:
            with item(False) as ii:
                ii.a(prod=1)
                ii.b(prod=2)

        ok (cr.item.a) == 1
        ok (cr.item.b) == 2


    @test("required attributes - accept override of single property")
    def _c(self):
        class root(ConfigRoot):
            pass

        @required('a, b')
        class item(ConfigItem):
            def __init__(self, a, b):
                super(item, self).__init__(repeat=False, a=a, b=b)

        with root(prod, [prod]) as cr:
            with item(a=1, b=1) as ii:
                ii.b(prod=2)

        ok (cr.item.a) == 1
        ok (cr.item.b) == 2


    @test("required_if attributes - condition true and condition unset")
    def _d(self):
        @required_if('a', 'b, c')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, dev2ct]) as cr:
            cr.a(prod=1)
            cr.b(prod=2)
            cr.c(prod=3)

        ok (cr.a) == 1
        ok (cr.b) == 2
        ok (cr.c) == 3

    @test("required_if attributes - condition false")
    def _e(self):
        @required_if('a', 'b, c')
        class root(ConfigRoot):
            pass

        with root(prod, [prod]) as cr:
            cr.a(prod=0)
            cr.b(prod=1)

        ok (cr.a) == 0
        ok (cr.b) == 1

    @test("optional attribute")
    def _f(self):
        @optional('a')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, dev2ct]) as cr:
            cr.a(dev2ct=18)
        ok ("no-exception") == "no-exception"

        with root(prod, [prod, dev2ct]) as cr:
            cr.a(prod=17)
        ok (cr.a) == 17

    @test("named_as")
    def _f(self):
        @named_as('project')
        class root(ConfigRoot):
            pass

        proj = root(prod, [prod, dev2ct], name='abc')            
        ok (repr(proj)) == "project {\n}"

if __name__ == '__main__':
    unittest.main()

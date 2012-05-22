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
from multiconf.decorators import  required, required_if, nested_repeatables, named_as, repeat, optional
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
            with item() as ii:
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
                super(item, self).__init__(a=a, b=b)

        with root(prod, [prod]) as cr:
            with item(a=1, b=1) as ii:
                ii.b(prod=2)

        ok (cr.item.a) == 1
        ok (cr.item.b) == 2


    @test("required_if attributes - condition true (prod) and condition unset (dev2ct)")
    def _d(self):
        @required_if('a', 'b, c')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, dev2ct]) as cr:
            cr.a(prod=10)
            cr.b(prod=20)
            cr.c(prod=30)

        ok (cr.a) == 10
        ok (cr.b) == 20
        ok (cr.c) == 30

        # Test iteritems
        expected_keys = ['a', 'b', 'c']
        index = 0
        for key, val in cr.iteritems():
            ok (key) == expected_keys[index]
            ok (val) == (index + 1) * 10
            index += 1

    @test("required_if attributes - condition false")
    def _e(self):
        @required_if('a', 'b, c')
        class root(ConfigRoot):
            pass

        with root(prod, [prod]) as cr:
            cr.a(prod=0)
            cr.b(prod=10)

        ok (cr.a) == 0
        ok (cr.b) == 10

        # Test iteritems
        expected_keys = ['a', 'b']
        index = 0
        for key, val in cr.iteritems():
            ok (key) == expected_keys[index]
            ok (val) == index * 10
            index += 1

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
    def _g(self):
        @named_as('project')
        class root(ConfigRoot):
            pass

        proj = root(prod, [prod, dev2ct], name='abc')
        ok (repr(proj)) == "project {\n}"


if __name__ == '__main__':
    unittest.main()

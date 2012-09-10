#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import  required, required_if, nested_repeatables, named_as, repeat, optional

from ..envs import EnvFactory

ef = EnvFactory()

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

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

_g_expected = """{
    "__class__": "root #as: 'project', id: 0000", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "name": "abc"
}"""

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

        proj = root(prod, [prod, dev2ct], name='abc').freeze()
        ok (replace_ids(repr(proj), named_as=False)) == _g_expected

    @test("required attributes - inherited, ok")
    def _h(self):
        @required('anattr, anotherattr')
        class root(ConfigRoot):
            pass

        @required('someattr2, someotherattr2')
        class root2(root):
            pass

        with root2(prod, [prod]) as cr:
            cr.anattr(prod=1)
            cr.anotherattr(prod=2)
            cr.someattr2(prod=3)
            cr.someotherattr2(prod=4)
        ok (cr.anattr) == 1
        ok (cr.anotherattr) == 2
        ok (cr.someattr2) == 3
        ok (cr.someotherattr2) == 4

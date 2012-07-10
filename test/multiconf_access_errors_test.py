#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import nested_repeatables, named_as, repeat
from ..envs import Env, EnvGroup

prod = Env('prod')

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

class MultiConfAccessErrorsTest(unittest.TestCase):
    @test("access undefined attribute")
    def _a(self):
        cr = ConfigRoot(prod, [prod])

        try:
            print cr.b
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "ConfigRoot {\n} has no attribute 'b'"

    @test("find_contained_in(named_as) - not found")
    def _b(self):
        @named_as('someitems')
        @nested_repeatables('someitems')
        @repeat()
        class NestedRepeatable(ConfigItem):
            pass

        @named_as('x')
        @nested_repeatables('someitems')
        class X(ConfigItem):
            pass

        @named_as('y')
        class Y(ConfigItem):
            pass

        @nested_repeatables('someitems')
        class root(ConfigRoot):
            pass

        with root(prod, [prod], a=0) as cr:
            NestedRepeatable()
            with X() as ci:
                ci.a(prod=0)
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c')
                    with X() as ci:
                        ci.a(prod=1)
                        with NestedRepeatable(id='d') as ci:
                            ci.a(prod=2)
                            with Y() as ci:
                                ci.a(prod=3)

        try:
            cr.x.someitems['b'].x.someitems['d'].y.find_contained_in(named_as='notthere').a
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Could not find a parent container named as: 'notthere' in hieracy with names: ['someitems', 'x', 'someitems', 'x', 'root']"


    @test("find_attribute(attribute_name) - not found")
    def _k(self):
        @named_as('someitems')
        @nested_repeatables('someitems')
        @repeat()
        class NestedRepeatable(ConfigItem):
            pass

        @named_as('x')
        @nested_repeatables('someitems')
        class X(ConfigItem):
            pass

        @nested_repeatables('someitems')
        class root(ConfigRoot):
            pass

        with root(prod, [prod], a=0, q=17) as cr:
            NestedRepeatable()
            with X() as ci:
                ci.a(prod=0)
                NestedRepeatable(id='a', a=9)
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c', a=7)
                    with X() as ci:
                        ci.b(prod=1)
                        with NestedRepeatable(id='d') as ci:
                            ci.a(prod=2)
                            with X() as ci:
                                ci.a(prod=3)
                    
        try:
            ok (cr.x.someitems['b'].x.someitems['d'].x.find_attribute('e')) == 3
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Could not find an attribute named: 'e' in hieracy with names: ['x', 'someitems', 'x', 'someitems', 'x', 'root']"

    # TODO
    #@test("error in property method implementation")
    #def _l(self):
    #    class root(ConfigRoot):
    #        pass
    #
    #    @named_as('x')
    #    class X(ConfigItem):
    #        @property
    #        def method(self):
    #            # Cheat pylint by getting string from dict
    #            a = {1:""}
    #            return a[1].nosuchprop
    #
    #    with root(prod, [prod]) as cr:
    #        X()
    #                
    #    try:
    #        a = cr.x.method
    #        fail ("Expected exception, but a " + repr(a) + " got a value")
    #    except ConfigException as ex:
    #        ok (ex.message) == ""


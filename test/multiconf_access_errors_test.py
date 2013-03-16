#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import test, fail

from .utils import config_error, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import nested_repeatables, named_as, repeat
from ..envs import EnvFactory

ef = EnvFactory()

prod = ef.Env('prod')

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_a1_expected_repr = """{
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }
} has no attribute 'b'"""


_a2_expected_repr = """{
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "bs": 4
} has no attribute 'b', but found attribute 'bs'"""


class MultiConfAccessErrorsTest(unittest.TestCase):
    @test("access undefined attribute")
    def _a(self):
        with ConfigRoot(prod, [prod]) as cr:
            pass

        try:
            print cr.b
            fail ("Expected exception")
        except AttributeError as ex:
            assert replace_ids(ex.message, named_as=False) == _a1_expected_repr

    @test("access undefined attribute - but has repeatable? attribute with attribute name+s")
    def _a2(self):
        with ConfigRoot(prod, [prod]) as cr:
            cr.setattr('bs', prod=4)

        try:
            print cr.b
            fail ("Expected exception")
        except AttributeError as ex:
            assert replace_ids(ex.message, named_as=False) == _a2_expected_repr

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
                ci.setattr('a', prod=0)
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c')
                    with X() as ci:
                        ci.setattr('a', prod=1)
                        with NestedRepeatable(id='d') as ci:
                            ci.setattr('a', prod=2)
                            with Y() as ci:
                                ci.setattr('a', prod=3)

        try:
            cr.x.someitems['b'].x.someitems['d'].y.find_contained_in(named_as='notthere').a
            fail ("Expected exception")
        except ConfigException as ex:
            assert ex.message == "Could not find a parent container named as: 'notthere' in hieracy with names: ['someitems', 'x', 'someitems', 'x', 'root']"


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
                ci.setattr('a', prod=0)
                NestedRepeatable(id='a', a=9)
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c', a=7)
                    with X() as ci:
                        ci.setattr('b', prod=1)
                        with NestedRepeatable(id='d') as ci:
                            ci.setattr('a', prod=2)
                            with X() as ci:
                                ci.setattr('a', prod=3)
                    
        try:
            assert cr.x.someitems['b'].x.someitems['d'].x.find_attribute('e') == 3
            fail ("Expected exception")
        except ConfigException as ex:
            assert ex.message == "Could not find an attribute named: 'e' in hieracy with names: ['x', 'someitems', 'x', 'someitems', 'x', 'root']"

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
    #        assert ex.message == ""


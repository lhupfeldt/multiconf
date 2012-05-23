#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno

from .. import ConfigRoot, ConfigItem
from ..envs import Env
from ..decorators import nested_repeatables, named_as, repeat

prod = Env('prod')
pp = Env('pp')


@named_as('someitems')
@repeat()
class RepeatableItem(ConfigItem):
    pass


class MulticonfTest(unittest.TestCase):

    @test("contained_in, root_conf")
    def _a(self):
        with ConfigRoot(prod, [prod]) as conf:
            ok (conf.root_conf) == conf
            ok (conf.contained_in) == None

            with ConfigItem() as c1:
                ok (c1.root_conf) == conf
                ok (c1.contained_in) == conf

                with ConfigItem() as c2:
                    ok (c2.root_conf) == conf
                    ok (c2.contained_in) == c1

    @test("nested repeatable items")
    def _b(self):
        @nested_repeatables('children')
        class root(ConfigRoot):
            pass

        @named_as('children')
        @repeat()
        class rchild(ConfigItem):
            pass

        with root(prod, [prod, pp]) as cr:
            with rchild(name="first", aa=1, bb=1) as ci:
                ci.aa(prod=3)

            with rchild(name="second", aa=4) as ci:
                ci.bb(prod=2, pp=17)

            with rchild(name="third") as ci:
                ci.aa(prod=5, pp=18)
                ci.bb(prod=3, pp=19)

        ok (cr.children['first'].bb) == 1
        ok (cr.children['second'].bb) == 2
        ok (cr.children['third'].bb) == 3

        index = 3
        for ci in cr.children.values():
            ok (ci.aa) == index
            index += 1

    @test("empty nested repeatable items")
    def _c(self):
        @nested_repeatables('children')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, pp]) as cr:
            pass

        for ci in cr.children.values():
            fail ("list should be empty")

    @test("iteritems - root, attributes")
    def _d(self):
        with ConfigRoot(prod, [prod, pp], a=1, b=2) as cr:
            pass

        for exp, actual in zip([('a', 1), ('b', 2)], list(cr.iteritems())):
            exp_key, exp_value = exp
            key, value = actual
            ok (exp_key) == key
            ok (exp_value) == value


    @test("iteritems - item, attributes")
    def _e(self):
        with ConfigRoot(prod, [prod, pp]) as cr:
            with ConfigItem(a=1, b=2) as ci:
                pass

        for exp, actual in zip([('a', 1), ('b', 2)], list(ci.iteritems())):
            exp_key, exp_value = exp
            key, value = actual
            ok (exp_key) == key
            ok (exp_value) == value

    @test("property defined with same type and None")
    def _g(self):
        with ConfigRoot(prod, [prod, pp], a=None) as cr:
            cr.a(prod=1, pp=2)
        ok (cr.a) == 1


    @test("automatic freeze on attr access outside of with statement")
    def _h(self):
        with ConfigRoot(prod, [prod, pp], a=0) as cr:
            ConfigItem(something=1)
        ok (cr.ConfigItem.something) == 1


    @test("automatic contained item freeze on exit")
    def _i(self):
        @named_as('someitems')
        @nested_repeatables('someitems')
        @repeat()
        class NestedRepeatable(ConfigItem):
            pass

        @nested_repeatables('someitems')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, pp], a=0) as cr:
            NestedRepeatable(id='a')
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='a')
                    with NestedRepeatable(id='b') as ci:
                        ci.a(prod=1, pp=2)
                    NestedRepeatable(id='c', something=1)
                NestedRepeatable(id='c', something=2)
            NestedRepeatable(id='c', something=3)

        ok (repr(cr).find("frozen")) == -1
        ok (len(cr.someitems['a'].someitems)) == 0
        ok (len(cr.someitems['b'].someitems)) == 3
        ok (len(cr.someitems['c'].someitems)) == 0

        ids = ['a', 'b', 'c']
        index = 0
        for item_id, item in cr.someitems['b'].someitems.iteritems():
            ok (item.id) == ids[index]
            ok (item_id) == ids[index]
            index += 1
        ok (index) == 3

        ok (cr.someitems['b'].someitems['b'].someitems['b'].a) == 1

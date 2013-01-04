#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

import unittest
from oktest import ok, test, fail

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..decorators import nested_repeatables, named_as, repeat, required, override
from ..envs import EnvFactory

ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class root(ConfigRoot):
    pass


@named_as('children')
@repeat()
class rchild(ConfigItem):
    pass


@named_as('recursive_items')
@nested_repeatables('recursive_items')
@repeat()
class NestedRepeatable(ConfigItem):
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
    def _nested_repeatable1(self):
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
    def _nested_repeatable2(self):
        with root(prod, [prod, pp]) as cr:
            pass

        for ci in cr.children.values():
            fail ("list should be empty")

    @test("unnamed nested repeatable item (no 'name' or 'id')")
    def _nested_repeatable3(self):
        with root(prod, [prod, pp]) as cr:
            with rchild(aa=1, bb=1) as ci:
                ci.aa(prod=3)
            ci_id = id(ci)

        ok (cr.children[ci_id].aa) == 3

    @test("unnamed nested repeatable item (no default 'name' or 'id')")
    def _nested_repeatable4(self):
        with root(prod, [prod, pp]) as cr:
            with rchild(aa=1, bb=1) as ci:
                ci.name(prod='somevalue', pp='another')
            ci_id = id(ci)

        ok (cr.children[ci_id].aa) == 1
        ok (cr.children[ci_id].name) == 'somevalue'
            

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

    @test("automatic freeze of child on exit")
    def _freeze0(self):
        with ConfigRoot(prod, [prod, pp], a=0) as cr:
            ConfigItem(something=1)
        ok (cr.ConfigItem.something) == 1

    @test("automatic freeze of previous sibling")
    def _freeze1(self):
        class X(ConfigItem):
            def __init__(self):
                super(X, self).__init__()
                ok (self.contained_in.children['a'].x) == 18

        with root(prod, [prod, pp], a=0):
            rchild(id='a', x=18)
            X()

    @test("automatic contained item freeze on exit")
    def _freeze2(self):
        @nested_repeatables('recursive_items')
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

        ok (len(cr.recursive_items['a'].recursive_items)) == 0
        ok (len(cr.recursive_items['b'].recursive_items)) == 3
        ok (len(cr.recursive_items['c'].recursive_items)) == 0

        ids = ['a', 'b', 'c']
        index = 0
        for item_id, item in cr.recursive_items['b'].recursive_items.iteritems():
            ok (item.id) == ids[index]
            ok (item_id) == ids[index]
            index += 1
        ok (index) == 3

        ok (cr.recursive_items['b'].recursive_items['b'].recursive_items['b'].a) == 1

    @test("automatic freeze of property defined in with_statement")
    def _freeze3(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a') as rc:
                rc.y(prod=1, pp=2)

                ok (rc.y) == 1

    @test("automatic freeze of property overridden in with_statement")
    def _freeze4(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a', y=18) as rc:
                rc.y(prod=7, pp=2)

                ok (rc.y) == 7

    @test("explicit freeze of all defined properties")
    def _freeze5(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a', x=17, z=18) as rc:
                rc.y(prod=7, pp=2)
                rc.z(pp=3)
                rc.freeze()

                ok (rc.y) == 7
                ok (rc.x) == 17
                ok (rc.z) == 18

    @test("explicit freeze of single property")
    def _freeze6(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a', x=19, z=20) as rc:
                rc.y(prod=7, pp=2)
                ok (rc.y) == 7
                rc.z(pp=3)
                ok (rc.z) == 20
                rc.x.freeze()
                ok (rc.x) == 19


    # TODO: allow this (while inside with statement only)
    #@test("define new attribute after freeze")
    #def _freeze6(self):
    #    with root(prod, [prod, pp], a=0):
    #        with rchild(id='a', x=19, z=20) as rc:
    #            rc.y(prod=7, pp=2)
    #            ok (rc.y) == 7
    #            rc.z(pp=3)
    #            ok (rc.z) == 20
    #            rc.freeze()
    #            ok (rc.x) == 19
    #            rc.a(prod=3, pp=4)
    #            ok (rc.a) == 3

    @test("find_contained_in(named_as)")
    def _j(self):
        @named_as('x')
        @nested_repeatables('recursive_items')
        class X(ConfigItem):
            pass

        @named_as('y')
        class Y(ConfigItem):
            pass

        @nested_repeatables('recursive_items')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, pp], a=0) as cr:
            NestedRepeatable()
            with X() as ci:
                ci.a(prod=0, pp=2)
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c')
                    with X() as ci:
                        ci.a(prod=1, pp=2)
                        with NestedRepeatable(id='d') as ci:
                            ci.a(prod=2, pp=2)
                            with Y() as ci:
                                ci.a(prod=3, pp=2)
                    
        ok (cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='x').a) == 1
        ok (cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='root').a) == 0
        ok (cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='recursive_items').a) == 2
        ok (cr.x.recursive_items['b'].x.find_contained_in(named_as='x').a) == 0

    @test("find_attribute(attribute_name)")
    def _k(self):
        @named_as('x')
        @nested_repeatables('recursive_items')
        class X(ConfigItem):
            pass

        @nested_repeatables('recursive_items')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, pp], a=-1, q='q0') as cr:
            NestedRepeatable()
            with X() as ci:
                ci.a(prod=0, pp=20)
                NestedRepeatable(id='a', a=9)
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c', a=7)
                    with X() as ci:
                        ci.b(prod='b1', pp='b21')
                        with NestedRepeatable(id='d') as ci:
                            ci.a(prod=2, pp=22)
                            with X() as ci:
                                ci.a(prod=3, pp=23)
                    
        ok (cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('a')) == 3
        ok (cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('b')) == 'b1'
        ok (cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('recursive_items')['d'].a) == 2
        ok (cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('q')) == 'q0'
        ok (cr.x.recursive_items['b'].x.find_attribute(attribute_name='a')) == 0

    @test("ConfigBuilder - override")
    def _l(self):
        @repeat()
        @named_as('xses')
        class X(ConfigItem):
            pass
        
        @required('b')
        @override('a')
        class XBuilder(ConfigBuilder):
            def __init__(self, num_servers=4, **kwargs):
                super(XBuilder, self).__init__(num_servers=num_servers, **kwargs)
        
            def build(self):
                for server_num in xrange(1, self.num_servers+1):
                    with X(name='server%d' % server_num, server_num=server_num) as c:
                        c.something(prod=1, pp=2)
                        self.override(c, 'b', 'something')

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            pass

        with Root(prod, [prod, pp]) as cr:
            with XBuilder(a=1, something=7) as xb:
                xb.num_servers(pp=2)
                xb.b(prod=3, pp=4)
                    
        ok (len(cr.xses)) == 4
        ok (cr.xses['server1'].a) == 1
        ok (cr.xses['server2'].b) == 3
        ok (cr.xses['server4'].b) == 3
        ok (cr.xses['server1'].something) == 7
        ok (cr.xses['server4'].something) == 7
        ok (cr.xses['server1'].server_num) == 1
        ok (cr.xses['server3'].server_num) == 3
        ok (cr.xses['server4'].server_num) == 4
        # TODO: override of conditional attributes (required_if)

    @test("ConfigBuilder - build at freeze")
    def _l2(self):
        @repeat()
        @named_as('xses')
        class X(ConfigItem):
            pass
        
        class XBuilder(ConfigBuilder):
            def __init__(self, num_servers=4, **kwargs):
                super(XBuilder, self).__init__(num_servers=num_servers, **kwargs)
        
            def build(self):
                for server_num in xrange(1, self.num_servers+1):
                    with X(name='server%d' % server_num) as c:
                        pass

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            pass

        with Root(prod, [prod, pp]) as cr:
            XBuilder(a=1)
                    
        ok (len(cr.xses)) == 4
        for ii in 1, 2, 3, 4:
            name = 'server' + repr(ii)
            ok (cr.xses[name].name) == name

    @test("ConfigBuilder - access to contained_in from build")
    def _l3(self):
        @named_as('x')
        class X(ConfigItem):
            pass
        
        class XBuilder(ConfigBuilder):
            def build(self):
                with X(number=self.contained_in.aaa):
                    pass

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 7

        with Root(prod, [prod, pp]) as cr:
            XBuilder()
                    
        ok (cr.x.number) == 7

    @test("ConfigBuilder - access to contained_in from __init__")
    def _l4(self):
        @named_as('x')
        class X(ConfigItem):
            pass

        class XBuilder(ConfigBuilder):
            def __init__(self):
                super(XBuilder, self).__init__()
                self.number(default=self.contained_in.aaa)

            def build(self):
                with X(number=self.number):
                    pass

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 7

        with Root(prod, [prod, pp]) as cr:
            cr.freeze()
            XBuilder()

        ok (cr.x.number) == 7

    @test("env value overrides group value")
    def _m(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem() as ci:
                ci.aa(prod=1, g_prod_like=2)
                ci.bb(g_prod_like=2, prod=3)

        ok (cr1.ConfigItem.aa) == 1
        ok (cr1.ConfigItem.bb) == 3

    @test("group value overrides default value")
    def _n(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=1, bb=3) as ci:
                ci.aa(g_prod_like=2)
                ci.bb(pp=4)

        ok (cr1.ConfigItem.aa) == 2
        ok (cr1.ConfigItem.bb) == 3

    @test("env value overrides default value")
    def _o(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=1, bb=3) as ci:
                ci.aa(prod=2)
                ci.bb(pp=4)

        ok (cr1.ConfigItem.aa) == 2
        ok (cr1.ConfigItem.bb) == 3

    @test("env value overrides group value and default value")
    def _p(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=0) as ci:
                ci.aa(prod=1, g_prod_like=2)
                ci.bb(g_prod_like=2, prod=3)

        ok (cr1.ConfigItem.aa) == 1
        ok (cr1.ConfigItem.bb) == 3

    @test("attribute is an OrderedDict")
    def _q(self):
        class y(ConfigItem):
            pass

        with ConfigRoot(prod, [prod, pp]) as cr1:
            x = y(aa=0)
            od = OrderedDict(((None, 1), ('foo', x)))
            ConfigItem(aa=od)

        ok (cr1.ConfigItem.aa) == od

    @test("attribute is a Sequence")
    def _q2(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            seq = []
            ConfigItem(aa=seq)

        ok (cr1.ConfigItem.aa) == seq

    @test("get valid_envs")
    def _r(self):
        ve = [prod, pp]
        with ConfigRoot(prod, ve) as cr:
            ConfigItem()

        ok (cr.valid_envs) == ve
        ok (cr.ConfigItem.valid_envs) == ve

    @test("required attributes - not required on imtermediate freeze - configroot")
    def _freeze_validation1(self):
        @required('anattr, anotherattr')
        class root(ConfigRoot):
            pass

        with root(prod, [prod]) as cr:
            cr.anattr(prod=1)
            ok (cr.anattr) == 1
            cr.freeze()
            cr.anotherattr(prod=2)
            ok (cr.anotherattr) == 2

    @test("required attributes - not required on imtermediate freeze - configitem")
    def _freeze_validation2(self):
        class root(ConfigRoot):
            pass

        @required('a, b')
        class item(ConfigItem):
            pass

        with root(prod, [prod]) as cr:
            with item() as ii:
                ii.a(prod=1)
                ok (cr.item.a) == 1
                ii.freeze()
                ii.b(prod=2)
                ok (cr.item.b) == 2

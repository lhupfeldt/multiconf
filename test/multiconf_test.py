#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

import unittest
from oktest import test

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..decorators import nested_repeatables, named_as, repeat, required
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


@named_as('xses')
@repeat()
class Xses(ConfigItem):
    pass


@named_as('x_children')
@repeat()
class XChild(ConfigItem):
    pass        
        

class MulticonfTest(unittest.TestCase):

    @test("contained_in, root_conf")
    def _a(self):
        with ConfigRoot(prod, [prod]) as conf:
            assert conf.root_conf == conf
            assert conf.contained_in == None

            with ConfigItem() as c1:
                assert c1.root_conf == conf
                assert c1.contained_in == conf

                with ConfigItem() as c2:
                    assert c2.root_conf == conf
                    assert c2.contained_in == c1

    @test("nested repeatable items")
    def _nested_repeatable1(self):
        with root(prod, [prod, pp]) as cr:
            with rchild(name="first", aa=1, bb=1) as ci:
                ci.setattr('aa', prod=3)

            with rchild(name="second", aa=4) as ci:
                ci.setattr('bb', prod=2, pp=17)

            with rchild(name="third") as ci:
                ci.setattr('aa', prod=5, pp=18)
                ci.setattr('bb', prod=3, pp=19)

        assert cr.children['first'].bb == 1
        assert cr.children['second'].bb == 2
        assert cr.children['third'].bb == 3

        index = 3
        for ci in cr.children.values():
            assert ci.aa == index
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
                ci.setattr('aa', prod=3)
            ci_id = id(ci)

        assert cr.children[ci_id].aa == 3

    @test("unnamed nested repeatable item (no default 'name' or 'id')")
    def _nested_repeatable4(self):
        with root(prod, [prod, pp]) as cr:
            with rchild(aa=1, bb=1) as ci:
                ci.setattr('name', prod='somevalue', pp='another')
            ci_id = id(ci)

        assert cr.children[ci_id].aa == 1
        assert cr.children[ci_id].name == 'somevalue'
            

    @test("iteritems - root, attributes")
    def _d(self):
        with ConfigRoot(prod, [prod, pp], a=1, b=2) as cr:
            pass

        for exp, actual in zip([('a', 1), ('b', 2)], list(cr.iteritems())):
            exp_key, exp_value = exp
            key, value = actual
            assert exp_key == key
            assert exp_value == value

    @test("iteritems - item, attributes")
    def _e(self):
        with ConfigRoot(prod, [prod, pp]) as cr:
            with ConfigItem(a=1, b=2) as ci:
                pass

        for exp, actual in zip([('a', 1), ('b', 2)], list(ci.iteritems())):
            exp_key, exp_value = exp
            key, value = actual
            assert exp_key == key
            assert exp_value == value

    @test("property defined with same type and None")
    def _g1(self):
        with ConfigRoot(prod, [prod, pp], a=None) as cr:
            cr.setattr('a', prod=1, pp=2)
        assert cr.a == 1

    @test("property defined with None and same type")
    def _g2(self):
        with ConfigRoot(prod, [prod, pp], a=1) as cr:
            cr.setattr('a', prod=None, pp=2)
        assert cr.a == None

    @test("automatic freeze of child on exit")
    def _freeze0(self):
        with ConfigRoot(prod, [prod, pp], a=0) as cr:
            ConfigItem(something=1)
        assert cr.ConfigItem.something == 1

    @test("automatic freeze of previous sibling")
    def _freeze1(self):
        class X(ConfigItem):
            def __init__(self):
                super(X, self).__init__()
                assert self.contained_in.children['a'].x == 18

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
                        ci.setattr('a', prod=1, pp=2)
                    NestedRepeatable(id='c', something=1)
                NestedRepeatable(id='c', something=2)
            NestedRepeatable(id='c', something=3)

        assert len(cr.recursive_items['a'].recursive_items) == 0
        assert len(cr.recursive_items['b'].recursive_items) == 3
        assert len(cr.recursive_items['c'].recursive_items) == 0

        ids = ['a', 'b', 'c']
        index = 0
        for item_id, item in cr.recursive_items['b'].recursive_items.iteritems():
            assert item.id == ids[index]
            assert item_id == ids[index]
            index += 1
        assert index == 3

        assert cr.recursive_items['b'].recursive_items['b'].recursive_items['b'].a == 1

    @test("automatic freeze of property defined in with_statement")
    def _freeze3(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a') as rc:
                rc.setattr('y', prod=1, pp=2)
                assert rc.y == 1

    @test("automatic freeze of property overridden in with_statement")
    def _freeze4(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a', y=18) as rc:
                rc.setattr('y', prod=7, pp=2)
                assert rc.y == 7

    @test("explicit freeze of all defined properties")
    def _freeze5(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a', x=17, z=18) as rc:
                rc.setattr('y', prod=7, pp=2)
                rc.setattr('z', pp=3)

                assert rc.y == 7
                assert rc.x == 17
                assert rc.z == 18

    @test("explicit freeze of single property")
    def _freeze6(self):
        with root(prod, [prod, pp], a=0):
            with rchild(id='a', x=19, z=20) as rc:
                rc.setattr('y', prod=7, pp=2)
                assert rc.y == 7
                rc.setattr('z', pp=3)
                assert rc.z == 20
                assert rc.x == 19


    # TODO: allow this (while inside with statement only)
    #@test("define new attribute after freeze")
    #def _freeze6(self):
    #    with root(prod, [prod, pp], a=0):
    #        with rchild(id='a', x=19, z=20) as rc:
    #            rc.setattr('y', prod=7, pp=2)
    #            assert rc.y == 7
    #            rc.setattr('z', pp=3)
    #            assert rc.z == 20
    #            assert rc.x == 19
    #            rc.a(prod=3, pp=4)
    #            assert rc.a == 3

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
                ci.setattr('a', prod=0, pp=2)
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c')
                    with X() as ci:
                        ci.setattr('a', prod=1, pp=2)
                        with NestedRepeatable(id='d') as ci:
                            ci.setattr('a', prod=2, pp=2)
                            with Y() as ci:
                                ci.setattr('a', prod=3, pp=2)
                    
        assert cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='x').a == 1
        assert cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='root').a == 0
        assert cr.x.recursive_items['b'].x.recursive_items['d'].y.find_contained_in(named_as='recursive_items').a == 2
        assert cr.x.recursive_items['b'].x.find_contained_in(named_as='x').a == 0

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
                ci.setattr('a', prod=0, pp=20)
                NestedRepeatable(id='a', a=9)
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='c', a=7)
                    with X() as ci:
                        ci.setattr('b', prod='b1', pp='b21')
                        with NestedRepeatable(id='d') as ci:
                            ci.setattr('a', prod=2, pp=22)
                            with X() as ci:
                                ci.setattr('a', prod=3, pp=23)
                    
        assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('a') == 3
        assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('b') == 'b1'
        assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('recursive_items')['d'].a == 2
        assert cr.x.recursive_items['b'].x.recursive_items['d'].x.find_attribute('q') == 'q0'
        assert cr.x.recursive_items['b'].x.find_attribute(attribute_name='a') == 0

    @test("ConfigBuilder - override")
    def _l(self):
        @required('b')
        class XBuilder(ConfigBuilder):
            def __init__(self, num_servers=4, **kwargs):
                super(XBuilder, self).__init__(num_servers=num_servers, **kwargs)
        
            def build(self):
                for server_num in xrange(1, self.num_servers+1):
                    with Xses(name='server%d' % server_num, server_num=server_num) as c:
                        c.setattr('something', prod=1, pp=2)

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            pass

        with Root(prod, [prod, pp]) as cr:
            with XBuilder(a=1, something=7) as xb:
                xb.setattr('num_servers', pp=2)
                xb.setattr('b', prod=3, pp=4)
                    
        assert len(cr.xses) == 4
        assert cr.xses['server1'].a == 1
        assert cr.xses['server2'].b == 3
        assert cr.xses['server4'].b == 3
        assert cr.xses['server1'].something == 7
        assert cr.xses['server4'].something == 7
        assert cr.xses['server1'].server_num == 1
        assert cr.xses['server3'].server_num == 3
        assert cr.xses['server4'].server_num == 4
        # TODO: override of conditional attributes (required_if)

    @test("ConfigBuilder - build at freeze")
    def _l2(self):
        class XBuilder(ConfigBuilder):
            def __init__(self, num_servers=4, **kwargs):
                super(XBuilder, self).__init__(num_servers=num_servers, **kwargs)
        
            def build(self):
                for server_num in xrange(1, self.num_servers+1):
                    with Xses(name='server%d' % server_num) as c:
                        pass

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            pass

        with Root(prod, [prod, pp]) as cr:
            XBuilder(a=1)
                    
        assert len(cr.xses) == 4
        for ii in 1, 2, 3, 4:
            name = 'server' + repr(ii)
            assert cr.xses[name].name == name

    @test("ConfigBuilder - access to contained_in from build")
    def _l3(self):
        @named_as('y')
        class Y(ConfigItem):
            pass
        
        class YBuilder(ConfigBuilder):
            def build(self):
                with Y(number=self.contained_in.aaa):
                    pass

        @nested_repeatables('ys')
        class Root(ConfigRoot):
            aaa = 7

        with Root(prod, [prod, pp]) as cr:
            YBuilder()
                    
        assert cr.y.number == 7

    @test("ConfigBuilder - access to contained_in from __init__")
    def _l4(self):
        @named_as('x')
        class X(ConfigItem):
            pass

        class XBuilder(ConfigBuilder):
            def __init__(self):
                super(XBuilder, self).__init__()
                self.number = self.contained_in.aaa

            def build(self):
                with X(number=self.number):
                    pass

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 7

        with Root(prod, [prod, pp]) as cr:
            XBuilder()

        assert cr.x.number == 7

    @test("ConfigBuilder - access to contained_in from with-block")
    def _l4b(self):
        @named_as('x')
        class X(ConfigItem):
            pass

        class XBuilder(ConfigBuilder):
            def build(self):
                X()

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 7

        with Root(prod, [prod, pp]) as cr:
            with XBuilder() as xb:
                parent = xb.contained_in

        assert parent == cr

    @test("ConfigBuilder - access to contained_in from built item. Must give parent of Builder.")
    def _l4c(self):
        @named_as('x')
        class X(ConfigItem):
            def __init__(self, **kwargs):
                super(X, self).__init__(**kwargs)
                self.init_parent = self.contained_in

            def validate(self):
                self.validate_parent = self.contained_in

        class XBuilder(ConfigBuilder):
            def __init__(self):
                super(XBuilder, self).__init__()
                self.number = self.contained_in.aaa

            def build(self):
                with X(number=self.number):
                    pass

        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 7

        with Root(prod, [prod, pp]) as cr:
            XBuilder()

        assert cr.x.number == 7
        assert cr.x.init_parent == cr
        assert cr.x.validate_parent == cr

    @test("ConfigBuilder - Nested Items")
    def _l5(self):
        class XBuilder(ConfigBuilder):
            def __init__(self):
                super(XBuilder, self).__init__()
                self.number = self.contained_in.aaa
        
            def build(self):
                for num in xrange(1, self.number+1):
                    with Xses(name='server%d' % num, server_num=num) as c:
                        c.setattr('something', prod=1, pp=2)
        
        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 2
        
        with Root(prod, [prod, pp]) as cr:
            with XBuilder() as xb:
                xb.b = 27
                XChild(a=10)
                XChild(a=11)
        
        assert len(cr.xses) == 2
        for server in 'server1', 'server2':
            index = 10
            for x_child in cr.xses[server].x_children.values():
                assert x_child.a == index
                index += 1
            assert index == 12

    @test("ConfigBuilder - Nested Items - Access to contained_in")
    def _l5b(self):
        class XBuilder(ConfigBuilder):
            def __init__(self):
                super(XBuilder, self).__init__()
                self.number = self.contained_in.aaa
        
            def build(self):
                for num in xrange(1, self.number+1):
                    with Xses(name='server%d' % num, server_num=num) as c:
                        c.setattr('something', prod=1, pp=2)
        
        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 2
        
        with Root(prod, [prod, pp]) as cr:
            with XBuilder() as xb:
                xb.b = 27
                with XChild(a=10) as x1:
                    with_root = x1.contained_in
                XChild(a=11)
        
        assert len(cr.xses) == 2
        for server in 'server1', 'server2':
            index = 10
            for x_child in cr.xses[server].x_children.values():
                assert x_child.a == index
                index += 1
            assert index == 12
        assert with_root == cr

    @test("ConfigBuilder - Multilevel Nested Items - Access to contained_in")
    def _l5c(self):
        class XBuilder(ConfigBuilder):
            def __init__(self, start=1):
                super(XBuilder, self).__init__()
                self.start = start
                self.number = self.contained_in.aaa
        
            def build(self):
                for num in xrange(self.start, self.start + self.number):
                    with Xses(name='server%d' % num, server_num=num) as c:
                        c.setattr('something', prod=1, pp=2)
        
        @nested_repeatables('xses')
        class ItemWithXses(ConfigItem):
            aaa = 2
        
        with ConfigRoot(prod, [prod, pp]) as cr:
            with ItemWithXses() as item:
                with XBuilder() as xb1:
                    xb1.b = 27
                    with XChild(a=10) as x1:
                        xb1_with_item = x1.contained_in
                    with XBuilder(start=3) as xb2:
                        xb2.c = 28
                        with XChild(a=11) as x2:
                            xb2_with_item = x2.contained_in
                        XChild(a=12)


        assert len(item.xses) == 4
        total = 0
        for server in 'server1', 'server2', 'server3', 'server4':
            for x_child in item.xses[server].x_children.values():
                print x_child.a
                total += x_child.a
        assert total == 66
        
        assert xb1_with_item == item
        assert xb2_with_item == item

    @test("ConfigBuilder - repeated")
    def _l6(self):
        class XBuilder(ConfigBuilder):
            def __init__(self, first=1, last=2):
                super(XBuilder, self).__init__()
                self.first = first
                self.last = last
        
            def build(self):
                for num in xrange(self.first, self.last+1):
                    with Xses(name='server%d' % num, server_num=num) as c:
                        c.setattr('something', prod=1, pp=2)
                    self.q = self.last
        
        @nested_repeatables('xses')
        class Root(ConfigRoot):
            aaa = 2
        
        with Root(prod, [prod, pp]) as cr:
            with XBuilder() as xb1:
                XChild(a=10)
                XChild(a=11)
            with XBuilder(first=3) as xb2:
                xb2.last = 3
                XChild(a=10)
        
        assert len(cr.xses) == 3
        total_children = 0
        for server in 'server1', 'server2', 'server3':
            index = 10
            for x_child in cr.xses[server].x_children.values():
                assert x_child.a == index
                index += 1
                total_children += 1
        assert total_children == 5        

        assert len(xb1.what_built()) == 2
        assert isinstance(xb1.what_built(), OrderedDict) == True
        assert xb1.what_built()['q'] == 2

        assert len(xb1.what_built()) == 2
        assert isinstance(xb2.what_built(), OrderedDict) == True
        assert xb2.what_built()['xses']['server3'].something == 1
        assert xb2.what_built()['q'] == 3

    # TODO not yet implemented 'partial' feature
    # @test("ConfigBuilder - Nested Items - override values, extend envs")
    # def _l6(self):
    #     @nested_repeatables('xses, x_children')
    #     class XBuilder(ConfigBuilder):
    #         def __init__(self):
    #             super(XBuilder, self).__init__()
    #             self.number = self.contained_in.aaa
    #     
    #         def build(self):
    #             for num in xrange(1, self.number+1):
    #                 with Xses(name='server%d' % num, server_num=num) as c:
    #                     # This does not list all envs
    #                     c.something(prod=1)
    #     
    #     @nested_repeatables('xses')
    #     class Root(ConfigRoot):
    #         aaa = 2
    #     
    #     with Root(prod, [prod, pp]) as cr:
    #         with XBuilder() as xb:
    #             xb.b = 27)
    #             # Here we finalize the setting of 'something' which was started in the 'build' method
    #             xb.something(pp=2)
    #             XChild(a=10)
    #             XChild(a=11)
    #     
    #     assert len(cr.xses) == 2
    #     index = 10
    #     for x_child in cr.xses['server1'].x_children.values():
    #         assert x_child.a == index
    #         index += 1

    @test("env value overrides group value")
    def _m(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem() as ci:
                ci.setattr('aa', prod=1, g_prod_like=2)
                ci.setattr('bb', g_prod_like=2, prod=3)

        assert cr1.ConfigItem.aa == 1
        assert cr1.ConfigItem.bb == 3

    @test("group value overrides default value - from init")
    def _n1(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=1, bb=3) as ci:
                ci.setattr('aa', g_prod_like=2)
                ci.setattr('bb', pp=4)

        assert cr1.ConfigItem.aa == 2
        assert cr1.ConfigItem.bb == 3

    @test("group value overrides default value - from setattr")
    def _n2(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem() as ci:
                ci.setattr('aa', default=1, g_prod_like=2)

        assert cr1.ConfigItem.aa == 2

    @test("assigned default value overrides default value from init")
    def _n3(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=1) as ci:
                ci.aa = 2

        assert cr1.ConfigItem.aa == 2

    @test("default value from setattr overrides default value from init")
    def _n4(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=1) as ci:
                ci.setattr('aa', default=2, pp=3)

        assert cr1.ConfigItem.aa == 2

    @test("env value overrides default value")
    def _o(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=1, bb=3) as ci:
                ci.setattr('aa', prod=2)
                ci.setattr('bb', pp=4)

        assert cr1.ConfigItem.aa == 2
        assert cr1.ConfigItem.bb == 3

    @test("env value overrides group value and default value")
    def _p(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            with ConfigItem(aa=0) as ci:
                ci.setattr('aa', prod=1, g_prod_like=2)
                ci.setattr('bb', g_prod_like=2, prod=3)

        assert cr1.ConfigItem.aa == 1
        assert cr1.ConfigItem.bb == 3

    @test("attribute is an OrderedDict")
    def _q(self):
        class y(ConfigItem):
            pass

        with ConfigRoot(prod, [prod, pp]) as cr1:
            x = y(aa=0)
            od = OrderedDict(((None, 1), ('foo', x)))
            ConfigItem(aa=od)

        assert cr1.ConfigItem.aa == od

    @test("attribute is a Sequence")
    def _q2(self):
        with ConfigRoot(prod, [prod, pp]) as cr1:
            seq = []
            ConfigItem(aa=seq)

        assert cr1.ConfigItem.aa == seq

    @test("get valid_envs")
    def _r(self):
        ve = [prod, pp]
        with ConfigRoot(prod, ve) as cr:
            ConfigItem()

        assert cr.valid_envs == ve
        assert cr.ConfigItem.valid_envs == ve

    @test("required attributes - not required on imtermediate freeze - configroot")
    def _freeze_validation1(self):
        @required('anattr, anotherattr')
        class root(ConfigRoot):
            pass

        with root(prod, [prod]) as cr:
            cr.setattr('anattr', prod=1)
            assert cr.anattr == 1
            cr.setattr('anotherattr', prod=2)
            assert cr.anotherattr == 2

    @test("required attributes - not required on imtermediate freeze - configitem")
    def _freeze_validation2(self):
        class root(ConfigRoot):
            pass

        @required('a, b')
        class item(ConfigItem):
            pass

        with root(prod, [prod]) as cr:
            with item() as ii:
                ii.setattr('a', prod=1)
                assert cr.item.a == 1
                ii.setattr('b', prod=2)
                assert cr.item.b == 2


    @test("hasattr")
    def _hasattr(self):
        class root(ConfigRoot):
            pass

        with root(prod, [prod]) as cr:
            with ConfigItem(a=1) as ii:
                ii.b = 2
                ii.setattr('c', prod=3)
                assert hasattr(ii, 'd') == False
        
            assert hasattr(ii, 'a') == True
            assert hasattr(ii, 'b') == True
            assert hasattr(ii, 'c') == True
            assert hasattr(ii, 'd') == False

    @test("assigning to attribute - root")
    def _r1(self):
        with root(prod, [prod]) as cr:
            cr.a = 7
        assert cr.a == 7

    @test("assigning to attribute - nested item")
    def _r2(self):
        with root(prod, [prod]) as cr:
            with ConfigItem() as ci:
                ci.a = 1
        assert ci.a == 1

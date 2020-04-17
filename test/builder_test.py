# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict
from pytest import xfail, raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED, ConfigApiException
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory

from .utils.check_containment import check_containment
from .utils.tstclasses import ItemWithName, ItemWithAABB


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')


@named_as('xses')
@nested_repeatables('x_children')
class Xses(RepeatableConfigItem):
    def __init__(self, mc_key, server_num=None):
        super().__init__(mc_key=mc_key)
        self.name = mc_key
        self.server_num = server_num


@named_as('x_children')
class XChild(RepeatableConfigItem):
    def __new__(cls, mc_key):
        return super().__new__(cls, mc_key=mc_key)

    def __init__(self, mc_key):
        super().__init__(mc_key=mc_key)
        self.a = mc_key


def test_configbuilder_with_required_item_decorator():
    @named_as('b_item')
    class BItem(ConfigItem):
        xx = 6

    @required('b_item')
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers, aa):
            super().__init__()
            self.num_servers = num_servers
            self.aa = aa

        def mc_build(self):
            for server_num in range(1, self.num_servers+1):
                with Xses(mc_key='server%d' % server_num, server_num=server_num) as cc:
                    cc.setattr('aa', prod=1, pp=2, mc_set_unknown=True)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder(num_servers=4, aa=7) as xb:
                xb.setattr('num_servers', pp=1)
                BItem()

    cr = config(prod2).Root
    assert len(cr.xses) == 4
    assert cr.xses['server1'].aa == 1  # Note: pre v6 this would have been 7 because of the automatic copy
    assert cr.xses['server4'].aa == 1  # Note: pre v6 this would have been 7 because of the automatic copy
    assert cr.xses['server1'].server_num == 1
    assert cr.xses['server3'].server_num == 3
    assert cr.xses['server4'].server_num == 4
    assert cr.xses['server3'].b_item.xx == 6

    cr = config(pp2).Root
    assert len(cr.xses) == 1
    assert cr.xses['server1'].aa == 2
    assert cr.xses['server1'].server_num == 1

    with raises(KeyError):
        cr.xses['server2']
    with raises(KeyError):
        cr.xses['server3']
    with raises(KeyError):
        cr.xses['server4']


def test_configbuilder_build_with_mc_required():
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers=4, a=MC_REQUIRED, something=None):
            super().__init__()
            self.num_servers = num_servers
            self.a = a
            self.something = something
            self.b = MC_REQUIRED

        def mc_build(self):
            for server_num in range(1, self.num_servers+1):
                print("server_num:", server_num)
                with Xses(mc_key='server%d' % server_num, server_num=server_num) as c:
                    c.setattr('something', prod=1, pp=2, mc_set_unknown=True)
                    c.setattr('none_is_not_used', default=False, mc_set_unknown=True)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder(a=1, something=7) as xb:
                xb.setattr('num_servers', pp=2)
                xb.setattr('b', prod=3, pp=4)
                xb.setattr('none_is_not_used', default=None, mc_set_unknown=True)

    cr = config(prod2).Root
    assert len(cr.xses) == 4
    # assert cr.xses['server1'].a == 1  # Attributes set on builder are no longer automatically set on built items
    # assert cr.xses['server2'].b == 3
    # assert cr.xses['server4'].b == 3
    assert cr.xses['server1'].something == 1  # This would be 7 in pre v6
    assert cr.xses['server4'].something == 1  # This would be 7 in pre v6
    assert cr.xses['server1'].server_num == 1
    assert cr.xses['server3'].server_num == 3
    assert cr.xses['server4'].server_num == 4
    assert cr.xses['server4'].none_is_not_used is False
    check_containment(cr)


def test_configbuilder_override_with_required_item():
    class b(ConfigItem):
        xx = 1

    @required('b')
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers):
            super().__init__()
            self.num_servers = num_servers

        def mc_build(self):
            for server_num in range(1, self.num_servers+1):
                Xses(mc_key='server%d' % server_num, server_num=server_num)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder(4) as xb:
                xb.setattr('num_servers', pp=2)
                b()

    cr = config(prod2).Root
    assert len(cr.xses) == 4
    assert cr.xses['server1'].server_num == 1
    assert cr.xses['server2'].b.xx == 1
    assert cr.xses['server3'].server_num == 3
    assert cr.xses['server4'].server_num == 4
    assert cr.xses['server4'].b.xx == 1

    check_containment(cr, verbose=True)


def test_configbuilder_build_at_root_freeze():
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers=4, a=MC_REQUIRED):
            super().__init__()
            self.num_servers = num_servers
            self.a = a

        def mc_build(self):
            for server_num in range(1, self.num_servers+1):
                with Xses(mc_key='server%d' % server_num) as c:
                    pass

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            XBuilder(a=1)

    cr = config(prod2).Root
    assert len(cr.xses) == 4
    for ii in 1, 2, 3, 4:
        name = 'server' + repr(ii)
        assert cr.xses[name].name == name
    check_containment(cr)


def test_configbuilder_access_to_contained_in_from_build():
    @named_as('y')
    class Y(ConfigItem):
        def __init__(self):
            super().__init__()
            self.number = MC_REQUIRED

    class YBuilder(ConfigBuilder):
        def mc_build(self):
            with Y() as y:
                y.number = self.contained_in.aaa

    @nested_repeatables('ys')
    class Root(ConfigItem):
        aaa = 7

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            YBuilder()

    cr = config(prod2).Root
    assert cr.y.number == 7
    check_containment(cr)


def test_configbuilder_access_to_contained_in_from___init__():
    @named_as('x')
    class X(ConfigItem):
        def __init__(self):
            super().__init__()
            self.number = MC_REQUIRED

    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()
            self.number = self.contained_in.aaa

        def mc_build(self):
            with X() as x:
                x.number = self.number

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 7

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            XBuilder()

    cr = config(prod2).Root
    assert cr.x.number == 7
    check_containment(cr)


def test_configbuilder_access_to_contained_in_from_with_block():
    parent = [None]

    @named_as('x')
    class X(ConfigItem):
        pass

    class XBuilder(ConfigBuilder):
        def mc_build(self):
            X()

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 7

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder() as xb:
                parent[0] = xb.contained_in

    cr = config(prod2).Root
    assert parent[0] == cr
    check_containment(cr)


def test_configbuilder_access_to_contained_in_from_built_item_must_give_parent_of_builder():
    mc_post_validate_parent = [None]

    @named_as('x')
    class X(ConfigItem):
        def __init__(self, number):
            super().__init__()
            self.number = number
            self.init_parent = self.contained_in
            self.mc_init_parent = MC_REQUIRED
            self.mc_validate_parent = MC_REQUIRED

        def mc_init(self):
            self.mc_init_parent = self.contained_in

        def mc_validate(self):
            self.mc_validate_parent = self.contained_in

        def mc_post_validate(self):
            mc_post_validate_parent[0] = self.contained_in

    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()
            self.number = self.contained_in.aaa

        def mc_build(self):
            with X(number=self.number):
                pass

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 7

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            XBuilder()

    cr = config(prod2).Root
    assert cr.x.number == 7
    assert cr.x.init_parent == cr
    assert cr.x.mc_init_parent == cr
    assert cr.x.mc_validate_parent == cr
    assert mc_post_validate_parent[0] == cr
    check_containment(cr)


def test_configbuilder_nested_items():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()
            self.number = self.contained_in.aaa
            self.b = None

        def mc_build(self):
            for num in range(1, self.number+1):
                with Xses(mc_key='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2, mc_set_unknown=True)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 2

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder() as xb:
                xb.b = 27
                XChild(mc_key=10)
                XChild(mc_key=11)

    cr = config(prod2).Root
    assert len(cr.xses) == 2
    for server in 'server1', 'server2':
        index = 10
        print('server:', server, cr.xses[server])
        for x_child in cr.xses[server].x_children.values():
            assert x_child.a == index
            index += 1
        assert index == 12
    check_containment(cr)


def test_configbuilder_nested_items_access_to_contained_in():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()
            # Access to contained_in is allowed here depending on where the object
            # is created, so it is discouraged to use contained_in from init
            self.number = self.contained_in.aaa
            self.b = MC_REQUIRED

        def mc_build(self):
            for num in range(1, self.number+1):
                with Xses(mc_key='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2, mc_set_unknown=True)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 2

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder() as xb:
                xb.b = 27
                with XChild(mc_key=10) as x1:
                    with ConfigItem() as ci:
                        assert ci.contained_in == x1
                XChild(mc_key=11)

    cr = config(prod2).Root
    assert len(cr.xses) == 2
    for server in 'server1', 'server2':
        index = 10
        for x_child in cr.xses[server].x_children.values():
            assert x_child.a == index
            index += 1
        assert index == 12
    check_containment(cr, verbose=True)


def test_configbuilder_multilevel_nested_items_access_to_contained_in():
    ybuilder_in_build_contained_in = []

    yc10 = [None]
    yc11 = [None]
    yc20 = [None]

    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()
            self.start = start
            self.b = MC_REQUIRED

        def mc_build(self):
            ybuilder_in_build_contained_in.append(self.contained_in)
            for num in range(self.start, self.start + self.contained_in.aaa):
                name = 'server%d' % num
                with Y(mc_key=name, name=name, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2, mc_set_unknown=True)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    @nested_repeatables('y_children', 'ys')
    class Y(RepeatableConfigItem):
        def __init__(self, mc_key, name, server_num):
            super().__init__(mc_key=mc_key)
            self.name = name
            self.server_num = server_num

    @named_as('y_children')
    class YChild(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=None)
            self.a = mc_key

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with ItemWithYs() as item:
            with YBuilder() as yb1:
                yb1.b = 27
                yc10[0] = YChild(mc_key=10)  # TODO: this should not be allowed, but it is impossible in python to prevent this, a workaround would be to use factories for object creation and then let the factory return None (if under a builder 'with')
                yc11[0] = YChild(mc_key=11)  # TODO: this must not be allowed
                with YBuilder(start=3) as yb2:
                    yb2.b = 28
                    yc20[0] = YChild(mc_key=20)  # TODO: this must not be allowed
                    YChild(mc_key=21)

    item = config(prod2).ItemWithYs

    assert len(item.ys) == 2
    total = 0
    for server in 'server1', 'server2':
        num_children = 0
        for y_child in item.ys[server].y_children.values():
            num_children += 1
            assert isinstance(y_child.contained_in, Y)
            total += y_child.a
        assert num_children == 2

        for inner_server in 'server3', 'server4':
            num_children = 0
            for y_child in item.ys[server].ys[inner_server].y_children.values():
                num_children += 1
                assert isinstance(y_child.contained_in, Y)
                total += y_child.a
            assert num_children == 2

    exp = 206
    assert total == exp, "Expected {exp} but got {got}".format(exp=exp, got=total)

    check_containment(item)

    # Note the length depends on the number of envs!
    assert len(ybuilder_in_build_contained_in) == 4
    for ci in ybuilder_in_build_contained_in:
        assert ci == item

    xfail("TODO: ref to item from with must not allow (wrong) contained_in")
    # The item created under the builder with statement will have contained_in == None
    # It may be proxied (in earlier versions cloned) for insertion under multiple items created in 'build'
    # The proxying (or cloning) is necessery to make sure the contained_in ref actually references the final parent
    got = type(yc10[0].contained_in)

    assert got == Y, "Expected type {exp}, but got type {got}".format(exp=Y, got=got)
    assert type(yc11[0].contained_in) == Y
    assert type(yc20[0].contained_in) == Y


def test_configbuilder_multilevel_nested_items_bad_access_to_contained_in():
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()

        def mc_build(self):
            with Y(mc_key='hello') as c:
                pass

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        pass

    @named_as('ys')
    @nested_repeatables('ys')
    class Y(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            # invalid access to self.contained_in
            print(self.contained_in)

    with raises(ConfigApiException):
        @mc_config(ef2_pp_prod, load_now=True)
        def config(_):
            with ItemWithYs() as item:
                with YBuilder() as yb1:
                    with YBuilder(start=3) as yb2:
                        pass


def test_configbuilder_repeated_repeatable_config_item_children():
    class XBuilder(ConfigBuilder):
        def __init__(self, mc_key=None, first=1, last=2):
            super().__init__(mc_key=mc_key)
            self.first = first
            self.last = last

        def mc_build(self):
            for num in range(self.first, self.last+1):
                with Xses(mc_key='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2, mc_set_unknown=True)
            self.setattr('q', default=self.last, mc_set_unknown=True)  # TODO: Only way to set an attribute in mc_build

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 2

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root() as cr:
            with XBuilder() as xb1:
                XChild(mc_key=10)
                XChild(mc_key=11)
            with XBuilder(mc_key='b2', first=3) as xb2:
                xb2.last = 3
                XChild(mc_key=10)

    cr = config(prod2).Root

    assert len(cr.xses) == 3
    total_children = 0
    for server in 'server1', 'server2', 'server3':
        index = 10
        for x_child in cr.xses[server].x_children.values():
            assert x_child.a == index
            index += 1
            total_children += 1
    print(cr)
    assert total_children == 5


def test_configbuilder_repeated_config_item_children():
    @named_as('a_item')
    @nested_repeatables('x_children')
    class AItem(ConfigItem):
        xx = 7

    class ABuilder(ConfigBuilder):
        def __init__(self, mc_key=None):
            super().__init__(mc_key=mc_key)

        def mc_build(self):
            AItem()

    @named_as('b_item')
    @nested_repeatables('x_children')
    class BItem(ConfigItem):
        xx = 6

    class BBuilder(ConfigBuilder):
        def __init__(self, mc_key=None):
            super().__init__(mc_key=mc_key)

        def mc_build(self):
            BItem()

    class Root(ConfigItem):
        aaa = 2

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root() as cr:
            with ABuilder():
                XChild(mc_key=10)
            with BBuilder():
                XChild(mc_key=11)

    cr = config(prod2).Root
    print(cr)
    assert cr.a_item.xx == 7
    assert cr.a_item.x_children[10]
    assert cr.a_item.x_children[10].a == 10

    assert cr.b_item.xx == 6
    assert cr.b_item.x_children[11]
    assert cr.b_item.x_children[11].a == 11


def test_configbuilder_repeated_what_built():
    builders = {}

    class XBuilder(ConfigBuilder):
        def __init__(self, mc_key=None, first=1, last=2):
            super().__init__(mc_key=mc_key)
            self.first = first
            self.last = last

        def mc_build(self):
            for num in range(self.first, self.last+1):
                with Xses(mc_key='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2, mc_set_unknown=True)
            self.setattr('q', default=self.last, mc_set_unknown=True)  # TODO: Only way to set an attribute in mc_build, does this even make sense?

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 2

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root() as cr:
            with XBuilder() as xb1:
                builders['xb1'] = xb1
                XChild(mc_key=10)
                XChild(mc_key=11)
            with XBuilder(mc_key='b2', first=3) as xb2:
                builders['xb2'] = xb2
                xb2.last = 3
                XChild(mc_key=10)

    cr = config(prod2).Root

    xfail("TODO: Implement 'what_built'?")
    xb1 = builders['xb1']
    assert len(xb1.what_built()) == 2
    assert isinstance(xb1.what_built(), OrderedDict)
    assert xb1.what_built()['q'] == 2

    xb2 = builders['xb2']
    assert len(xb2.what_built()) == 2
    assert isinstance(xb2.what_built(), OrderedDict)
    assert xb2.what_built()['xses']['server3'].something == 1
    assert xb2.what_built()['q'] == 3
    check_containment(cr)


def test_required_attributes_not_required_on_imtermediate_freeze_configbuilder_with_required_decorator():
    ii = [None]

    @named_as('a')
    class A(ConfigItem):
        xx = 1

    @named_as('b')
    class B(ConfigItem):
        xx = 2

    @required('a', 'b')
    class builder(ConfigBuilder):
        def mc_build(self):
            pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with builder() as wii:
            ii[0] = wii
            A()
            B()

    cr = config(prod1)
    ii = ii[0]
    assert ii.a.xx == 1
    assert ii.b.xx == 2
    check_containment(cr)


def test_required_attributes_not_required_on_imtermediate_freeze_configbuilder_with_mc_required():
    ii = [None]

    class builder(ConfigBuilder):
        def __init__(self):
            super().__init__()
            self.a = MC_REQUIRED
            self.b = MC_REQUIRED

        def mc_build(self):
            pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with builder() as wii:
            ii[0] = wii
            wii.a = 1
            wii.setattr('b', prod=2)

    cr = config(prod1)
    ii = ii[0]
    assert ii.a == 1
    assert ii.b == 2
    check_containment(cr)


def test_configbuilder_child_with_nested_repeatables():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            with Xses(1):
                XChild(mc_key=23)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            XBuilder()

    cr = config(prod2).Root
    assert len(cr.xses) == 1
    for x in cr.xses.values():
        assert len(x.x_children) == 1
    check_containment(cr)


def test_configbuilder_child_with_declared_but_not_defined_nested_repeatables():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            Xses(1)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root() as cr:
            XBuilder()

    cr = config(prod2).Root
    assert len(cr.xses) == 1
    for x in cr.xses.values():
        assert isinstance(x.x_children, dict)
        assert len(x.x_children) == 0
    check_containment(cr)


def test_configbuilders_alternating_with_items():
    @named_as('inners')
    class InnerItem(ConfigItem):
        def __init__(self, name):
            super().__init__()
            self.name = name

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            InnerItem('innermost')

    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super().__init__()
            self.id = name

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def mc_build(self):
            with MiddleItem(name=self.name):
                pass

    class OuterItem(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with ItemWithName() as cr:
            cr.name = 'myp'
            with OuterItem():
                with MiddleBuilder('base'):
                    InnerBuilder()

    cr = config(prod1).ItemWithName
    cr.json(compact=True)
    check_containment(cr)


def test_configbuilders_alternating_with_items_repeatable_simple():
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, name):
            super().__init__(mc_key=name)
            self.name = name

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            InnerItem('innermost')

    class OuterBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            InnerBuilder()

    @nested_repeatables('inners')
    class OuterItem(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with ItemWithName() as cr:
            cr.name = 'myp'
            with OuterItem():
                OuterBuilder()

    cr = config(prod1).ItemWithName
    cr.json()
    check_containment(cr)


def test_configbuilders_alternating_with_items_repeatable_many():
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, name):
            super().__init__(mc_key=name)
            self.name = name

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            InnerItem('innermost1')
            InnerItem('innermost2')

    @nested_repeatables('inners')
    class MiddleItem(RepeatableConfigItem):
        def __init__(self, name):
            super().__init__(mc_key=name)
            self.id = name

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def mc_build(self):
            MiddleItem('middleitem1')
            MiddleItem('middleitem2')
            MiddleItem('middleitem3')

    @nested_repeatables('MiddleItems')
    class OuterItem(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with OuterItem():
            with MiddleBuilder('base'):
                InnerBuilder()

    cr = config(prod1)
    cr.json(compact=True)
    check_containment(cr)


def test_configbuilders_alternating_with_items_repeatable_multilevel():
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.name = mc_key

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            InnerItem('innermost')

    @nested_repeatables('inners')
    class MiddleItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.id = mc_key

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def mc_build(self):
            with MiddleItem(mc_key=self.name):
                pass

    class OuterBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            with MiddleBuilder('base'):
                InnerBuilder()

    @nested_repeatables('MiddleItems')
    class OuterItem(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with OuterItem():
            OuterBuilder()

    cr = config(prod1)
    cr.json(builders=True)
    check_containment(cr)


def test_item_parent_proxy_get_env():
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.name = mc_key

    class Builder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            InnerItem('innermost')

    @nested_repeatables('inners')
    class OuterItem(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with OuterItem():
            with Builder():
                ConfigItem()

    cr = config(prod1)
    assert cr.OuterItem.inners['innermost'].ConfigItem.env == prod1


def test_assign_underscore_on_proxied_built_item_child_after_freeze():
    """This will go through the proxy object"""
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()

        def mc_build(self):
            Y()

    @named_as('y')
    class Y(ConfigItem):
        def __init__(self):
            super().__init__()
            self.something = None

    # Test assignment '_xxx'ok
    @mc_config(ef1_prod, load_now=True)
    def config(root):
        with YBuilder():
            ConfigItem()

        root.y.ConfigItem._aa = 1

    cr = config(prod1)
    assert cr.y.ConfigItem._aa == 1


def test_configbuilder_child_with_child_merge_setattr_in_with():
    """Test that values of an item defined in the config 'with block' overwrites values from a nested item in created in builder"""
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            with Xses(1):
                with ItemWithAABB(1) as xcab:
                    xcab.setattr('bb', pp=3, prod=4)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder():
                with ItemWithAABB(1) as xcab:
                    xcab.setattr('bb', default=7, prod=14)

    cr = config(prod2).Root
    assert len(cr.xses) == 1
    assert cr.xses[1].ItemWithAABB.aa == 1
    assert cr.xses[1].ItemWithAABB.bb == 14
    check_containment(cr)

    cr = config(pp2).Root
    assert cr.xses[1].ItemWithAABB.aa == 1
    xfail("TODO merge instead of 'owerwrite'")
    assert cr.xses[1].ItemWithAABB.bb == 3
    check_containment(cr)


def test_configbuilder_child_with_child_merge_setattr_in_init_with():
    """Test that values of an item defined in the config 'with block' overwrites values from a nested item in created in builder"""
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            with Xses(1):
                with ItemWithAABB(1) as xcab:
                    xcab.setattr('bb', pp=3, prod=4)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with Root():
            with XBuilder():
                with ItemWithAABB(1) as xcab:
                    xcab.setattr('aa', default=7, prod=14)

    cr = config(prod2).Root
    assert len(cr.xses) == 1
    assert cr.xses[1].ItemWithAABB.aa == 14
    assert cr.xses[1].ItemWithAABB.bb == 4
    check_containment(cr)

    cr = config(pp2).Root
    assert cr.xses[1].ItemWithAABB.aa == 7
    xfail("TODO merge instead of 'owerwrite'")
    assert cr.xses[1].ItemWithAABB.bb == 3
    check_containment(cr)

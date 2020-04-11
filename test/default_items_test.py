# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from pytest import raises, xfail

from multiconf import mc_config, DefaultItems, ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED, ConfigException
from multiconf.decorators import required, named_as, nested_repeatables
from multiconf.envs import EnvFactory

from .utils.utils import next_line_num, lines_in, start_file_line, total_msg
from .utils.messages import config_error_mc_required_expected, config_error_never_received_value_expected
from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA


minor_version = sys.version_info[1]

ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


def test_multiple_required_attributes_some_shared_resolved_for_configitem(capsys):
    """
    Under DefaultItems it is OK not to provide any value for an MC_REQUIRED attribute, elsewhere it is not.
    The item which is not shared resolves the remaining attributes without values from the corresponding shared item.
    """

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config(_):
        with DefaultItems():
            with item() as ii:
                ii.efgh = 7

        with item() as ii:
            ii.abcd = 6
            ii.ijkl = 8

    sout, serr = capsys.readouterr()

    cr = config(prod)
    it = cr.item
    assert it.abcd == 6
    assert it.efgh == 7
    assert it.ijkl == 8

    assert not sout
    assert not serr


def test_multiple_required_attributes_some_shared_resolved_for_repeatable_configitem(capsys):
    """
    Under DefaultItems it is OK not to provide any value for an MC_REQUIRED attribute, elsewhere it is not.
    The items which are not shared resolves the remaining attributes without values from the corresponding shared item.
    """

    @named_as('three_attr_items')
    class Item(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key)
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    @nested_repeatables('three_attr_items')
    class root(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            with DefaultItems():
                with Item('default') as ii:
                    ii.abcd = 1
                    ii.efgh = 7

            with Item('aa') as iaa:
                iaa.abcd = 6
                iaa.ijkl = 8

            with Item('bb') as ibb:
                ibb.efgh = 16
                ibb.ijkl = 17

    sout, serr = capsys.readouterr()

    cr = config(prod).root

    iaa = cr.three_attr_items['aa']
    assert iaa.abcd == 6
    assert iaa.efgh == 7
    assert iaa.ijkl == 8

    ibb = cr.three_attr_items['bb']
    assert ibb.abcd == 1
    assert ibb.efgh == 16
    assert ibb.ijkl == 17

    assert not sout
    assert not serr


def test_repeated_repeatable_configitem_error(capsys):
    """Under DefaultItems a RepeatableConfigItem cannot be repeated!"""

    @named_as('three_attr_items')
    class Item(RepeatableConfigItem):
        pass

    @nested_repeatables('three_attr_items')
    class root(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with root():
                with DefaultItems():
                    Item('default')
                    Item('oops')

    print(str(exinfo.value))
    assert str(exinfo.value) == "'Item' cannot be repeated under 'DefaultItems'. The first (and only) occurance of a 'RepeatableConfigItem' instance is used to provide the default attribute values."


def test_nested_default_value_item_error():
    """DefaultItems cannot be nested"""

    @nested_repeatables('three_attr_items')
    class root(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with root():
                with DefaultItems():
                    DefaultItems()

    print(str(exinfo.value))
    assert str(exinfo.value) == "'DefaultItems' cannot be nested."


def test_repeated_default_value_item_error():
    """DefaultItems cannot be repeated (not declader as nested_repeatables, so this is normal behaviour)"""

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            DefaultItems()
            DefaultItems()

    print(str(exinfo.value))
    assert str(exinfo.value) == "Repeated: <class 'multiconf.multiconf.DefaultItems'>."


def test_default_items_cannot_be_repeated_even_if_declared_repeatable(capsys):
    @nested_repeatables('DefaultItems')
    class root(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            DefaultItems()
            DefaultItems()

    assert str(exinfo.value) == "Repeated: <class 'multiconf.multiconf.DefaultItems'>."
    xfail("TODO: Error when using @nested_repeatables('DefaultItems')")


def test_required_attributes_shared_partial_env_assignment_all_resolved_for_configitem(capsys):
    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config(_):
        with DefaultItems():
            with item() as ii:
                ii.setattr('abcd', default=MC_REQUIRED, prod=106)
                ii.efgh = 18

        with item() as it:
            it.setattr('abcd', pp=17)
            it.ijkl = 19

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

    it = config(pp).item
    assert it.abcd == 17
    assert it.efgh == 18
    assert it.ijkl == 19

    it = config(prod).item
    assert it.abcd == 106
    assert it.efgh == 18
    assert it.ijkl == 19


def test_required_attributes_shared_multi_level_all_resolved_for_configitem(capsys):
    class root(ConfigItem):
        pass

    class l1(ConfigItem):
        pass

    class l2(ConfigItem):
        pass

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED
            self.mnop = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            with DefaultItems():
                with item() as ii:
                    ii.abcd = 17
                    ii.efgh = 1
                    ii.ijkl = 2
                    ii.mnop = 3

            with l1():
                with DefaultItems():
                    with item() as ii:
                        ii.efgh = 18

                with l2():
                    with DefaultItems():
                        with item() as ii:
                            ii.ijkl = 19

                    with item() as it:
                        it.mnop = 20

    cr = config(pp).root
    it = cr.l1.l2.item
    assert it.abcd == 17
    assert it.efgh == 18
    assert it.ijkl == 19
    assert it.mnop == 20


def test_multiple_required_attributes_shared_not_assigned_for_configitem(capsys):
    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config1(_):
        with DefaultItems():
            with item() as ii:
                ii.efgh = 7
                item()

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config2(_):
            with DefaultItems():
                with item() as ii:
                    ii.efgh = 7

            item()

    print(str(exinfo.value))
    assert total_msg(2) in str(exinfo.value)


def test_multiple_required_attributes_shared_not_assigned_some_envs_for_configitem(capsys):
    errorline = [None, None, None]

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            errorline[1] = next_line_num()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            errorline[2] = next_line_num()
            self.ijkl = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        errorline[0] = next_line_num() + (1 if minor_version > 7 else 0)
        @mc_config(ef, load_now=True)
        def config(_):
            with DefaultItems():
                with item() as ii:
                    ii.setattr('abcd', default=MC_REQUIRED, prod=6)
                    ii.efgh = 7

            item()

    _sout, serr = capsys.readouterr()
    print(str(exinfo.value))
    assert total_msg(2) in str(exinfo.value)
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp),
        start_file_line(__file__, errorline[1]),
        config_error_mc_required_expected.format(attr='abcd', env=pp),
        start_file_line(__file__, errorline[2]),
        config_error_mc_required_expected.format(attr='ijkl', env=pp),
    )


def test_shared_items_does_not_provide_matching_item_for_configitem_missing_attributes(capsys):
    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    class item2(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with DefaultItems():
                with item2() as ii:
                    ii.abcd = 13

            item()

    print(str(exinfo.value))
    assert total_msg(3) in str(exinfo.value)


def test_required_nested_items_shared_not_provided_for_configitem(capsys):
    """Under DefaultItems it is OK not to provide any value for an 'required' nested item, elsewhere it is not."""

    errorline = [None]

    @required('child')
    class item(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config1(_):
        with DefaultItems():
            item()

    with raises(ConfigException) as exinfo:
        errorline[0] = next_line_num() + (1 if minor_version > 7 else 0)
        @mc_config(ef, load_now=True)
        def config2(_):
            with DefaultItems():
                item()

            item()

    print(str(exinfo.value))
    assert total_msg(1) in str(exinfo.value)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "Missing '@required' items: ['child']",
    )


def test_required_nested_items_resolved_by_matching_default_item(capsys):
    """If a @required item is missing from regular config, but found under a corresponding default value item, then that satisfies the requirement."""

    class child(ConfigItem):
        def __init__(self, xx):
            super().__init__()
            self.xx = xx

    @required('child')
    class item(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with DefaultItems():
            child(111)  # This is ignored
            with item():
                child(1)

        item()

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

    it = config(pp).item
    assert it.child
    assert it.child.xx == 1
    assert it.child.contained_in == it


def test_required_nested_items_resolved_by_provided_required_default_item(capsys):
    """If a @required item is missing from regular config, but found under a DefaultItem, then that satisfies the requirement."""

    class child(ConfigItem):
        def __init__(self, xx):
            super().__init__()
            self.xx = xx

    @required('child')
    class item(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with DefaultItems():
            child(111)

        item()

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

    it = config(pp).item
    assert it.child
    assert it.child.xx == 111
    assert it.child.contained_in == it


def test_required_nested_items_of_repeatable_item_resolved_by_default_item(capsys):
    """If a @required item of a repeatable is missing from regular config, but found under a corresponding default value item, then that satisfies the requirement."""

    @nested_repeatables('Items')
    class root(ConfigItem):
        pass

    class child(ConfigItem):
        def __init__(self, xx):
            super().__init__()
            self.xx = xx

    @required('child')
    class Item(RepeatableConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            with DefaultItems():
                child(111)  # This is ignored
                with Item():
                    child(1)

            Item('aa')
            with Item('bb'):
                child(40)

            Item('cc')

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

    its = config(pp).root.Items

    aa = its['aa']
    assert aa.child.xx == 1
    assert aa.child.contained_in == aa

    bb = its['bb']
    assert bb.child.xx == 40
    assert bb.child.contained_in == bb

    cc = its['cc']
    assert cc.child.xx == 1
    assert cc.child.contained_in == cc


def test_nested_items_shared_by_default_item(capsys):
    """If a default item is found which has nested children not existing on item, then those children will be available from item."""

    class child(ConfigItem):
        def __init__(self, xx):
            super().__init__()
            self.xx = xx

    class item(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with DefaultItems():
            child(111)  # This is ignored
            with item():
                child(1)

        item()

    sout, serr = capsys.readouterr()

    it = config(pp).item
    assert it.child
    assert it.child.xx == 1
    assert it.child.contained_in == it

    assert not sout
    assert not serr


def test_repeatable_nested_items_shared_by_default_item(capsys):
    """If a default item is found which has nested repeatable children not existing on item, then those children will be available from item, iff item declared it as 'nested_repeatables'."""

    @nested_repeatables('RepeatableItems')
    class root(ItemWithAA):
        pass

    @named_as('children')
    class child(RepeatableItemWithAA):
        pass

    @nested_repeatables('children')
    class Item(RepeatableItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa='root'):
            with DefaultItems():
                child('a', 111)  # This is ignored
                with Item(None, aa='default_item'):
                    child('b1', 1)
                    child('b2', 2)

            Item('aa', 'aa')

            with Item('bb', 'bb'):
                child('c', 40)

            with Item('cc', 'cc'):
                child('b1', 17)

    sout, serr = capsys.readouterr()

    its = config(pp).root.RepeatableItems

    aa = its['aa']
    ach = aa.children
    assert ach['b1'].aa == 1
    assert ach['b1'].contained_in == aa
    assert ach['b2'].aa == 2
    assert ach['b2'].contained_in == aa

    bb = its['bb']
    bch = bb.children
    assert bch['c'].aa == 40
    assert bch['c'].contained_in == bb
    assert bch['b1'].aa == 1
    assert bch['b1'].contained_in == bb
    assert bch['b2'].aa == 2
    assert bch['b2'].contained_in == bb
    assert list(it.aa for it in bch.values()) == [40, 1, 2]

    cc = its['cc']
    cch = cc.children
    assert cch['b1'].aa == 17
    assert cch['b1'].contained_in == cc
    assert cch['b2'].aa == 2
    assert cch['b2'].contained_in == cc

    assert not sout
    assert not serr


def test_repeatable_nested_items_not_declare_as_nested_repeatables_shared_by_default_item(capsys):
    """If a default item is found which has nested repeatable children not existing on item, then those children will be available from item, iff item declared it as 'nested_repeatables'."""

    @nested_repeatables('RepeatableItems')
    class root(ItemWithAA):
        pass

    @named_as('children')
    class child(RepeatableItemWithAA):
        pass

    @nested_repeatables('children')
    class ItemX(RepeatableItemWithAA):
        pass

    class Item(RepeatableItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa='root'):
            with DefaultItems():
                with ItemX(None, aa='default_item'):
                    child('b1', 1)

            Item('aa', 'aa')

    sout, serr = capsys.readouterr()

    its = config(pp).root.RepeatableItems

    aa = its['aa']
    assert not hasattr(aa, 'children')

    assert not sout
    assert not serr


def test_repeatable_nested_items_but_non_repeatable_shared_by_default_item(capsys):
    """Repeatable non-Repeatable mixup."""

    @nested_repeatables('RepeatableItems')
    class root(ItemWithAA):
        pass

    @named_as('children')
    class child(RepeatableItemWithAA):
        pass

    @named_as('children')
    class NonRepChild(ItemWithAA):
        pass

    @nested_repeatables('children')
    class Item(RepeatableItemWithAA):
        pass

    class Item2(RepeatableItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa='root'):
            with DefaultItems():
                child('a', 111)  # This is ignored
                with Item2(None, aa='default_item'):
                    NonRepChild(1)

            Item('aa', 'aa')

            with Item('bb', 'bb'):
                child('c', 40)

            with Item('cc', 'cc'):
                child('b1', 17)

    sout, serr = capsys.readouterr()

    its = config(pp).root.RepeatableItems

    aa = its['aa']
    ach = aa.children
    assert not ach

    bb = its['bb']
    bch = bb.children
    assert bch['c'].aa == 40
    assert bch['c'].contained_in == bb
    assert list(it.aa for it in bch.values()) == [40]

    cc = its['cc']
    cch = cc.children
    assert cch['b1'].aa == 17
    assert cch['b1'].contained_in == cc

    assert not sout
    assert not serr


def test_non_repeatable_nested_items_but_repeatable_shared_by_default_item(capsys):
    """Repeatable non-Repeatable mixup inverse."""

    @nested_repeatables('RepeatableItems')
    class root(ItemWithAA):
        pass

    @named_as('children')
    class child(RepeatableItemWithAA):
        pass

    @named_as('children')
    class NonRepChild(ItemWithAA):
        pass

    @nested_repeatables('children')
    class Item(RepeatableItemWithAA):
        pass

    class Item2(RepeatableItemWithAA):
        pass

    @required('children')
    class Item3(RepeatableItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root(aa='root'):
            with DefaultItems():
                child('a', 111)  # This is ignored
                with Item(None, aa='default_item'):
                    child('b1', 1)
                    child('b2', 2)

            Item2('aa')

            with Item2('bb'):
                NonRepChild(40)

            with Item2('cc'):
                NonRepChild(17)

            with Item3('33'):
                NonRepChild(47)

    sout, serr = capsys.readouterr()

    its = config(pp).root.RepeatableItems

    aa = its['aa']
    assert not hasattr(aa, 'children')

    bb = its['bb']
    bch = bb.children
    assert bch.aa == 40
    assert bch.contained_in == bb

    cc = its['cc']
    cch = cc.children
    assert cch.aa == 17
    assert cch.contained_in == cc

    x33 = its['33']
    x33ch = x33.children
    assert x33ch.aa == 47
    assert x33ch.contained_in == x33

    assert not sout
    assert not serr


def test_required_will_not_resolve_to_default_repeatable(capsys):
    """Repeatable non-Repeatable mixup inverse."""

    errorline = [None]

    @nested_repeatables('RepeatableItems')
    class root(ItemWithAA):
        pass

    @named_as('children')
    class child(RepeatableItemWithAA):
        pass

    @nested_repeatables('children')
    class Item(RepeatableItemWithAA):
        pass

    @required('children')
    class Item3(RepeatableItemWithAA):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with root(aa='root'):
                with DefaultItems():
                    with Item(None, aa='default_item'):
                        child('b1', 1)

                errorline[0] = next_line_num()
                Item3('33')

    print(str(exinfo.value))
    assert total_msg(1) in str(exinfo.value)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "Missing '@required' items: ['children']",
    )


def test_required_shared_items_attribute_inherited_env_values_missing(capsys):
    """Under DefaultItems setattr must stil provide a value for all defined envs"""

    errorline = [None, None, None, None]

    class root(ConfigItem):
        def __init__(self):
            super().__init__()
            errorline[1] = next_line_num()
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

    class root2(root):
        def __init__(self):
            super().__init__()
            errorline[2] = next_line_num()
            self.someattr2 = MC_REQUIRED
            errorline[3] = next_line_num()
            self.someotherattr2 = MC_REQUIRED

    @mc_config(ef)
    def config(_):
        with DefaultItems():
            with root2() as cr:
                cr.setattr('anattr', prod=1)
                cr.setattr('someattr2', prod=3)
                cr.setattr('someotherattr2', pp=4)

        root2()

    with raises(ConfigException):
        errorline[0] = next_line_num()
        config.load(error_next_env=True)

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp),
        start_file_line(__file__, errorline[1]),
        config_error_mc_required_expected.format(attr='anattr', env=pp),
        start_file_line(__file__, errorline[2]),
        config_error_mc_required_expected.format(attr='someattr2', env=pp),
        start_file_line(__file__, errorline[3]),
        config_error_mc_required_expected.format(attr='someotherattr2', env=prod),
        # 'anotherattr' will not be verified because it might get a value in mc_init
        # which is not called when there are errors in 'with' block
    )


def test_shared_under_builder(capsys):
    class x(ConfigItem):
        pass

    class root(ConfigBuilder):
        def mc_build(self):
            x()

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            with DefaultItems():
                with item() as its:
                    its.efgh = 7

            with item() as it:
                it.abcd = 1
                it.ijkl = 2

    it = config(pp).x.item
    assert it.abcd == 1
    assert it.efgh == 7
    assert it.ijkl == 2


def test_shared_not_allowed_in_mc_init(capsys):
    class root(ConfigItem):
        def mc_init(self):
            DefaultItems()

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            root()

    print(str(exinfo.value))
    assert "'DefaultItems' are not allowed in 'mc_init'." in str(exinfo.value)


def test_shared_not_allowed_in_mc_build(capsys):
    class root(ConfigBuilder):
        def mc_build(self):
            with DefaultItems():
                pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            root()

    print(str(exinfo.value))
    assert "'DefaultItems' are not allowed in 'mc_build'." in str(exinfo.value)


def test_shared_item_is_not_subtype(capsys):
    """DefaultItems lookup is based solely on the named_as property."""
    errorline = [None, None]

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            errorline[1] = next_line_num()
            self.abcd = MC_REQUIRED

    @named_as('item')
    class item2(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        errorline[0] = next_line_num() + (1 if minor_version > 7 else 0)
        @mc_config(ef, load_now=True)
        def config(_):
            with DefaultItems():
                item2()

            item()

    _sout, serr = capsys.readouterr()

    print(str(exinfo.value))
    assert total_msg(1) in str(exinfo.value)
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_never_received_value_expected.format(env=pp),
        start_file_line(__file__, errorline[1]),
        config_error_mc_required_expected.format(attr='abcd', env=pp),
    )


def test_inherit_from_default_item_with_attribute_does_not_resolve_required(capsys):
    """TODO: Not sure about the use for inheriting from DefaultItems, but currently needed to get coverage."""
    errorline = [None]

    class DefaultItemsX(DefaultItems):
        abcd = 1

    @required('abcd')
    class item(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        errorline[0] = next_line_num() + (1 if minor_version > 7 else 0)
        @mc_config(ef, load_now=True)
        def config(_):
            DefaultItemsX()
            item()

    _sout, serr = capsys.readouterr()
    print(serr)
    print(str(exinfo.value))
    assert total_msg(1) in str(exinfo.value)
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "Missing '@required' items: ['abcd']",
    )


def test_nested_items_shared_by_default_item_not_valid(capsys):
    """If a default item is found which has nested children not existing on item, then those children must be valid."""
    errorline = [None]

    class child(ConfigItem):
        def __init__(self, xx=MC_REQUIRED):
            super().__init__()
            errorline[0] = next_line_num()
            self.xx = xx

    class item(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with DefaultItems():
                with item():
                    with child() as ch:
                        ch.setattr('xx', pp=1)

            item()

    sout, serr = capsys.readouterr()
    assert not sout
    assert lines_in(
        serr,
        config_error_never_received_value_expected.format(env=prod),
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='xx', env=prod),
    )

    xfail('TODO: ref item, child and message abount default ref')

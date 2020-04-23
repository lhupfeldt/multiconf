# Copyright (c) 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.multiconf import _ItemParentProxy, _mc_item_parent_proxy_factory


class MockConfigItem():
    _mc_contained_in = None
    _mc_excluded = 0


def test_type():
    root = MockConfigItem()
    ipp = _ItemParentProxy(root, MockConfigItem())
    assert type(ipp) is _ItemParentProxy


def test_isinstance():
    root = MockConfigItem()
    ipp = _mc_item_parent_proxy_factory(root, MockConfigItem())
    assert isinstance(ipp, MockConfigItem)
    assert isinstance(ipp, _ItemParentProxy)


def test_type_repr():
    root = MockConfigItem()
    ipp = _mc_item_parent_proxy_factory(root, MockConfigItem())
    assert repr(type(ipp)) == "<class 'multiconf.multiconf.ItemParentProxy:<test.item_parent_proxy_test.MockConfigItem>'>"

# Copyright (c) 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from multiconf.multiconf import _ItemParentProxy


class MockConfigItem(object):
    _mc_contained_in = None
    _mc_excluded = 0


def test_type():
    root = MockConfigItem()
    ipp = _ItemParentProxy(root, MockConfigItem())
    assert type(ipp) is _ItemParentProxy


def test_isinstance():
    root = MockConfigItem()
    ipp = _ItemParentProxy(root, MockConfigItem())
    assert isinstance(ipp, MockConfigItem)
    assert isinstance(ipp, _ItemParentProxy)

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ..attribute import Attribute


def test_attribute_repr():
    class Container(object):
        attributes = {}
    ac = Attribute(attribute_name='some_name1')
    assert repr(ac) == "Attribute: 'some_name1':not-frozen, values: {}"
    ac._mc_frozen = True
    assert repr(ac) == "Attribute: 'some_name1':frozen, values: {}"

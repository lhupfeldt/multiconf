# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ..attribute import Attribute
from ..values import MC_REQUIRED


def test_attribute_repr():
    class Container(object):
        attributes = {}
    ac = Attribute(attribute_name='some_name1')
    assert repr(ac) == "Attribute: 'some_name1':not-frozen, values: {}"
    ac._mc_frozen = True
    assert repr(ac) == "Attribute: 'some_name1':frozen, values: {}"


def test_attribute_has_default():
    ac = Attribute(attribute_name='some_name1')

    assert not ac.has_default()
    ac.env_values['default'] = (None, "ttt.py", 1)
    assert ac.has_default()
    ac.env_values['default'] = (MC_REQUIRED, "ttt.py", 1)
    assert not ac.has_default()

    ac = Attribute(attribute_name='some_name1')
    ac.env_values['__init__'] = (None, "ttt", 1)
    assert ac.has_default()
    ac.env_values['__init__'] = (MC_REQUIRED, "ttt.py", 1)
    assert not ac.has_default()


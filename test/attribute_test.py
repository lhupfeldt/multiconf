#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ..attribute import Attribute
from ..config_errors import _user_file_line


def test_attribute_repr():
    class Container(object):
        attributes = {}
    ac = Attribute(attribute_name='some_name1')
    assert repr(ac) == "Attribute: 'some_name1':not-frozen not-all-envs-initialized, values: {}"
    ac._frozen = True
    assert repr(ac) == "Attribute: 'some_name1':frozen not-all-envs-initialized, values: {}"

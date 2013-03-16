#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest

from ..attribute import Attribute
from ..config_errors import _user_file_line


class AttributeTest(unittest.TestCase):
    def attribute_repr_test(self):
        class Container(object):
            attributes = {}
        ac = Attribute(attribute_name='some_name1')
        assert repr(ac) == "Attribute: 'some_name1':not-frozen not-all-envs-initialized, values: {}"
        ac._frozen = True
        assert repr(ac) == "Attribute: 'some_name1':frozen not-all-envs-initialized, values: {}"

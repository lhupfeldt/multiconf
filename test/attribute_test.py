#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test

from ..attribute import Attribute
from ..config_errors import _user_file_line


class AttributeTest(unittest.TestCase):

    @test("Attribute - repr")
    def _a(self):
        class Container(object):
            attributes = {}
        ac = Attribute(attribute_name='some_name1')
        ok (repr(ac)) == "Attribute: 'some_name1':not-frozen not-all-envs-initialized, values: {}"
        ac._frozen = True
        ok (repr(ac)) == "Attribute: 'some_name1':frozen not-all-envs-initialized, values: {}"
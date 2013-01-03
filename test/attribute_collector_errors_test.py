#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail

from .. import ConfigException
from ..attribute_collector import AttributeCollector


class AttributeCollectorTest(unittest.TestCase):

    @test("assigning property on AttributeCollector - not allowed")
    def _a(self):
        class Container(object):
            attributes = {}
        ac = AttributeCollector('attribute_name', Container(), has_default=False, default_value=None)

        try:
            ac.someprop = 1
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Trying to set a property 'someprop' on an attribute collector"

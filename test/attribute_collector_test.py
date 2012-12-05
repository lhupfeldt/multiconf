#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno

from .. import ConfigException
from ..attribute_collector import AttributeCollector


class AttributeCollectorTest(unittest.TestCase):

    @test("AttributeCollector - repr")
    def _a(self):
        ac = AttributeCollector(attribute_name='some_name1', container='no-container')
        ok (repr(ac)) == "AttributeCollector: 'some_name1':not-frozen, values: {}"
        ac._frozen = True
        ok (repr(ac)) == "AttributeCollector: 'some_name1':frozen, values: {}"

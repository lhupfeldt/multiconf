#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test

from ..attribute_collector import AttributeCollector
from ..config_errors import _user_file_line


class AttributeCollectorTest(unittest.TestCase):

    @test("AttributeCollector - repr")
    def _a(self):
        class Container(object):
            attributes = {}
        ac = AttributeCollector(attribute_name='some_name1', container=Container(), default_value=None, default_user_file_line=('fake_file.py', 999))
        ok (repr(ac)) == "AttributeCollector: 'some_name1':not-frozen not-all-envs-initialized, values: {'__init__': (None, ('fake_file.py', 999))}"
        ac._frozen = True
        ok (repr(ac)) == "AttributeCollector: 'some_name1':frozen not-all-envs-initialized, values: {'__init__': (None, ('fake_file.py', 999))}"

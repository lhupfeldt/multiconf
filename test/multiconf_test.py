#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno

from multiconf import ConfigRoot, ConfigItem
from multiconf.envs import Env

prod = Env('prod')

class MulticonfTest(unittest.TestCase):

    @test("contained_in")
    def _a(self):
        with ConfigRoot(prod, [prod]) as conf:
            ok (conf.root_conf) == conf
            ok (conf.contained_in) == None
        
            with ConfigItem() as c1:
                ok (c1.root_conf) == conf
                ok (c1.contained_in) == conf

                with ConfigItem() as c2:
                    ok (c2.root_conf) == conf
                    ok (c2.contained_in) == c1

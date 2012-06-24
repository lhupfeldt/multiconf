# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..envs import Env, EnvGroup
from ..decorators import nested_repeatables, named_as, repeat

dev1 = Env('dev1')
dev2 = Env('dev2')
g_dev = EnvGroup('g_dev', dev1, dev2)

tst = Env('tst')

pp = Env('pp')
prod = Env('prod')

g_prod_like = EnvGroup('g_prod_like', prod, pp)


expected_json_output = """{
    "__class__": "root", 
    "a": 0, 
    "env": {
        "__class__": "Env", 
        "members": [], 
        "name": "prod", 
        "name #calculated": true
    }, 
    "env #calculated": true, 
    "nested": [], 
    "nested #calculated": true, 
    "someitems": {
        "a": {
            "__class__": "NestedRepeatable", 
            "id": "a", 
            "nested": [], 
            "nested #calculated": true, 
            "someitems": {}
        }, 
        "b": {
            "__class__": "NestedRepeatable", 
            "id": "b", 
            "nested": [], 
            "nested #calculated": true, 
            "someitems": {
                "a": {
                    "__class__": "NestedRepeatable", 
                    "id": "a", 
                    "nested": [], 
                    "nested #calculated": true, 
                    "someitems": {}
                }, 
                "b": {
                    "__class__": "NestedRepeatable", 
                    "id": "b", 
                    "nested": [], 
                    "nested #calculated": true, 
                    "someitems": {
                        "a": {
                            "__class__": "NestedRepeatable", 
                            "id": "a", 
                            "nested": [], 
                            "nested #calculated": true, 
                            "someitems": {}
                        }, 
                        "b": {
                            "__class__": "NestedRepeatable", 
                            "a": 1, 
                            "id": "b", 
                            "nested": [], 
                            "nested #calculated": true, 
                            "someitems": {}
                        }, 
                        "c": {
                            "__class__": "NestedRepeatable", 
                            "id": "c", 
                            "nested": [], 
                            "nested #calculated": true, 
                            "someitems": {}, 
                            "something": 1
                        }
                    }
                }, 
                "c": {
                    "__class__": "NestedRepeatable", 
                    "id": "c", 
                    "nested": [], 
                    "nested #calculated": true, 
                    "someitems": {}, 
                    "something": 2
                }
            }
        }, 
        "c": {
            "__class__": "NestedRepeatable", 
            "id": "c", 
            "nested": [], 
            "nested #calculated": true, 
            "someitems": {}, 
            "something": 3
        }
    }, 
    "valid_envs": [
        {
            "__class__": "Env", 
            "members": [], 
            "name": "prod", 
            "name #calculated": true
        }, 
        {
            "__class__": "Env", 
            "members": [], 
            "name": "pp", 
            "name #calculated": true
        }
    ], 
    "valid_envs #calculated": true
}"""

@named_as('someitems')
@repeat()
class RepeatableItem(ConfigItem):
    pass


class MulticonfTest(unittest.TestCase):
    @test("json dump")
    def _a(self):
        @named_as('someitems')
        @nested_repeatables('someitems')
        @repeat()
        class NestedRepeatable(ConfigItem):
            pass

        @nested_repeatables('someitems')
        class root(ConfigRoot):
            pass

        with root(prod, [prod, pp], a=0) as cr:
            NestedRepeatable(id='a')
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='a')
                with NestedRepeatable(id='b') as ci:
                    NestedRepeatable(id='a')
                    with NestedRepeatable(id='b') as ci:
                        ci.a(prod=1, pp=2)
                    NestedRepeatable(id='c', something=1)
                NestedRepeatable(id='c', something=2)
            NestedRepeatable(id='c', something=3)

        ok (cr.json()) == expected_json_output

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


_a_expected_json_output = """{
    "__class__": "root", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable", 
            "someitems": {}, 
            "id": "a-level1"
        }, 
        "b-level1": {
            "__class__": "NestedRepeatable", 
            "someitems": {
                "a-level2": {
                    "__class__": "NestedRepeatable", 
                    "someitems": {}, 
                    "id": "a-level2"
                }, 
                "b-level2": {
                    "__class__": "NestedRepeatable", 
                    "someitems": {
                        "a-level3": {
                            "__class__": "NestedRepeatable", 
                            "someitems": {}, 
                            "id": "a-level3"
                        }, 
                        "b-level3": {
                            "__class__": "NestedRepeatable", 
                            "someitems": {}, 
                            "a": 1, 
                            "id": "b-level3"
                        }, 
                        "c-level3": {
                            "__class__": "NestedRepeatable", 
                            "someitems": {}, 
                            "something": 1, 
                            "id": "c-level3"
                        }
                    }, 
                    "id": "b-level2"
                }, 
                "c-level2": {
                    "__class__": "NestedRepeatable", 
                    "someitems": {}, 
                    "something": 2, 
                    "id": "c-level2"
                }
            }, 
            "id": "b-level1"
        }, 
        "c-level1": {
            "__class__": "NestedRepeatable", 
            "someitems": {}, 
            "something": 3, 
            "id": "c-level1"
        }
    }, 
    "a": 0
}"""


_b_expected_json_output = """{
    "__class__": "root", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "someitems": {
        "a1": {
            "__class__": "NestedRepeatable", 
            "someitems": {}, 
            "some_value": 2, 
            "id": "a1"
        }, 
        "b1": {
            "__class__": "NestedRepeatable", 
            "someitems": {
                "a2": {
                    "__class__": "NestedRepeatable", 
                    "someitems": {}, 
                    "id": "a2", 
                    "referenced_item": "#confitem ref: root.someitems"
                }, 
                "b2": {
                    "__class__": "NestedRepeatable", 
                    "someitems": {}, 
                    "a": 1, 
                    "id": "b2"
                }
            }, 
            "someattr": 12, 
            "id": "b1"
        }
    }, 
    "anitem": {
        "__class__": "AnXItem", 
        "ref": "#confitem ref: root.someitems.someitems", 
        "something": 3
    }, 
    "a": 0
}"""


_c_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "someitem": {
        "__class__": "Nested", 
        "cycl": {
            "cyclic_item_ref": "#confitem ref: ConfigRoot.someitem"
        }, 
        "id": "b1", 
        "someattr": 12
    }, 
    "a": 0
}"""


@named_as('someitems')
@repeat()
class RepeatableItem(ConfigItem):
    pass


class MulticonfTest(unittest.TestCase):
    @test("json dump - simple")
    def _a(self):
        @nested_repeatables('someitems')
        class root(ConfigRoot):
            pass

        @named_as('someitems')
        @nested_repeatables('someitems')
        @repeat()
        class NestedRepeatable(ConfigItem):
            pass

        with root(prod, [prod, pp], a=0) as cr:
            NestedRepeatable(id='a-level1')
            with NestedRepeatable(id='b-level1') as ci:
                NestedRepeatable(id='a-level2')
                with NestedRepeatable(id='b-level2') as ci:
                    NestedRepeatable(id='a-level3')
                    with NestedRepeatable(id='b-level3') as ci:
                        ci.a(prod=1, pp=2)
                    NestedRepeatable(id='c-level3', something=1)
                NestedRepeatable(id='c-level2', something=2)
            NestedRepeatable(id='c-level1', something=3)

        ok (cr.json()) == _a_expected_json_output

    @test("json dump - cyclic references in conf items")
    def _b(self):
        @nested_repeatables('someitems')
        class root(ConfigRoot):
            pass

        @named_as('someitems')
        @nested_repeatables('someitems')
        @repeat()
        class NestedRepeatable(ConfigItem):
            pass

        @named_as('anitem')
        class AnXItem(ConfigItem):
            pass

        with root(prod, [prod, pp], a=0) as cr:
            with NestedRepeatable(id='a1') as ref_obj1:
                ref_obj1.some_value(pp=1, prod=2)
        
            with NestedRepeatable(id='b1', someattr=12):
                NestedRepeatable(id='a2', referenced_item=ref_obj1)
                with NestedRepeatable(id='b2') as ref_obj2:
                    ref_obj2.a(prod=1, pp=2)
            with AnXItem(something=3) as last_item:
                last_item.ref(pp=ref_obj1, prod=ref_obj2)
            
        ok (cr.json()) == _b_expected_json_output


    @test("json dump - cyclic references between conf items and other objects")
    def _c(self):
        @named_as('someitem')
        class Nested(ConfigItem):
            pass
        
        cycler = {}
        
        with ConfigRoot(prod, [prod, pp], a=0) as cr:
            with Nested(id='b1', someattr=12, cycl=cycler) as ref_obj2:
                pass            
            cycler['cyclic_item_ref'] = ref_obj2

        ok (cr.json()) == _c_expected_json_output

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, RepeatableConfigItem

from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


@nested_repeatables('someitems')
class root(ConfigItem):
    def __init__(self, aa=None):
        super().__init__()
        if aa is not None:
            self.aa = aa


@named_as('someitems')
@nested_repeatables('someitems')
class NestedRepeatable(RepeatableConfigItem):
    def __init__(self, mc_key, **kwargs):
        super().__init__(mc_key=mc_key)
        self.id = mc_key

        # Not an example of good coding!
        for key, val in kwargs.items():
            setattr(self, key, val)


_json_dump_persistent_ids_expected_json = """{
    "__class__": "root",
    "__id__": "<class 'test.json_output_persistent_ids_test.root'>",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "#ref later, id: <class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'b-level1'",
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable",
            "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'a-level1'",
            "id": "a-level1",
            "someitems": {}
        },
        "b-level1": {
            "__class__": "NestedRepeatable",
            "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'b-level1'",
            "id": "b-level1",
            "someitems": {
                "a-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'a-level2'",
                    "id": "a-level2",
                    "someitems": {}
                }
            }
        },
        "c-level1": {
            "__class__": "NestedRepeatable",
            "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'c-level1'",
            "id": "c-level1",
            "something": 3,
            "someitems": {}
        }
    }
}"""

_json_dump_persistent_ids_all_envs_expected_json = """{
    "__class__": "root",
    "__id__": "<class 'test.json_output_persistent_ids_test.root'>, name: 'NO-CURRENT-VALUE",
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "aa": "#ref later, id: <class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'NO-CURRENT-VALUE",
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable",
            "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'NO-CURRENT-VALUE",
            "id": "a-level1",
            "someitems": {}
        },
        "b-level1": {
            "__class__": "NestedRepeatable",
            "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'NO-CURRENT-VALUE",
            "id": "b-level1",
            "someitems": {
                "a-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'NO-CURRENT-VALUE",
                    "id": "a-level2",
                    "someitems": {}
                }
            }
        },
        "c-level1": {
            "__class__": "NestedRepeatable",
            "__id__": "<class 'test.json_output_persistent_ids_test.NestedRepeatable'>, id: 'NO-CURRENT-VALUE",
            "id": "c-level1",
            "something #multiconf attribute": true,
            "something": {
                "pp": 17,
                "prod": 3
            },
            "someitems": {}
        }
    }
}"""

def test_json_dump_persistent_ids():
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0) as rt:
            NestedRepeatable(mc_key='a-level1')
            with NestedRepeatable(mc_key='b-level1') as ci:
                NestedRepeatable(mc_key='a-level2')
            with NestedRepeatable(mc_key='c-level1', something=3) as nr:
                nr.setattr('something', pp=17)
            rt.aa = ci

    cr = config(prod).root
    assert compare_json(
        cr, _json_dump_persistent_ids_expected_json, sort_attributes=False, test_compact=False,
        expected_all_envs_json=_json_dump_persistent_ids_all_envs_expected_json, replace_ids=False)

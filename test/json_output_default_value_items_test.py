# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, MC_REQUIRED, ConfigItem, RepeatableConfigItem, ConfigBuilder, DefaultItems
from multiconf.envs import EnvFactory

from .utils.compare_json import compare_json


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


_json_dump_with_shared_and_builder_expected_json_full = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "mc_ConfigBuilder_root default-builder": {
        "__class__": "root",
        "__id__": 0000,
        "mc_DefaultItems": {
            "__class__": "DefaultItems",
            "__id__": 0000,
            "item": {
                "__class__": "item",
                "__id__": 0000,
                "abcd": "MC_REQUIRED",
                "efgh": 7,
                "ijkl": "MC_REQUIRED",
                "mc_is_default_value_item": true,
                "mc_is_default_value_item #calculated": true
            },
            "mc_is_default_value_item": true,
            "mc_is_default_value_item #calculated": true,
            "name": "mc_DefaultItems",
            "name #static": true
        },
        "item": {
            "__class__": "item",
            "__id__": 0000,
            "abcd": 1,
            "efgh": 7,
            "ijkl": 2
        }
    },
    "x": {
        "__class__": "x",
        "__id__": 0000,
        "mc_DefaultItems": "#ref default, id: 0000",
        "item": "#ref, id: 0000"
    }
}"""


_json_dump_with_shared_and_builder_expected_json_full = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "mc_ConfigBuilder_root default-builder": {
        "__class__": "root",
        "__id__": 0000,
        "mc_DefaultItems": {
            "__class__": "DefaultItems",
            "__id__": 0000,
            "item": {
                "__class__": "item",
                "__id__": 0000,
                "abcd": "MC_REQUIRED",
                "efgh": 7,
                "ijkl": "MC_REQUIRED",
                "mc_is_default_value_item": true,
                "mc_is_default_value_item #calculated": true
            },
            "mc_is_default_value_item": true,
            "mc_is_default_value_item #calculated": true,
            "name": "mc_DefaultItems",
            "name #static": true
        },
        "item": {
            "__class__": "item",
            "__id__": 0000,
            "abcd": 1,
            "efgh": 7,
            "ijkl": 2
        }
    },
    "x": {
        "__class__": "x",
        "__id__": 0000,
        "mc_DefaultItems": "#ref default, id: 0000",
        "item": "#ref, id: 0000"
    }
}"""

_json_dump_with_shared_expected_json_full = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "x": {
        "__class__": "x",
        "__id__": 0000,
        "mc_DefaultItems": {
            "__class__": "DefaultItems",
            "__id__": 0000,
            "item": {
                "__class__": "item",
                "__id__": 0000,
                "abcd": "MC_REQUIRED",
                "efgh": 7,
                "ijkl": "MC_REQUIRED",
                "mc_is_default_value_item": true,
                "mc_is_default_value_item #calculated": true
            },
            "mc_is_default_value_item": true,
            "mc_is_default_value_item #calculated": true,
            "name": "mc_DefaultItems",
            "name #static": true
        },
        "item": {
            "__class__": "item",
            "__id__": 0000,
            "abcd": 1,
            "efgh": 7,
            "ijkl": 2
        }
    }
}"""

_json_dump_expected_json_full = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "x": {
        "__class__": "x",
        "__id__": 0000,
        "item": {
            "__class__": "item",
            "__id__": 0000,
            "abcd": 1,
            "efgh": 7,
            "ijkl": 2
        }
    }
}"""

def test_shared_json_dump(capsys):
    class x(ConfigItem):
        pass

    class root(ConfigBuilder):
        def mc_build(self):
            x()

    class item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.abcd = MC_REQUIRED
            self.efgh = MC_REQUIRED
            self.ijkl = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            with DefaultItems():
                with item() as its:
                    its.efgh = 7

            with item() as it:
                it.abcd = 1
                it.ijkl = 2

    cr = config(pp)

    assert compare_json(cr, _json_dump_with_shared_and_builder_expected_json_full)
    assert compare_json(cr, _json_dump_with_shared_expected_json_full, dump_builders=False)
    assert compare_json(cr, _json_dump_expected_json_full, dump_builders=False, dump_default_items=False)

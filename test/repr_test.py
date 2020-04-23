# Copyright (c) 2018 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, MC_REQUIRED

from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import replace_ids
from .utils.utils import local_func
from .utils.compare_repr import compare_repr
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


@named_as('someitem')
class SimpleItem(ConfigItem):
    def __init__(self, **kwargs):
        super().__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)


_repr_root_expected_repr = """{
    "__class__": "ConfigItem #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    }
}"""

def test_repr_root():
    @mc_config(ef, load_now=True)
    def config(rt):
        ConfigItem()

    cr = config(prod).ConfigItem
    assert compare_repr(cr, _repr_root_expected_repr, replace_ids=True)


_repr_simple_expected_repr = """{
    "__class__": "root #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
            "id": "a-level1",
            "someitems": {}
        },
        "b-level1": {
            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
            "id": "b-level1",
            "someitems": {
                "a-level2": {
                    "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                    "id": "a-level2",
                    "someitems": {}
                },
                "b-level2": {
                    "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                    "id": "b-level2",
                    "someitems": {
                        "a-level3": {
                            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                            "id": "a-level3",
                            "someitems": {}
                        },
                        "b-level3": {
                            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                            "id": "b-level3",
                            "a": 1,
                            "someitems": {}
                        },
                        "c-level3": {
                            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                            "id": "c-level3",
                            "something": 1,
                            "someitems": {}
                        }
                    }
                },
                "c-level2": {
                    "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                    "id": "c-level2",
                    "something": 2,
                    "someitems": {}
                }
            }
        },
        "c-level1": {
            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
            "id": "c-level1",
            "something": 3,
            "someitems": {}
        }
    }
}"""


def test_repr_simple():
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            NestedRepeatable(mc_key='a-level1')
            with NestedRepeatable(mc_key='b-level1') as ci:
                NestedRepeatable(mc_key='a-level2')
                with NestedRepeatable(mc_key='b-level2') as ci:
                    NestedRepeatable(mc_key='a-level3')
                    with NestedRepeatable(mc_key='b-level3', a=7) as ci:
                        ci.setattr('a', prod=1, pp=2)
                    NestedRepeatable(mc_key='c-level3', something=1)
                NestedRepeatable(mc_key='c-level2', something=2)
            NestedRepeatable(mc_key='c-level1', something=3)

    cr = config(prod).root
    assert compare_repr(cr, _repr_simple_expected_repr)


_repr_cyclic_references_in_conf_items_expected_repr = """{
    "__class__": "root #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "a1": {
            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
            "id": "a1",
            "some_value": 2,
            "someitems": {}
        },
        "b1": {
            "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
            "id": "b1",
            "someattr": 12,
            "someitems": {
                "a2": {
                    "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                    "id": "a2",
                    "referenced_item": "#ref, id: 0000",
                    "someitems": {}
                },
                "b2": {
                    "__class__": "NestedRepeatable #as: 'xxxx', id: 0000",
                    "id": "b2",
                    "a": 1,
                    "someitems": {}
                }
            }
        }
    },
    "anitem": {
        "__class__": "AnXItem #as: 'xxxx', id: 0000",
        "something": 3,
        "ref": "#ref, id: 0000"
    }
}"""

def test_repr_cyclic_references_in_conf_items():
    @named_as('anitem')
    class AnXItem(ConfigItem):
        def __init__(self):
            super().__init__()
            self.something = MC_REQUIRED
            self.ref = MC_REQUIRED

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            with NestedRepeatable(mc_key='a1', some_value=27) as ref_obj1:
                ref_obj1.setattr('some_value', pp=1, prod=2)

            with NestedRepeatable(mc_key='b1', someattr=12):
                NestedRepeatable(mc_key='a2', referenced_item=ref_obj1)
                with NestedRepeatable(mc_key='b2', a=MC_REQUIRED) as ref_obj2:
                    ref_obj2.setattr('a', prod=1, pp=2)
            with AnXItem() as last_item:
                last_item.something = 3
                last_item.setattr('ref', pp=ref_obj1, prod=ref_obj2)

    cr = config(prod).root
    assert compare_repr(cr, _repr_cyclic_references_in_conf_items_expected_repr)


_repr_property_method_name_only_expected = """{
    "__class__": "ItemWithAA #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested #as: 'xxxx', id: 0000",
        "m": "@property method value - call disabled #calculated"
    }
}"""

def test_repr_property_method_name_only():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    cr = config(prod).ItemWithAA
    assert compare_repr(cr, _repr_property_method_name_only_expected)


_repr_property_attribute_method_override_expected_repr = """{
    "__class__": "ItemWithAA #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested #as: 'xxxx', id: 0000",
        "m": 7,
        "m #overrides @property": true,
        "m #overridden @property #calculated value was": "@property method value - call disabled"
    }
}"""

def test_repr_property_attribute_method_override():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            with Nested() as nn:
                nn.setattr("m", mc_overwrite_property=True, default=7)

    cr = config(prod).ItemWithAA
    assert compare_repr(cr, _repr_property_attribute_method_override_expected_repr)
    assert cr.someitem.m == 7


_repr_property_attribute_method_override_other_env_expected_repr = """{
    "__class__": "ConfigItem #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "Nested #as: 'xxxx', id: 0000",
        "m": "@property method value - call disabled #calculated",
        "m #value for Env('prod') provided by @property": true
    }
}"""

def test_repr_property_attribute_method_override_other_env():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ConfigItem():
            with Nested() as nn:
                nn.setattr("m", mc_overwrite_property=True, pp=7)

    cr = config(prod).ConfigItem
    assert compare_repr(cr, _repr_property_attribute_method_override_other_env_expected_repr)
    assert cr.someitem.m == 1


_repr_non_conf_item_used_as_key_expected_json = """{
    "__class__": "ItemWithAA #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "SimpleItem #as: 'xxxx', id: 0000",
        "b": {
            "<test.repr_test.%(local_func)sKey object at 0x0000>": 2
        }
    }
}"""

def test_repr_non_conf_item_used_as_key(capsys):
    class Key():
        pass

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            SimpleItem(b={Key(): 2})

    cr = config(prod).ItemWithAA

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

    assert compare_repr(cr, _repr_non_conf_item_used_as_key_expected_json % dict(local_func=local_func()), replace_address=True)


_repr_iterable_expected_repr = """{
    "__class__": "ConfigItem #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "SimpleItem #as: 'xxxx', id: 0000",
        "a": [
            1
        ]
    }
}"""

def test_repr_iterable():
    class MyIterable():
        def __iter__(self):
            yield 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ConfigItem():
            SimpleItem(a=MyIterable())

    cr = config(prod).ConfigItem
    assert compare_repr(cr, _repr_iterable_expected_repr)


_repr_during_load_json0_exp = """{
    "__class__": "root #as: 'xxxx', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": 0,
    "someitems": {}
}"""

_repr_during_load_json1_exp = """{
    "__class__": "NestedRepeatable #as: 'xxxx', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "id": "b-level1",
    "someitems": {}
}"""

def test_repr_during_load():
    jsons = []

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0) as cr:
            jsons.append(repr(cr))
            NestedRepeatable(mc_key='a-level1')
            with NestedRepeatable(mc_key='b-level1') as ci:
                jsons.append(repr(ci))
                NestedRepeatable(mc_key='a-level2')

    cr = config(prod).root
    assert replace_ids(jsons[0]) == _repr_during_load_json0_exp
    assert replace_ids(jsons[1]) == _repr_during_load_json1_exp

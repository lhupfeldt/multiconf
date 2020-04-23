# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, abc
from collections import OrderedDict
import pytest
from pytest import raises, xfail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, InvalidUsageException, ConfigException, ConfigAttributeError, MC_REQUIRED

from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import replace_ids, next_line_num, to_compact
from .utils.utils import local_func, py37_no_exc_comma
from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
g_p = ef.EnvGroup('g_p', pp, prod)

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


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


_json_dump_root_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    }
}"""

_json_dump_root_no_env_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    }
}"""

def test_json_dump_root():
    @mc_config(ef, load_now=True)
    def config(rt):
        ConfigItem()

    cr = config(prod).ConfigItem
    assert compare_json(cr, _json_dump_root_expected_json, expected_all_envs_json=_json_dump_root_no_env_expected_json)


_json_dump_simple_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "a-level1",
            "someitems": {}
        },
        "b-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "b-level1",
            "someitems": {
                "a-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "a-level2",
                    "someitems": {}
                },
                "b-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "b-level2",
                    "someitems": {
                        "a-level3": {
                            "__class__": "NestedRepeatable",
                            "__id__": 0000,
                            "id": "a-level3",
                            "someitems": {}
                        },
                        "b-level3": {
                            "__class__": "NestedRepeatable",
                            "__id__": 0000,
                            "id": "b-level3",
                            "a": 1,
                            "someitems": {}
                        },
                        "c-level3": {
                            "__class__": "NestedRepeatable",
                            "__id__": 0000,
                            "id": "c-level3",
                            "something": 1,
                            "someitems": {}
                        }
                    }
                },
                "c-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "c-level2",
                    "something": 2,
                    "someitems": {}
                }
            }
        },
        "c-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "c-level1",
            "something": 3,
            "someitems": {}
        }
    }
}"""

_json_dump_simple_all_envs_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "aa": 0,
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "a-level1",
            "someitems": {}
        },
        "b-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "b-level1",
            "someitems": {
                "a-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "a-level2",
                    "someitems": {}
                },
                "b-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "b-level2",
                    "someitems": {
                        "a-level3": {
                            "__class__": "NestedRepeatable",
                            "__id__": 0000,
                            "id": "a-level3",
                            "someitems": {}
                        },
                        "b-level3": {
                            "__class__": "NestedRepeatable",
                            "__id__": 0000,
                            "id": "b-level3",
                            "a #multiconf attribute": true,
                            "a": {
                                "pp": 2,
                                "prod": 1
                            },
                            "someitems": {}
                        },
                        "c-level3": {
                            "__class__": "NestedRepeatable",
                            "__id__": 0000,
                            "id": "c-level3",
                            "something": 1,
                            "someitems": {}
                        }
                    }
                },
                "c-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "c-level2",
                    "something": 2,
                    "someitems": {}
                }
            }
        },
        "c-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "c-level1",
            "something": 3,
            "someitems": {}
        }
    }
}"""

def test_json_dump_simple():
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
    assert compare_json(cr, _json_dump_simple_expected_json, sort_attributes=False, expected_all_envs_json=_json_dump_simple_all_envs_expected_json)


_json_dump_cyclic_references_in_conf_items_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "a1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "a1",
            "some_value": 2,
            "someitems": {}
        },
        "b1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "b1",
            "someattr": 12,
            "someitems": {
                "a2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "a2",
                    "referenced_item": "#ref, id: 0000",
                    "someitems": {}
                },
                "b2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "b2",
                    "a": 1,
                    "someitems": {}
                }
            }
        }
    },
    "anitem": {
        "__class__": "AnXItem",
        "__id__": 0000,
        "something": 3,
        "ref": "#ref, id: 0000"
    }
}"""

def test_json_dump_cyclic_references_in_conf_items():
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
    assert compare_json(cr, _json_dump_cyclic_references_in_conf_items_expected_json, sort_attributes=False, test_containment=False)


__json_dump_cyclic_references_between_conf_items_and_other_objects_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "cycl": {
            "cyclic_item_ref": "#ref, id: 0000"
        },
        "id": "b1",
        "someattr": 12
    }
}"""

def test_json_dump_cyclic_references_between_conf_items_and_other_objects():
    cycler = {}

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            with SimpleItem(id='b1', someattr=12, cycl=cycler) as ref_obj2:
                pass
            cycler['cyclic_item_ref'] = ref_obj2

    cr = config(prod).ItemWithAA
    assert compare_json(cr, __json_dump_cyclic_references_between_conf_items_and_other_objects_expected_json)


_json_dump_property_method_expected = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m": 1,
        "m #calculated": true
    }
}"""

def test_json_dump_property_method():
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
    assert compare_json(cr, _json_dump_property_method_expected)


_json_dump_property_method_name_only_expected = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m": "@property method value - call disabled",
        "m #calculated": true
    }
}"""

def test_json_dump_property_method_name_only():
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
    assert compare_json(cr, _json_dump_property_method_name_only_expected, property_methods=None)


_json_dump_property_attribute_method_override_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m": 7,
        "m #overrides @property": true,
        "m #overridden @property #calculated value was": 1
    }
}"""

def test_json_dump_property_attribute_method_override():
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
    assert compare_json(cr, _json_dump_property_attribute_method_override_expected_json)
    assert cr.someitem.m == 7


_json_dump_property_attribute_method_override_other_env_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m": 1,
        "m #value for Env('prod') provided by @property": true,
        "m #calculated": true
    }
}"""

_json_dump_property_attribute_method_override_other_env_all_envs_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m": {
            "pp": 7,
            "pp #overrides @property": true,
            "prod": 1,
            "prod #value for Env('prod') provided by @property": true
        },
        "m #multiconf attribute": true,
        "m #overridden @property #calculated value was": 1
    }
}"""

def test_json_dump_property_attribute_method_override_other_env():
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
    assert compare_json(cr, _json_dump_property_attribute_method_override_other_env_expected_json,
                        expected_all_envs_json=_json_dump_property_attribute_method_override_other_env_all_envs_expected_json)
    assert cr.someitem.m == 1


_json_dump_property_method_raises_InvalidUsageException_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m #invalid usage context": "InvalidUsageException('No m now'%(comma)s)"
    }
}""" % dict(comma=py37_no_exc_comma)

_json_dump_property_method_raises_InvalidUsageException_all_envs_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m #invalid usage context": "InvalidUsageException('No m now'%(comma)s)"
    }
}""" % dict(comma=py37_no_exc_comma)

def test_json_dump_property_method_raises_InvalidUsageException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise InvalidUsageException("No m now")

    @mc_config(ef)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    config.load(validate_properties=False)
    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_dump_property_method_raises_InvalidUsageException_expected_json,
                        expected_all_envs_json=_json_dump_property_method_raises_InvalidUsageException_all_envs_expected_json)


_json_dump_property_method_raises_exception_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m #json_error trying to handle property method": "Exception('Something is wrong'%(comma)s)"
    }
}""" % dict(comma=py37_no_exc_comma)

_json_dump_property_method_raises_exception_all_envs_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "aa": {
        "pp": 1,
        "prod": 0
    },
    "aa #multiconf attribute": true,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m #json_error trying to handle property method": "Exception('Something is wrong'%(comma)s)"
    }
}""" % dict(comma=py37_no_exc_comma)

def test_json_dump_property_method_raises_exception():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise Exception("Something is wrong")

    @mc_config(ef)
    def config(rt):
        with ItemWithAA() as it:
            it.setattr('aa', default=1, prod=0)
            Nested()

    config.load(validate_properties=False)
    cr = config(prod).ItemWithAA
    assert compare_json(
        cr, _json_dump_property_method_raises_exception_expected_json, expect_num_errors=1,
        expected_all_envs_json=_json_dump_property_method_raises_exception_all_envs_expected_json, expect_all_envs_num_errors=2)


_json_dump_property_method_raises_exception_in_pp_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "aa": 1,
        "m #json_error trying to handle property method": "Exception('Something is wrong'%(comma)s)"
    }
}""" % dict(comma=py37_no_exc_comma)

_json_dump_property_method_raises_exception_in_pp_all_envs_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "aa": {
            "pp": 17,
            "prod": 1
        },
        "aa #multiconf attribute": true,
        "m": {
            "pp": 24,
            "pp #calculated": true,
            "prod #json_error trying to handle property method": "Exception('Something is wrong'%(comma)s)"
        },
        "m #multiconf env specific @property": true
    }
}""" % dict(comma=py37_no_exc_comma)

def test_json_dump_property_method_raises_exception_in_pp():
    @named_as('someitem')
    class Nested(ItemWithAA):
        @property
        def m(self):
            if self.aa == 1:
                raise Exception("Something is wrong")
            return self.aa + 7

    @mc_config(ef)
    def config(rt):
        with ItemWithAA(aa=0):
            with Nested() as nn:
                nn.setattr('aa', default=1, pp=17)

    config.load(validate_properties=False)
    cr = config(prod).ItemWithAA
    assert compare_json(
        cr, _json_dump_property_method_raises_exception_in_pp_expected_json, expect_num_errors=1,
        expected_all_envs_json=_json_dump_property_method_raises_exception_in_pp_all_envs_expected_json)


_e2b_expected_json_output = _json_dump_property_method_raises_exception_expected_json.replace('Exception', 'ConfigException')

def test_json_dump_property_method_raises_ConfigException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise ConfigException("Something is wrong")

    @mc_config(ef)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    config.load(validate_properties=False)
    cr = config(prod).ItemWithAA
    assert compare_json(cr, _e2b_expected_json_output, expect_num_errors=1)


_json_dump_property_method_returns_self_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m": "#ref self, id: 0000",
        "m #calculated": true
    }
}"""

def test_json_dump_property_method_returns_self():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return self

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_dump_property_method_returns_self_expected_json)


_json_dump_property_method_returns_already_seen_conf_item_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "referenced": {
        "__class__": "X",
        "__id__": 0000,
        "a": 0
    },
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "other_conf_item": "#ref, id: 0000",
        "other_conf_item #calculated": true
    }
}"""

def test_json_dump_property_method_returns_already_seen_conf_item():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            return self.contained_in.referenced

    @named_as('referenced')
    class X(ConfigItem):
        def __init__(self, a):
            super().__init__()
            self.a = a

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            X(a=0)
            Nested()

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_dump_property_method_returns_already_seen_conf_item_expected_json)


_json_dump_property_method_calls_json_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "other_conf_item": 7,
        "other_conf_item #calculated": true
    }
}"""

_json_dump_property_method_calls_json_expected_stderr = """Warning: Nested json calls, disabling @property method value dump:
outer object type: <class 'test.json_output_test.%(local_func)sNested'>
inner object type: <class 'test.json_output_test.%(local_func)sNested'>, inner obj: {
    "__class__": "Nested #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    }
}"""

def test_json_dump_property_method_calls_json(capsys):
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            self.json()
            return 7

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    cr = config(prod).ItemWithAA
    warn_nesting = os.environ.get('MULTICONF_WARN_JSON_NESTING', "false")
    os.environ['MULTICONF_WARN_JSON_NESTING'] = "true"
    try:
        assert compare_json(cr, _json_dump_property_method_calls_json_expected_json, warn_nesting=True)
        sout, serr = capsys.readouterr()
        assert not sout
        exp = _json_dump_property_method_calls_json_expected_stderr % dict(local_func=local_func())
        assert exp in replace_ids(serr)
    finally:
        os.environ['MULTICONF_WARN_JSON_NESTING'] = warn_nesting


def test_json_dump_property_method_calls_json_no_warn(capsys):
    """Get branch coverage for warn_nesting == False"""
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            self.json()

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0):
            Nested()

    cr = config(prod).ItemWithAA
    cr.json(warn_nesting=False)
    sout, serr = capsys.readouterr()
    assert not sout
    assert "Warning: Nested json calls" not in serr


_json_dump_non_conf_item_used_as_key_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "b": {
            "<test.json_output_test.%(local_func)sKey object at 0x0000>": 2
        }
    }
}"""

def test_json_dump_non_conf_item_used_as_key(capsys):
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

    assert compare_json(cr, _json_dump_non_conf_item_used_as_key_expected_json % dict(local_func=local_func()), replace_address=True)


_json_dump_non_conf_item_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "a": {
            "__class__": "SomeClass",
            "__id__": 0000,
            "a": 187
        }
    }
}"""


_json_dump_unhandled_item_function_ref_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "func": "__json_error__ # don't know how to handle obj of type: <class 'function'>"
    }
}"""

def test_json_dump_unhandled_item_function_ref():
    def fff():
        pass

    @mc_config(ef, load_now=True)
    def config(rt):
        with ConfigItem():
            SimpleItem(func=fff)

    cr = config(prod).ConfigItem
    assert compare_json(cr, _json_dump_unhandled_item_function_ref_expected_json, expect_num_errors=1)


_json_dump_iterable_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "a": [
            1
        ]
    }
}"""

def test_json_dump_iterable():
    class MyIterable():
        def __iter__(self):
            yield 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ConfigItem():
            SimpleItem(a=MyIterable())

    cr = config(prod).ConfigItem
    assert compare_json(cr, _json_dump_iterable_expected_json)


_json_dump_iterable_static_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "SimpleItem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "a": [
            1
        ],
        "a #static": true
    }
}"""

def test_json_dump_iterable_static():
    class MyIterable():
        def __iter__(self):
            yield 1

    class SimpleItem(ConfigItem):
        a = MyIterable()

    @mc_config(ef, load_now=True)
    def config(rt):
        with ConfigItem():
            SimpleItem()

    cr = config(prod).ConfigItem
    assert compare_json(cr, _json_dump_iterable_static_expected_json, test_compact=False)


_uplevel_ref_expected_json_output = """{
    "__class__": "NestedRepeatable",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "c": 2,
    "id": "n2",
    "someitems": {
        "n3": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "d": 3,
            "id": "n3",
            "uplevel_ref": "#outside-ref: <class 'test.json_output_test.NestedRepeatable'>, id: 'n1', name: 'Number 1'",
            "someitems": {}
        }
    }
}"""

def test_json_dump_uplevel_reference_while_dumping_from_lower_nesting_level():
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            with NestedRepeatable(mc_key='n1', name='Number 1', b=1) as n1:
                with NestedRepeatable(mc_key='n2', c=2) as n2:
                    NestedRepeatable(mc_key='n3', uplevel_ref=n1, d=3)
        return n2

    cfg = config(prod)
    n2 = cfg.mc_config_result
    assert compare_json(n2, _uplevel_ref_expected_json_output, test_containment=False)


_json_dump_dir_error_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "aa": 2,
        "c": "will-show",
        "c #calculated": true
    }
}"""

def test_json_dump_dir_error(capsys):
    @named_as('someitem')
    class Nested(ItemWithAA):
        _errorline = 0

        # multiconf does not rely on dir(instance), only dir(cls)
        def __dir__(self):
            self._errorline = next_line_num()
            raise Exception('Error in dir()')

        @property
        def c(self):
            return "will-show"

    @mc_config(ef)
    def config(rt):
        with ItemWithAA(aa=0):
            with Nested() as nn:
                nn.aa = 2

    config.load(validate_properties=False)
    cr = config(prod).ItemWithAA
    cr.json()
    sout, serr = capsys.readouterr()
    assert serr == sout == ''
    assert compare_json(cr, _json_dump_dir_error_expected_json)


# TODO: Not absolutely correct output (not outside ref)
_json_dump_property_method_returns_later_confitem_same_level_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "one": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "one",
            "x": 3,
            "someitems": {},
            "m": "#ref later, id: 0000",
            "m #calculated": true
        },
        "two": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "two",
            "x": 3,
            "someitems": {},
            "m": "#ref self, id: 0000",
            "m #calculated": true
        }
    }
}"""


@named_as('someitems')
@nested_repeatables('someitems')
class _NamedNestedRepeatable(RepeatableConfigItem, metaclass=abc.ABCMeta):
    def __new__(cls, name):
        return super().__new__(cls, mc_key=name)

    def __init__(self, name):
        super().__init__(mc_key=name)
        self.name = name
        self.x = 3

    @abc.abstractproperty
    def m(self):
        pass


def test_json_dump_property_method_returns_later_confitem_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return self.contained_in.someitems['two']

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            NamedNestedRepeatable(name='one')
            NamedNestedRepeatable(name='two')

    cr = config(prod).root
    assert compare_json(cr, _json_dump_property_method_returns_later_confitem_same_level_expected_json)


_json_dump_property_method_returns_later_confitem_list_same_level_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "one": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "one",
            "x": 3,
            "someitems": {},
            "m": [
                "#ref later, id: 0000",
                "#ref later, id: 0000"
            ],
            "m #calculated": true
        },
        "two": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "two",
            "x": 3,
            "someitems": {},
            "m": [
                "#ref self, id: 0000",
                "#ref later, id: 0000"
            ],
            "m #calculated": true
        },
        "three": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "three",
            "x": 3,
            "someitems": {},
            "m": [
                "#ref, id: 0000",
                "#ref self, id: 0000"
            ],
            "m #calculated": true
        }
    }
}"""

def test_json_dump_property_method_returns_later_confitem_list_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return [self.contained_in.someitems['two'], self.contained_in.someitems['three']]

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            NamedNestedRepeatable(name='one')
            NamedNestedRepeatable(name='two')
            NamedNestedRepeatable(name='three')

    cr = config(prod).root
    assert compare_json(cr, _json_dump_property_method_returns_later_confitem_list_same_level_expected_json)


def test_json_dump_property_method_returns_later_confitem_tuple_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return self.contained_in.someitems['two'], self.contained_in.someitems['three']

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            NamedNestedRepeatable(name='one')
            NamedNestedRepeatable(name='two')
            NamedNestedRepeatable(name='three')

    cr = config(prod).root
    assert compare_json(cr, _json_dump_property_method_returns_later_confitem_list_same_level_expected_json)


_json_dump_property_method_returns_later_confitem_ordereddict_same_level_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "one": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "one",
            "x": 3,
            "someitems": {},
            "m": {
                "a": "#ref later, id: 0000",
                "b": "#ref later, id: 0000"
            },
            "m #calculated": true
        },
        "two": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "two",
            "x": 3,
            "someitems": {},
            "m": {
                "a": "#ref self, id: 0000",
                "b": "#ref later, id: 0000"
            },
            "m #calculated": true
        },
        "three": {
            "__class__": "NamedNestedRepeatable",
            "__id__": 0000,
            "name": "three",
            "x": 3,
            "someitems": {},
            "m": {
                "a": "#ref, id: 0000",
                "b": "#ref self, id: 0000"
            },
            "m #calculated": true
        }
    }
}"""

def test_json_dump_property_method_returns_later_confitem_ordereddict_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return OrderedDict((('a', self.contained_in.someitems['two']), ('b', self.contained_in.someitems['three'])))

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            NamedNestedRepeatable(name='one')
            NamedNestedRepeatable(name='two')
            NamedNestedRepeatable(name='three')

    cr = config(prod).root
    assert compare_json(cr, _json_dump_property_method_returns_later_confitem_ordereddict_same_level_expected_json, test_decode=True)


_json_dump_test_json_dump_nested_class_non_mc_expected_json_1 = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {},
    "McWithNestedClass": {
        "__class__": "McWithNestedClass",
        "__id__": 0000,
        "TTT": "<class 'test.json_output_test.%(local_func)sMcWithNestedClass.TTT'>"
    }
}"""

_json_dump_test_json_dump_nested_class_non_mc_expected_json_2 = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {},
    "ItemWithAA": {
        "__class__": "ItemWithAA",
        "__id__": 0000,
        "aa": "<class 'test.json_output_test.%(local_func)sNonMcWithNestedClass'>"
    }
}"""

def test_json_dump_nested_class_non_mc():
    class McWithNestedClass(ConfigItem):
        class TTT():
            pass

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            McWithNestedClass()

    cr = config(prod).root
    assert compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_1 % dict(local_func=local_func()))

    class NonMcWithNestedClass():
        class TTT():
            pass

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            with ItemWithAA() as ci:
                ci.aa = NonMcWithNestedClass

    cr = config(prod).root
    assert compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_2 % dict(local_func=local_func()))


def test_json_dump_nested_class_with_json_equiv_non_mc():
    class McWithNestedClass(ConfigItem):
        class TTT():
            def json_equivalent(self):
                return ""

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            McWithNestedClass()

    cr = config(prod).root
    assert compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_1 % dict(local_func=local_func()))

    class NonMcWithNestedClass():
        class TTT():
            def json_equivalent(self):
                return ""

    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            with ItemWithAA() as ci:
                ci.aa = NonMcWithNestedClass

    cr = config(prod).root
    assert compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_2 % dict(local_func=local_func()))


_json_dump_multiple_errors_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "func": "__json_error__ # don't know how to handle obj of type: <class 'function'>",
        "someitem": {
            "__class__": "SimpleItem",
            "__id__": 0000,
            "func": "__json_error__ # don't know how to handle obj of type: <class 'function'>"
        }
    }
}"""

def test_json_dump_multiple_errors():
    def fff():
        pass

    def ggg():
        pass

    @mc_config(ef, load_now=True)
    def config(rt):
        with ConfigItem():
            with SimpleItem(func=fff):
                SimpleItem(func=ggg)

    cr = config(prod).ConfigItem
    assert compare_json(cr, _json_dump_multiple_errors_expected_json, expect_num_errors=2)


_iterable_attr_forward_item_ref = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "ItemWithAnXRef": {
        "__class__": "ItemWithAnXRef",
        "__id__": 0000,
        "aa": 1,
        "item_refs": [
            "#ref later, id: 0000"
        ]
    },
    "xx": {
        "__class__": "Xx",
        "__id__": 0000,
        "a": 1
    }
}"""

def test_iterable_attr_forward_item_ref():
    class ItemWithAnXRef(ItemWithAA):
        def __init__(self):
            super().__init__()
            self.item_refs = []

    @named_as('xx')
    class Xx(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 0
            with ItemWithAnXRef() as x_ref:
                x_ref.setattr('aa', default=1, pp=2)
            xx = Xx()
            x_ref.item_refs.append(xx)

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _iterable_attr_forward_item_ref)


_iterable_tuple_attr_forward_item_ref = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "ItemWithAnXRef": {
        "__class__": "ItemWithAnXRef",
        "__id__": 0000,
        "aa": 1,
        "item_refs": [
            "#ref later, id: 0000"
        ],
        "xx": {
            "__class__": "Xx",
            "__id__": 0000,
            "a": 1
        }
    }
}"""

def test_iterable_tuple_attr_forward_item_ref():
    class ItemWithAnXRef(ItemWithAA):
        def __init__(self):
            super().__init__()
            self.item_refs = MC_REQUIRED

    @named_as('xx')
    class Xx(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 0
            with ItemWithAnXRef() as x_ref:
                x_ref.setattr('aa', default=1, pp=2)
                xx = Xx()
                x_ref.item_refs = (xx,)

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _iterable_tuple_attr_forward_item_ref)


_dict_attr_forward_item_ref = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "ItemWithAnXRef": {
        "__class__": "ItemWithAnXRef",
        "__id__": 0000,
        "aa": 1,
        "item_refs": {
            "xr": "#ref later, id: 0000"
        },
        "xx": {
            "__class__": "Xx",
            "__id__": 0000,
            "a": 1
        }
    }
}"""

def test_dict_attr_forward_item_ref():
    class ItemWithAnXRef(ItemWithAA):
        def __init__(self):
            super().__init__()
            self.item_refs = {}

    @named_as('xx')
    class Xx(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA() as cr:
            cr.aa = 0
            with ItemWithAnXRef() as x_ref:
                x_ref.setattr('aa', default=1, pp=2)
                xx = Xx()
                x_ref.item_refs['xr'] = xx

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _dict_attr_forward_item_ref)


_static_member_direct_expected_json = """{
    "__class__": "ConfigItem",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "Xx": {
        "__class__": "Xx",
        "__id__": 0000,
        "a": 1,
        "a #static": true
    }
}"""

def test_static_member_direct():
    class Xx(ConfigItem):
        a = 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ConfigItem():
            Xx()

    cr = config(prod).ConfigItem
    assert compare_json(cr, _static_member_direct_expected_json)


_static_member_inherited_mc_expected_json = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "Xx": {
        "__class__": "Xx",
        "__id__": 0000,
        "a": 1,
        "a #static": true
    },
    "Yy": {
        "__class__": "Yy",
        "__id__": 0000,
        "a": 1,
        "a #static": true
    },
    "Zz": {
        "__class__": "Zz",
        "__id__": 0000,
        "a": 1,
        "a #static": true
    },
    "Aa": {
        "__class__": "Aa",
        "__id__": 0000,
        "a": 7,
        "a #static": true
    },
    "Bb": {
        "__class__": "Bb",
        "__id__": 0000,
        "a": 7,
        "a #static": true
    }
}"""

def test_static_member_inherited_mc():
    class Xx(ConfigItem):
        a = 1

    class Yy(Xx):
        pass

    class Zz(Yy):
        pass

    class Aa(Zz):
        a = 7

    class Bb(Aa):
        pass

    @mc_config(ef, load_now=True)
    def config(root):
        Xx()
        Yy()
        Zz()
        Aa()
        Bb()

    cr = config(prod)
    assert compare_json(cr, _static_member_inherited_mc_expected_json)


_env_ref_expected_json = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "Xx": {
        "__class__": "Xx",
        "__id__": 0000,
        "env_ref": {
            "__class__": "Env",
            "name": "pp"
        }
    }
}"""

def test_env_ref():
    class Xx(ConfigItem):
        def mc_init(self):
            self.setattr('env_ref', default=pp, mc_set_unknown=True)

    @mc_config(ef, load_now=True)
    def config(root):
        Xx()

    cr = config(prod)
    assert compare_json(cr, _env_ref_expected_json)


_envgroup_ref_expected_json = """{
    "__class__": "McConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "Xx": {
        "__class__": "Xx",
        "__id__": 0000,
        "egref": {
            "__class__": "EnvGroup",
            "name": "g_p"
        }
    }
}"""

def test_envgroup_ref():
    class Xx(ConfigItem):
        def mc_init(self):
            self.setattr('egref', default=g_p, mc_set_unknown=True)

    @mc_config(ef, load_now=True)
    def config(root):
        Xx()

    cr = config(prod)
    assert compare_json(cr, _envgroup_ref_expected_json)


_json_dump_depth_expected_json_d1 = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": "<class 'multiconf.repeatable.RepeatableDict'>",
    "ItemWithAA": "<class 'test.utils.tstclasses.ItemWithAA'>"
}"""

_json_dump_depth_expected_json_d2 = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "a-level1": "<class 'test.json_output_test.NestedRepeatable'>, id: 'a-level1'",
        "b-level1": "<class 'test.json_output_test.NestedRepeatable'>, id: 'b-level1'"
    },
    "ItemWithAA": {
        "__class__": "ItemWithAA",
        "__id__": 0000,
        "aa": 1
    }
}"""

_json_dump_depth_expected_json_d3 = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "a-level1",
            "someitems": {}
        },
        "b-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "b-level1",
            "someitems": {
                "a-level2": "<class 'test.json_output_test.NestedRepeatable'>, id: 'a-level2'",
                "b-level2": "<class 'test.json_output_test.NestedRepeatable'>, id: 'b-level2'"
            },
            "ItemWithAA": {
                "__class__": "ItemWithAA",
                "__id__": 0000,
                "aa": 2
            }
        }
    },
    "ItemWithAA": {
        "__class__": "ItemWithAA",
        "__id__": 0000,
        "aa": 1
    }
}"""

_json_dump_depth_expected_json_full = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitems": {
        "a-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "a-level1",
            "someitems": {}
        },
        "b-level1": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "id": "b-level1",
            "someitems": {
                "a-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "a-level2",
                    "someitems": {}
                },
                "b-level2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "id": "b-level2",
                    "someitems": {
                        "b-level3": {
                            "__class__": "NestedRepeatable",
                            "__id__": 0000,
                            "id": "b-level3",
                            "a": 1,
                            "someitems": {
                                "c-level3": {
                                    "__class__": "NestedRepeatable",
                                    "__id__": 0000,
                                    "id": "c-level3",
                                    "something": 1,
                                    "someitems": {}
                                }
                            }
                        }
                    },
                    "ItemWithAA": {
                        "__class__": "ItemWithAA",
                        "__id__": 0000,
                        "aa": 3
                    }
                }
            },
            "ItemWithAA": {
                "__class__": "ItemWithAA",
                "__id__": 0000,
                "aa": 2
            }
        }
    },
    "ItemWithAA": {
        "__class__": "ItemWithAA",
        "__id__": 0000,
        "aa": 1
    }
}"""

def test_json_dump_depth(capsys):
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0):
            ItemWithAA(1)
            NestedRepeatable(mc_key='a-level1')
            with NestedRepeatable(mc_key='b-level1') as ci:
                ItemWithAA(2)
                NestedRepeatable(mc_key='a-level2')
                with NestedRepeatable(mc_key='b-level2') as ci:
                    ItemWithAA(3)
                    with NestedRepeatable(mc_key='b-level3', a=7) as ci:
                        ci.setattr('a', prod=1, pp=2)
                        NestedRepeatable(mc_key='c-level3', something=1)

    cr = config(prod).root

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

    assert compare_json(cr, _json_dump_depth_expected_json_d1, sort_attributes=False, depth=0)
    assert compare_json(cr, _json_dump_depth_expected_json_d1, sort_attributes=False, depth=1)
    assert compare_json(cr, _json_dump_depth_expected_json_d2, sort_attributes=False, depth=2)
    assert compare_json(cr, _json_dump_depth_expected_json_d3, sort_attributes=False, depth=3)
    assert compare_json(cr, _json_dump_depth_expected_json_full, sort_attributes=False)


_json_dump_during_load_json0_exp = """{
    "__class__": "root, not-frozen",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": 0,
    "someitems": {}
}"""

_json_dump_during_load_json1_exp = """{
    "__class__": "NestedRepeatable, not-frozen",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "id": "b-level1",
    "someitems": {}
}"""

def test_json_dump_during_load():
    jsons = []
    @mc_config(ef, load_now=True)
    def config(rt):
        with root(aa=0) as cr:
            jsons.append(cr.json())
            NestedRepeatable(mc_key='a-level1')
            with NestedRepeatable(mc_key='b-level1') as ci:
                jsons.append(ci.json())
                NestedRepeatable(mc_key='a-level2')

    cr = config(prod).root
    assert replace_ids(jsons[0]) == _json_dump_during_load_json0_exp
    assert replace_ids(jsons[1]) == _json_dump_during_load_json1_exp


_exception_in_property_exception_exc_ex = """{
    "__class__": "Xx #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "xxx #no value for Env('prod')": true,
    "xxx #json_error trying to handle property method": "Error gettting repr of obj, type: <class 'test.json_output_test.test_exception_in_property_exception.<locals>.BadException'>, exception: BadException: BadException bad __repr__"
}, object of type: <class 'test.json_output_test.test_exception_in_property_exception.<locals>.Xx'> has no attribute 'xxx'. Attribute 'xxx' is defined as a multiconf attribute and as a @property method but value is undefined for Env('prod') and @property method call failed with: <class 'test.json_output_test.test_exception_in_property_exception.<locals>.BadException'>
"""

def test_exception_in_property_exception():
    class BadException(Exception):
        def __repr__(self):
            raise BadException("BadException bad __repr__")

    class Xx(ConfigItem):
        @property
        def xxx(self):
            raise BadException("Error in 'xxx' property impl.")

    @mc_config(ef)
    def config(root):
        with Xx() as xx:
            xx.setattr('xxx', pp=1, mc_overwrite_property=True)

    config.load(validate_properties=False)
    cr = config(prod).Xx

    with raises(ConfigAttributeError) as exinfo:
        print(cr.xxx)

    print(str(exinfo.value))
    print()
    print("--- exp ---")
    print(_exception_in_property_exception_exc_ex.strip())
    print("--- exc ---")
    print(replace_ids(str(exinfo.value).strip()))
    assert replace_ids(str(exinfo.value).strip()) == _exception_in_property_exception_exc_ex.strip()

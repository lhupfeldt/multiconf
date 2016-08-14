# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
from collections import OrderedDict
import pytest

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, InvalidUsageException, ConfigException, ConfigBuilder, MC_REQUIRED

from ..decorators import nested_repeatables, named_as
from ..envs import EnvFactory

from .utils.utils import replace_ids, lineno, to_compact, replace_user_file_line_msg, replace_multiconf_file_line_msg, config_error
from .utils.utils import py3_local
from .utils.compare_json import compare_json
from .utils.tstclasses import RootWithName, RootWithAA, ItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


@nested_repeatables('someitems')
class root(ConfigRoot):
    def __init__(self, selected_env, env_factory, aa=None):
        super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)
        if aa is not None:
            self.aa = aa


@named_as('someitems')
@nested_repeatables('someitems')
class NestedRepeatable(RepeatableConfigItem):
    def __init__(self, id, **kwargs):
        super(NestedRepeatable, self).__init__(mc_key=id)
        self.id = id

        # Not an example of goot coding!
        for key, val in kwargs.items():
            setattr(self, key, val)


@named_as('someitem')
class SimpleItem(ConfigItem):
    def __init__(self, **kwargs):
        super(SimpleItem, self).__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)


_json_dump_root_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    }
}"""

def test_json_dump_root():
    with ConfigRoot(prod, ef) as cr:
        pass

    compare_json(cr, _json_dump_root_expected_json)


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
                            "a": 1,
                            "id": "b-level3",
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
    with root(prod, ef, aa=0) as cr:
        NestedRepeatable(id='a-level1')
        with NestedRepeatable(id='b-level1') as ci:
            NestedRepeatable(id='a-level2')
            with NestedRepeatable(id='b-level2') as ci:
                NestedRepeatable(id='a-level3')
                with NestedRepeatable(id='b-level3', a=7) as ci:
                    ci.setattr('a', prod=1, pp=2)
                NestedRepeatable(id='c-level3', something=1)
            NestedRepeatable(id='c-level2', something=2)
        NestedRepeatable(id='c-level1', something=3)

    compare_json(cr, _json_dump_simple_expected_json)


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
                    "someitems": {},
                    "referenced_item": "#ref, id: 0000"
                },
                "b2": {
                    "__class__": "NestedRepeatable",
                    "__id__": 0000,
                    "a": 1,
                    "id": "b2",
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
            super(AnXItem, self).__init__()
            self.something = MC_REQUIRED
            self.ref = MC_REQUIRED

    with root(prod, ef, aa=0) as cr:
        with NestedRepeatable(id='a1', some_value=27) as ref_obj1:
            ref_obj1.setattr('some_value', pp=1, prod=2)

        with NestedRepeatable(id='b1', someattr=12):
            NestedRepeatable(id='a2', referenced_item=ref_obj1)
            with NestedRepeatable(id='b2', a=MC_REQUIRED) as ref_obj2:
                ref_obj2.setattr('a', prod=1, pp=2)
        with AnXItem() as last_item:
            last_item.something = 3
            last_item.setattr('ref', pp=ref_obj1, prod=ref_obj2)

    compare_json(cr, _json_dump_cyclic_references_in_conf_items_expected_json, test_containment=False)


__json_dump_cyclic_references_between_conf_items_and_other_objects_expected_json = """{
    "__class__": "RootWithAA",
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

    with RootWithAA(prod, ef, aa=0) as cr:
        with SimpleItem(id='b1', someattr=12, cycl=cycler) as ref_obj2:
            pass
        cycler['cyclic_item_ref'] = ref_obj2

    compare_json(cr, __json_dump_cyclic_references_between_conf_items_and_other_objects_expected_json)


_json_dump_property_method_expected = """{
    "__class__": "RootWithAA",
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

    with RootWithAA(prod, ef, aa=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_expected)


_json_dump_property_attribute_method_override_expected_json = """{
    "__class__": "RootWithAA",
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
        "m #!overrides @property": true,
        "m #!overridden @property": "1 #calculated"
    }
}"""

def test_json_dump_property_attribute_method_override():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    with RootWithAA(prod, ef, aa=0) as cr:
        with Nested() as nn:
            nn.setattr("m!", default=7)

    compare_json(cr, _json_dump_property_attribute_method_override_expected_json)
    assert cr.someitem.m == 7


_json_dump_property_attribute_method_override_other_env_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m #value for current env provided by @property": true,
        "m": 1,
        "m #calculated": true
    }
}"""

def test_json_dump_property_attribute_method_override_other_env():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    with ConfigRoot(prod, ef) as cr:
        with Nested() as nn:
            nn.setattr("m!", pp=7)

    compare_json(cr, _json_dump_property_attribute_method_override_other_env_expected_json)
    assert cr.someitem.m == 1


_json_dump_property_method_raises_InvalidUsageException_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m #invalid usage context": "InvalidUsageException('No m now',)"
    }
}"""

def test_json_dump_property_method_raises_InvalidUsageException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise InvalidUsageException("No m now")

    with RootWithAA(prod, ef, aa=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_raises_InvalidUsageException_expected_json)


_json_dump_property_method_raises_Exception_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "m # json_error trying to handle property method": "Exception('Something is wrong',)"
    }
}"""

def test_json_dump_property_method_raises_Exception():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise Exception("Something is wrong")

    with RootWithAA(prod, ef, aa=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_raises_Exception_expected_json, expect_num_errors=1)


_e2b_expected_json_output = _json_dump_property_method_raises_Exception_expected_json.replace('Exception', 'ConfigException')

def test_json_dump_property_method_raises_ConfigException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise ConfigException("Something is wrong")

    with RootWithAA(prod, ef, aa=0) as cr:
        Nested()

    compare_json(cr, _e2b_expected_json_output, expect_num_errors=1)


_json_dump_property_method_returns_self_expected_json = """{
    "__class__": "RootWithAA",
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

    with RootWithAA(prod, ef, aa=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_returns_self_expected_json)


_json_dump_property_method_returns_already_seen_conf_item_expected_json = """{
    "__class__": "RootWithAA",
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
            return self.root_conf.referenced

    @named_as('referenced')
    class X(ConfigItem):
        def __init__(self, a):
            super(X, self).__init__()
            self.a = a

    with RootWithAA(prod, ef, aa=0) as cr:
        X(a=0)
        Nested()

    compare_json(cr, _json_dump_property_method_returns_already_seen_conf_item_expected_json)


_json_dump_property_method_calls_json_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "other_conf_item # json_error trying to handle property method": "NestedJsonCallError('Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?',)"
    }
}"""

_json_dump_property_method_calls_json_expected_stderr = """Warning: Nested json calls:
outer object type: <class 'multiconf.test.json_output_test.%(py3_local)sNested'>
inner object type: <class 'multiconf.test.json_output_test.%(py3_local)sNested'>, inner obj: {
    "__class__": "Nested #as: 'xxxx', id: 0000"
}"""

def test_json_dump_property_method_calls_json(capsys):
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            self.json()

    with RootWithAA(prod, ef, aa=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_calls_json_expected_json, expect_num_errors=1)
    _sout, serr = capsys.readouterr()
    assert "Nested json calls detected" in serr
    assert _json_dump_property_method_calls_json_expected_stderr % dict(py3_local=py3_local()) in replace_ids(serr)


def test_json_dump_property_method_calls_json_no_warn(capsys):
    """Get branch coverage for warn_nesting == False"""
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            self.json()

    with RootWithAA(prod, ef, aa=0) as cr:
        Nested()

    cr.json(warn_nesting=False)
    _sout, serr = capsys.readouterr()
    assert "Warning: Nested json calls" not in serr


# TODO: insert information about skipped objects into json output
_json_dump_non_conf_item_not_json_serializable_expected_json = """{
    "__class__": "RootWithAA",
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
            
        }
    }
}"""

def test_json_dump_non_conf_item_not_json_serializable():
    class Key():
        def __repr__(self):
            return "<Key object>"

    with RootWithAA(prod, ef, aa=0) as cr:
        SimpleItem(b={Key(): 2})

    compare_json(cr, _json_dump_non_conf_item_not_json_serializable_expected_json)


_json_dump_non_conf_item_expected_json = """{
    "__class__": "RootWithAA",
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

@pytest.mark.skipif(sys.version_info[0] >= 3, reason="Python3 does not have old style classes.")
def test_json_dump_non_conf_item():
    # This is an old style class
    class SomeClass():
        def __init__(self):
            self.a = 187
            self._x = 7

    with RootWithAA(prod, ef, aa=0) as cr:
        SimpleItem(a=SomeClass())

    assert replace_ids(cr.json()) == _json_dump_non_conf_item_expected_json
    # to_compact will not handle conversion of non-multiconf object representation, an extra '#as...' is inserted,
    # we remove it again
    assert replace_ids(cr.json(compact=True)) == to_compact(_json_dump_non_conf_item_expected_json).replace("SomeClass #as: 'xxxx', id", 'SomeClass #id')


_json_dump_unhandled_item_function_ref_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "func": "__json_error__ # don't know how to handle obj of type: <%(type_or_class)s 'function'>"
    }
}"""

def test_json_dump_unhandled_item_function_ref():
    def fff():
        pass

    with ConfigRoot(prod, ef) as cr:
        SimpleItem(func=fff)

    compare_json(cr, _json_dump_unhandled_item_function_ref_expected_json, expect_num_errors=1)


_json_dump_iterable_expected_json = """{
    "__class__": "ConfigRoot",
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
    class MyIterable(object):
        def __iter__(self):
            yield 1

    with ConfigRoot(prod, ef) as cr:
        SimpleItem(a=MyIterable())

    compare_json(cr, _json_dump_iterable_expected_json)


_json_dump_iterable_static_expected_json = """{
    "__class__": "ConfigRoot",
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
    class MyIterable(object):
        def __iter__(self):
            yield 1

    class SimpleItem(ConfigItem):
        a = MyIterable()

    with ConfigRoot(prod, ef) as cr:
        SimpleItem()

    compare_json(cr, _json_dump_iterable_static_expected_json, test_compact=False)


_uplevel_ref_expected_json_output = """{
    "__class__": "NestedRepeatable",
    "__id__": 0000,
    "c": 2,
    "id": "n2",
    "someitems": {
        "n3": {
            "__class__": "NestedRepeatable",
            "__id__": 0000,
            "d": 3,
            "id": "n3",
            "someitems": {},
            "uplevel_ref": "#outside-ref: NestedRepeatable: id: 'n1', name: 'Number 1'"
        }
    }
}"""

def test_json_dump_uplevel_reference_while_dumping_from_lower_nesting_level():
    with root(prod, ef, aa=0):
        with NestedRepeatable(id='n1', name='Number 1', b=1) as n1:
            with NestedRepeatable(id='n2', c=2) as n2:
                NestedRepeatable(id='n3', uplevel_ref=n1, d=3)

    compare_json(n2, _uplevel_ref_expected_json_output, test_containment=False)


_json_dump_dir_error_expected_stderr = """Error in json generation:
Traceback (most recent call last):
  File "fake_multiconf_dir/json_output.py", line 999, in __call__
    entries = dir(obj)
  File "fake_dir/json_output_test.py", line %s, in __dir__
    raise Exception('Error in dir()')
Exception: Error in dir()
"""

_json_dump_dir_error_expected = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "__json_error__ # trying to list property methods, failed call to dir(), @properties will not be included": "Exception('Error in dir()',)",
        "aa": 2
    }
}"""

def test_json_dump_dir_error(capsys):
    @named_as('someitem')
    class Nested(ItemWithAA):
        _errorline = 0

        def __dir__(self):
            self._errorline = lineno() + 1
            raise Exception('Error in dir()')

        @property
        def c(self):
            return "will-not-show"

    with RootWithAA(prod, ef, aa=0) as cr:
        with Nested() as nn:
            nn.aa = 2

    cr.json()
    _sout, serr = capsys.readouterr()
    # pylint: disable=W0212
    assert replace_user_file_line_msg(replace_multiconf_file_line_msg(serr), cr.someitem._errorline) == _json_dump_dir_error_expected_stderr % cr.someitem._errorline
    compare_json(cr, _json_dump_dir_error_expected, expect_num_errors=1)


_json_dump_configbuilder_expected_json_full = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "b": 27,
            "name": "server1",
            "server_num": 1,
            "start": 1,
            "y_children": {
                "Hugo": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 10,
                    "name": "Hugo"
                }
            },
            "ys": {
                "server3": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "c": 28,
                    "name": "server3",
                    "server_num": 3,
                    "start": 3,
                    "y_children": {
                        "Hanna": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 11,
                            "name": "Hanna"
                        },
                        "Herbert": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 12,
                            "name": "Herbert"
                        }
                    },
                    "ys": {}
                },
                "server4": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "c": 28,
                    "name": "server4",
                    "server_num": 4,
                    "start": 3,
                    "y_children": {
                        "Hanna": "#ref, id: 0000",
                        "Herbert": "#ref, id: 0000"
                    },
                    "ys": {}
                }
            },
            "YBuilder.builder.0000": "#ref later, id: 0000"
        },
        "server2": {
            "__class__": "Y",
            "__id__": 0000,
            "b": 27,
            "name": "server2",
            "server_num": 2,
            "start": 1,
            "y_children": {
                "Hugo": "#ref, id: 0000"
            },
            "ys": {
                "server3": "#ref, id: 0000",
                "server4": "#ref, id: 0000"
            },
            "YBuilder.builder.0000": {
                "__class__": "YBuilder",
                "__id__": 0000,
                "c": 28,
                "start": 3,
                "y_children": {
                    "Hanna": "#ref, id: 0000",
                    "Herbert": "#ref, id: 0000"
                }
            }
        }
    },
    "YBuilder.builder.0000": {
        "__class__": "YBuilder",
        "__id__": 0000,
        "b": 27,
        "start": 1,
        "y_children": {
            "Hugo": "#ref, id: 0000"
        },
        "YBuilder.builder.0000": "#ref, id: 0000",
        "ys": {
            "server3": "#ref, id: 0000",
            "server4": "#ref, id: 0000"
        }
    },
    "aaa": 2,
    "aaa #static": true
}"""

_json_dump_configbuilder_expected_json_repeatable_item = """{
    "__class__": "Y",
    "__id__": 0000,
    "b": 27,
    "name": "server2",
    "server_num": 2,
    "start": 1,
    "y_children": {
        "Hugo": {
            "__class__": "YChild",
            "__id__": 0000,
            "a": 10,
            "name": "Hugo"
        }
    },
    "ys": {
        "server3": {
            "__class__": "Y",
            "__id__": 0000,
            "c": 28,
            "name": "server3",
            "server_num": 3,
            "start": 3,
            "y_children": {
                "Hanna": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 11,
                    "name": "Hanna"
                },
                "Herbert": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 12,
                    "name": "Herbert"
                }
            },
            "ys": {}
        },
        "server4": {
            "__class__": "Y",
            "__id__": 0000,
            "c": 28,
            "name": "server4",
            "server_num": 4,
            "start": 3,
            "y_children": {
                "Hanna": "#ref, id: 0000",
                "Herbert": "#ref, id: 0000"
            },
            "ys": {}
        }
    },
    "YBuilder.builder.0000": {
        "__class__": "YBuilder",
        "__id__": 0000,
        "c": 28,
        "start": 3,
        "y_children": {
            "Hanna": "#ref, id: 0000",
            "Herbert": "#ref, id: 0000"
        }
    }
}"""

_json_dump_configbuilder_dont_dump_expected_json_full = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "b": 27,
            "name": "server1",
            "server_num": 1,
            "start": 1,
            "y_children": {
                "Hugo": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 10,
                    "name": "Hugo"
                }
            },
            "ys": {
                "server3": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "c": 28,
                    "name": "server3",
                    "server_num": 3,
                    "start": 3,
                    "y_children": {
                        "Hanna": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 11,
                            "name": "Hanna"
                        },
                        "Herbert": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 12,
                            "name": "Herbert"
                        }
                    },
                    "ys": {}
                },
                "server4": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "c": 28,
                    "name": "server4",
                    "server_num": 4,
                    "start": 3,
                    "y_children": {
                        "Hanna": "#ref, id: 0000",
                        "Herbert": "#ref, id: 0000"
                    },
                    "ys": {}
                }
            }
        },
        "server2": {
            "__class__": "Y",
            "__id__": 0000,
            "b": 27,
            "name": "server2",
            "server_num": 2,
            "start": 1,
            "y_children": {
                "Hugo": "#ref, id: 0000"
            },
            "ys": {
                "server3": "#ref, id: 0000",
                "server4": "#ref, id: 0000"
            }
        }
    },
    "aaa": 2,
    "aaa #static": true
}"""

_json_dump_configbuilder_dont_dump_expected_json_repeatable_item = """{
    "__class__": "Y",
    "__id__": 0000,
    "b": 27,
    "name": "server2",
    "server_num": 2,
    "start": 1,
    "y_children": {
        "Hugo": {
            "__class__": "YChild",
            "__id__": 0000,
            "a": 10,
            "name": "Hugo"
        }
    },
    "ys": {
        "server3": {
            "__class__": "Y",
            "__id__": 0000,
            "c": 28,
            "name": "server3",
            "server_num": 3,
            "start": 3,
            "y_children": {
                "Hanna": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 11,
                    "name": "Hanna"
                },
                "Herbert": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 12,
                    "name": "Herbert"
                }
            },
            "ys": {}
        },
        "server4": {
            "__class__": "Y",
            "__id__": 0000,
            "c": 28,
            "name": "server4",
            "server_num": 4,
            "start": 3,
            "y_children": {
                "Hanna": "#ref, id: 0000",
                "Herbert": "#ref, id: 0000"
            },
            "ys": {}
        }
    }
}"""

def test_json_dump_configbuilder():
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super(YBuilder, self).__init__()
            self.start = start

        def build(self):
            for num in range(self.start, self.start + self.contained_in.aaa):
                Y(name='server%d' % num, server_num=num)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigRoot):
        aaa = 2

    @named_as('ys')
    @nested_repeatables('y_children, ys')
    class Y(RepeatableConfigItem):
        def __init__(self, name, server_num):
            super(Y, self).__init__(mc_key=name)
            self.name = name
            self.server_num = server_num

    @named_as('y_children')
    class YChild(RepeatableConfigItem):
        def __init__(self, name, a):
            super(YChild, self).__init__(mc_key=name)
            self.name = name
            self.a = a

    with ItemWithYs(prod, ef) as cr:
        with YBuilder() as yb1:
            yb1.b = 27
            YChild(name='Hugo', a=10)
            with YBuilder(start=3) as yb2:
                yb2.c = 28
                YChild(name='Hanna', a=11)
                YChild(name='Herbert', a=12)

    compare_json(cr, _json_dump_configbuilder_expected_json_full, replace_builders=True, test_decode=True)
    compare_json(cr.ys['server2'], _json_dump_configbuilder_expected_json_repeatable_item, replace_builders=True, test_decode=True)

    compare_json(cr, _json_dump_configbuilder_dont_dump_expected_json_full, replace_builders=False, dump_builders=False, test_decode=True)
    compare_json(cr.ys['server2'], _json_dump_configbuilder_dont_dump_expected_json_repeatable_item, replace_builders=False, dump_builders=False, test_decode=True)


if sys.version_info[0] < 3:
    from .json_output_test_py2 import _NamedNestedRepeatable
else:
    from .json_output_test_py3 import _NamedNestedRepeatable


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

def test_json_dump_property_method_returns_later_confitem_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return self.contained_in.someitems['two']

    with root(prod, ef, aa=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_same_level_expected_json)


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

    with root(prod, ef, aa=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')
        NamedNestedRepeatable(name='three')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_list_same_level_expected_json)


def test_json_dump_property_method_returns_later_confitem_tuple_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return self.contained_in.someitems['two'], self.contained_in.someitems['three']

    with root(prod, ef, aa=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')
        NamedNestedRepeatable(name='three')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_list_same_level_expected_json)


_json_dump_property_method_returns_later_confitem_dict_same_level_expected_json = """{
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

def test_json_dump_property_method_returns_later_confitem_dict_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return OrderedDict((('a', self.contained_in.someitems['two']), ('b', self.contained_in.someitems['three'])))

    with root(prod, ef, aa=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')
        NamedNestedRepeatable(name='three')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_dict_same_level_expected_json, test_decode=True)


def test_json_dump_property_method_returns_later_confitem_ordereddict_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return OrderedDict((('a', self.contained_in.someitems['two']), ('b', self.contained_in.someitems['three'])))

    with root(prod, ef, aa=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')
        NamedNestedRepeatable(name='three')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_dict_same_level_expected_json)


def test_json_dump_with_builders_containment_check():
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(mc_key=name)
            self.name = name

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost')

    @nested_repeatables('inners')
    class MiddleItem(RepeatableConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(mc_key=name)
            self.name = name

    class MyMiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MyMiddleBuilder, self).__init__()
            self.name = name

        def build(self):
            with MiddleItem(name=self.name):
                pass

    class MyOuterBuilder(ConfigBuilder):
        def __init__(self):
            super(MyOuterBuilder, self).__init__()

        def build(self):
            with MyMiddleBuilder('base'):
                InnerBuilder()

    @nested_repeatables('MiddleItems')
    class MyOuterItem(ConfigItem):
        pass

    with RootWithName(prod2, ef2_prod) as cr:
        cr.name = 'myp'
        with MyOuterItem():
            MyOuterBuilder()

    cr.json(builders=True)
    # TODO
    assert True


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
        "TTT": "<class 'multiconf.test.json_output_test.%(py3_local)sTTT'>"
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
        "aa": "<class 'multiconf.test.json_output_test.%(py3_local)sNonMcWithNestedClass'>"
    }
}"""

def test_json_dump_nested_class_non_mc():
    class McWithNestedClass(ConfigItem):
        class TTT(object):
            pass

    with root(prod, ef, aa=0) as cr:
        McWithNestedClass()
    compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_1 % dict(py3_local=py3_local('McWithNestedClass.')))

    class NonMcWithNestedClass(object):
        class TTT(object):
            pass

    with root(prod, ef, aa=0) as cr:
        with ItemWithAA() as ci:
            ci.aa = NonMcWithNestedClass
    compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_2 % dict(py3_local=py3_local()))


def test_json_dump_nested_class_with_json_equiv_non_mc():
    class McWithNestedClass(ConfigItem):
        class TTT(object):
            def json_equivalent(self):
                return ""

    with root(prod, ef, aa=0) as cr:
        McWithNestedClass()
    compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_1 % dict(py3_local=py3_local('McWithNestedClass.')))

    class NonMcWithNestedClass(object):
        class TTT(object):
            def json_equivalent(self):
                return ""

    with root(prod, ef, aa=0) as cr:
        with ItemWithAA() as ci:
            ci.aa = NonMcWithNestedClass
    compare_json(cr, _json_dump_test_json_dump_nested_class_non_mc_expected_json_2 % dict(py3_local=py3_local()))


_json_dump_multiple_errors_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "someitem": {
        "__class__": "SimpleItem",
        "__id__": 0000,
        "func": "__json_error__ # don't know how to handle obj of type: <%(type_or_class)s 'function'>",
        "someitem": {
            "__class__": "SimpleItem",
            "__id__": 0000,
            "func": "__json_error__ # don't know how to handle obj of type: <%(type_or_class)s 'function'>"
        }
    }
}"""

def test_json_dump_multiple_errors():
    def fff():
        pass

    def ggg():
        pass

    with ConfigRoot(prod, ef) as cr:
        with SimpleItem(func=fff):
            SimpleItem(func=ggg)

    compare_json(cr, _json_dump_multiple_errors_expected_json, expect_num_errors=2)


_iterable_attr_forward_item_ref = """{
    "__class__": "RootWithAA",
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
            "#ref, id: 0000"
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
            super(ItemWithAnXRef, self).__init__()
            self.item_refs = []

    @named_as('xx')
    class Xx(ConfigItem):
        def __init__(self):
            super(Xx, self).__init__()
            self.a = 1

    with RootWithAA(prod, ef) as cr:
        cr.aa = 0
        with ItemWithAnXRef() as x_ref:
            x_ref.setattr('aa', default=1, pp=2)
        xx = Xx()
        x_ref.item_refs.append(xx)

    compare_json(cr, _iterable_attr_forward_item_ref)


_iterable_tuple_attr_forward_item_ref = """{
    "__class__": "RootWithAA",
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
            "#ref, id: 0000"
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
            super(ItemWithAnXRef, self).__init__()
            self.item_refs = MC_REQUIRED

    @named_as('xx')
    class Xx(ConfigItem):
        def __init__(self):
            super(Xx, self).__init__()
            self.a = 1

    with RootWithAA(prod, ef) as cr:
        cr.aa = 0
        with ItemWithAnXRef() as x_ref:
            x_ref.setattr('aa', default=1, pp=2)
            xx = Xx()
            x_ref.item_refs = (xx,)

    compare_json(cr, _iterable_tuple_attr_forward_item_ref)


_dict_attr_forward_item_ref = """{
    "__class__": "RootWithAA",
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
            "xr": "#ref, id: 0000"
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
            super(ItemWithAnXRef, self).__init__()
            self.item_refs = {}

    @named_as('xx')
    class Xx(ConfigItem):
        def __init__(self):
            super(Xx, self).__init__()
            self.a = 1

    with RootWithAA(prod, ef) as cr:
        cr.aa = 0
        with ItemWithAnXRef() as x_ref:
            x_ref.setattr('aa', default=1, pp=2)
            xx = Xx()
            x_ref.item_refs['xr'] = xx

    compare_json(cr, _dict_attr_forward_item_ref)


_static_member_direct_expected_json = """{
    "__class__": "ConfigRoot",
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

    with ConfigRoot(prod, ef) as cr:
        Xx()

    compare_json(cr, _static_member_direct_expected_json)


_static_member_inherited_mc_expected_json = """{
    "__class__": "ConfigRoot",
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

    with ConfigRoot(prod, ef) as cr:
        Xx()
        Yy()
        Zz()
        Aa()
        Bb()

    compare_json(cr, _static_member_inherited_mc_expected_json)

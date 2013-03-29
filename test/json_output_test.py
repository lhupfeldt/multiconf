# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

try:    
    import demjson
    decode = demjson.JSON(strict=True).decode
except ImportError:
    def decode(_string):
        pass

from .utils import replace_ids, replace_ids_builder, to_compact

from .. import ConfigRoot, ConfigItem, InvalidUsageException, ConfigException, ConfigBuilder

from ..decorators import nested_repeatables, named_as, repeat
from ..envs import EnvFactory

ef = EnvFactory()


dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


_a_expected_json_output = """{
    "__class__": "root", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
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
                            "someitems": {}, 
                            "a": 1
                        }, 
                        "c-level3": {
                            "__class__": "NestedRepeatable", 
                            "__id__": 0000, 
                            "something": 1, 
                            "id": "c-level3", 
                            "someitems": {}
                        }
                    }
                }, 
                "c-level2": {
                    "__class__": "NestedRepeatable", 
                    "__id__": 0000, 
                    "something": 2, 
                    "id": "c-level2", 
                    "someitems": {}
                }
            }
        }, 
        "c-level1": {
            "__class__": "NestedRepeatable", 
            "__id__": 0000, 
            "something": 3, 
            "id": "c-level1", 
            "someitems": {}
        }
    }
}"""


_b_expected_json_output = """{
    "__class__": "root", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitems": {
        "a1": {
            "__class__": "NestedRepeatable", 
            "__id__": 0000, 
            "id": "a1", 
            "someitems": {}, 
            "some_value": 2
        }, 
        "b1": {
            "__class__": "NestedRepeatable", 
            "__id__": 0000, 
            "someattr": 12, 
            "id": "b1", 
            "someitems": {
                "a2": {
                    "__class__": "NestedRepeatable", 
                    "__id__": 0000, 
                    "id": "a2", 
                    "referenced_item": "#ref id: 0000", 
                    "someitems": {}
                }, 
                "b2": {
                    "__class__": "NestedRepeatable", 
                    "__id__": 0000, 
                    "id": "b2", 
                    "someitems": {}, 
                    "a": 1
                }
            }
        }
    }, 
    "anitem": {
        "__class__": "AnXItem", 
        "__id__": 0000, 
        "something": 3, 
        "ref": "#ref id: 0000"
    }
}"""


_c_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "SimpleItem", 
        "__id__": 0000, 
        "cycl": {
            "cyclic_item_ref": "#ref id: 0000"
        }, 
        "id": "b1", 
        "someattr": 12
    }
}"""


_e_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "Nested", 
        "__id__": 0000, 
        "m #invalid usage context": "InvalidUsageException('No m now',)"
    }
}"""


_e3_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "Nested", 
        "__id__": 0000, 
        "m": "#ref id: 0000", 
        "m #calculated": true
    }
}"""


_e4_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "referenced": {
        "__class__": "X", 
        "__id__": 0000, 
        "a": 0
    }, 
    "someitem": {
        "__class__": "Nested", 
        "__id__": 0000, 
        "other_conf_item": "#ref id: 0000", 
        "other_conf_item #calculated": true
    }
}"""


_e5_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "Nested", 
        "__id__": 0000, 
        "'other_conf_item' # json_error trying to handle property method": "NestedJsonCallError('Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?',)"
    }
}"""


# TODO: insert information about skipped objects into json output
_f_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "SimpleItem", 
        "__id__": 0000, 
        "b": {
            
        }
    }
}"""


_g_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
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


_h_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "someitem": {
        "__class__": "SimpleItem", 
        "__id__": 0000, 
        "func": "__json_error__ # don't know how to handle obj of type: <type 'function'>"
    }
}"""


_i_expected_json_output = """{
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
            "uplevel_ref": "#outside-ref: NestedRepeatable: id: 'n1', name: 'Number 1'", 
            "id": "n3", 
            "someitems": {}
        }
    }
}"""


_filter_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "Nested", 
        "__id__": 0000, 
        "b": 2, 
        "a": 1, 
        "a #calculated": true
    }
}"""


@nested_repeatables('someitems')
class root(ConfigRoot):
    pass


@named_as('someitems')
@nested_repeatables('someitems')
@repeat()
class NestedRepeatable(ConfigItem):
    pass


@named_as('someitem')
class SimpleItem(ConfigItem):
    def __init__(self, **kwargs):
        super(SimpleItem, self).__init__(**kwargs)


def test_json_dump_simple():
    with root(prod, [prod, pp], a=0) as cr:
        NestedRepeatable(id='a-level1')
        with NestedRepeatable(id='b-level1') as ci:
            NestedRepeatable(id='a-level2')
            with NestedRepeatable(id='b-level2') as ci:
                NestedRepeatable(id='a-level3')
                with NestedRepeatable(id='b-level3') as ci:
                    ci.setattr('a', prod=1, pp=2)
                NestedRepeatable(id='c-level3', something=1)
            NestedRepeatable(id='c-level2', something=2)
        NestedRepeatable(id='c-level1', something=3)

    assert replace_ids(cr.json()) == _a_expected_json_output
    assert replace_ids(cr.json(compact=True)) == to_compact(_a_expected_json_output)


def test_json_dump_cyclic_references_in_conf_items():
    @named_as('anitem')
    class AnXItem(ConfigItem):
        pass

    with root(prod, [prod, pp], a=0) as cr:
        with NestedRepeatable(id='a1') as ref_obj1:
            ref_obj1.setattr('some_value', pp=1, prod=2)

        with NestedRepeatable(id='b1', someattr=12):
            NestedRepeatable(id='a2', referenced_item=ref_obj1)
            with NestedRepeatable(id='b2') as ref_obj2:
                ref_obj2.setattr('a', prod=1, pp=2)
        with AnXItem(something=3) as last_item:
            last_item.setattr('ref', pp=ref_obj1, prod=ref_obj2)

    assert replace_ids(cr.json()) == _b_expected_json_output


def test_json_dump_cyclic_references_between_conf_items_and_other_objects():
    cycler = {}

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        with SimpleItem(id='b1', someattr=12, cycl=cycler) as ref_obj2:
            pass
        cycler['cyclic_item_ref'] = ref_obj2

    assert replace_ids(cr.json()) == _c_expected_json_output


_test_json_dump_property_method_expected = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
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

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    assert replace_ids(cr.json()) == _test_json_dump_property_method_expected
    assert replace_ids(cr.json(compact=True)) == to_compact(_test_json_dump_property_method_expected)


_test_json_dump_property_method_shadows_attribute_expected = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "Nested", 
        "__id__": 0000, 
        "m #shadowed": 7, 
        "m": 1, 
        "m #calculated": true
    }
}"""

def test_json_dump_property_method_shadows_attribute():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested(m=7)

    assert replace_ids(cr.json()) == _test_json_dump_property_method_shadows_attribute_expected
    assert replace_ids(cr.json(compact=True)) == to_compact(_test_json_dump_property_method_shadows_attribute_expected)
    assert cr.someitem.m == 1


def test_json_dump_property_method_raises_InvalidUsageException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise InvalidUsageException("No m now")

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    assert replace_ids(cr.json()) == _e_expected_json_output


_e2_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitem": {
        "__class__": "Nested", 
        "__id__": 0000, 
        "'m' # json_error trying to handle property method": "Exception('Something is wrong',)"
    }
}"""

def test_json_dump_property_method_raises_Exception():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise Exception("Something is wrong")

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    assert replace_ids(cr.json()) == _e2_expected_json_output


_e2b_expected_json_output = _e2_expected_json_output.replace('Exception', 'ConfigException')

def test_json_dump_property_method_raises_ConfigException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise ConfigException("Something is wrong")

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    assert replace_ids(cr.json()) == _e2b_expected_json_output


def test_json_dump_property_method_returns_self():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return self

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    assert replace_ids(cr.json()) == _e3_expected_json_output


def test_json_dump_property_method_returns_already_seen_conf_item():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            return self.root_conf.referenced

    @named_as('referenced')
    class X(ConfigItem):
        pass

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        X(a=0)
        Nested()

    assert replace_ids(cr.json()) == _e4_expected_json_output


def test_json_dump_property_method_calls_json():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            print self.json()

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    assert replace_ids(cr.json()) == _e5_expected_json_output


def test_json_dump_non_conf_item_not_json_serializable():
    class Key():
        def __repr__(self):
            return "<Key object>"

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        SimpleItem(b={Key():2})

    assert replace_ids(cr.json()) == _f_expected_json_output


def test_json_dump_non_conf_item():
    # This is an old style class
    class SomeClass():
        def __init__(self):
            self.a = 187

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        SimpleItem(a=SomeClass())

    assert replace_ids(cr.json()) == _g_expected_json_output
    # to_compact will not handle conversion of non-multiconf object representation, an extra '#as...' is inserted,
    # we remove it again
    assert replace_ids(cr.json(compact=True)) == to_compact(_g_expected_json_output).replace("SomeClass #as: 'xxxx', id", 'SomeClass #id')


def test_json_dump_unhandled_item_function_ref():
    def fff():
        pass

    with ConfigRoot(prod, [prod, pp]) as cr:
        SimpleItem(func=fff)

    assert replace_ids(cr.json()) == _h_expected_json_output


def test_json_dump_iterable():
    class MyIterable(object):
        def __iter__(self):
            yield 1

    with ConfigRoot(prod, [prod, pp]) as cr:
        SimpleItem(a=MyIterable())

    assert replace_ids(cr.json()) == _i_expected_json_output


def test_json_dump_uplevel_reference_while_dumping_from_lower_nesting_level():
    with root(prod, [prod, pp], a=0):
        with NestedRepeatable(id='n1', name='Number 1', b=1) as n1:
            with NestedRepeatable(id='n2', c=2) as n2:
                NestedRepeatable(id='n3', uplevel_ref=n1, d=3)

    assert replace_ids(n2.json()) == _uplevel_ref_expected_json_output


def test_json_dump_user_defined_attribute_filter():
    def json_filter(obj, key, value):
        return (False, None) if (key == 'hide_me1' or key == 'hide_me2') else (key, value)

    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def hide_me2(self):
            return "FAIL"

        @property
        def a(self):
            return 1

    with ConfigRoot(prod, [prod, pp], json_filter=json_filter, a=0, hide_me1='FAILED') as cr:
        Nested(b=2, hide_me1=7)

    assert replace_ids(cr.json()) == _filter_expected_json_output


_test_json_dump_configbuilder_expected_json_full = """{
    "__class__": "ItemWithYs #as: 'ItemWithYs', id: 0000", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "ys": {
        "server3": {
            "__class__": "Y #as: 'ys', id: 0000", 
            "name": "server3", 
            "server_num": 3, 
            "start": 3, 
            "c": 28, 
            "y_children": {
                "Hanna": {
                    "__class__": "YChild #as: 'y_children', id: 0000", 
                    "a": 11, 
                    "name": "Hanna"
                }, 
                "Herbert": {
                    "__class__": "YChild #as: 'y_children', id: 0000", 
                    "a": 12, 
                    "name": "Herbert"
                }
            }
        }, 
        "server4": {
            "__class__": "Y #as: 'ys', id: 0000", 
            "name": "server4", 
            "server_num": 4, 
            "start": 3, 
            "c": 28, 
            "y_children": {
                "Hanna": "#ref id: 0000", 
                "Herbert": "#ref id: 0000"
            }
        }, 
        "server1": {
            "__class__": "Y #as: 'ys', id: 0000", 
            "name": "server1", 
            "server_num": 1, 
            "start": 1, 
            "b": 27, 
            "y_children": {
                "Hugo": {
                    "__class__": "YChild #as: 'y_children', id: 0000", 
                    "a": 10, 
                    "name": "Hugo"
                }
            }, 
            "YBuilder.builder.0000": "#outside-ref: YBuilder"
        }, 
        "server2": {
            "__class__": "Y #as: 'ys', id: 0000", 
            "name": "server2", 
            "server_num": 2, 
            "start": 1, 
            "b": 27, 
            "y_children": {
                "Hugo": "#ref id: 0000"
            }, 
            "YBuilder.builder.0000": "#outside-ref: YBuilder"
        }
    }, 
    "YBuilder.builder.0000": {
        "__class__": "YBuilder #as: 'YBuilder.builder.0000', id: 0000", 
        "start": 1, 
        "b": 27, 
        "y_children": {
            "Hugo": "#ref id: 0000"
        }, 
        "YBuilder.builder.0000": {
            "__class__": "YBuilder #as: 'YBuilder.builder.0000', id: 0000", 
            "start": 3, 
            "c": 28, 
            "y_children": {
                "Hanna": "#ref id: 0000", 
                "Herbert": "#ref id: 0000"
            }, 
            "ys": {
                "server3": "#ref id: 0000", 
                "server4": "#ref id: 0000"
            }
        }, 
        "ys": {
            "server1": "#ref id: 0000", 
            "server2": "#ref id: 0000"
        }
    }, 
    "aaa": "2 #calculated"
}"""

_test_json_dump_configbuilder_expected_json_repeatable_item = """{
    "__class__": "Y #as: 'ys', id: 0000", 
    "name": "server2", 
    "server_num": 2, 
    "start": 1, 
    "b": 27, 
    "y_children": {
        "Hugo": {
            "__class__": "YChild #as: 'y_children', id: 0000", 
            "a": 10, 
            "name": "Hugo"
        }
    }, 
    "YBuilder.builder.0000": "#outside-ref: YBuilder"
}"""

def test_json_dump_configbuilder():
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super(YBuilder, self).__init__()
            self.start = start

        def build(self):
            for num in xrange(self.start, self.start + self.contained_in.aaa):
                Y(name='server%d' % num, server_num=num)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigRoot):
        aaa = 2

    @named_as('ys')
    @repeat()
    class Y(ConfigItem):
        pass

    @named_as('y_children')
    @repeat()
    class YChild(ConfigItem):
        pass

    with ItemWithYs(prod, [prod, pp]) as cr:
        with YBuilder() as yb1:
            yb1.b = 27
            YChild(name='Hugo', a=10)
            with YBuilder(start=3) as yb2:
                yb2.c = 28
                YChild(name='Hanna', a=11)
                YChild(name='Herbert', a=12)

    assert decode(_test_json_dump_configbuilder_expected_json_full)
    assert replace_ids_builder(cr.json(compact=True), named_as=False) == _test_json_dump_configbuilder_expected_json_full

    assert decode(_test_json_dump_configbuilder_expected_json_repeatable_item)
    assert replace_ids_builder(cr.ys['server2'].json(compact=True), named_as=False) == _test_json_dump_configbuilder_expected_json_repeatable_item

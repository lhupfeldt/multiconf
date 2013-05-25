# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re, abc
from collections import OrderedDict

from .. import ConfigRoot, ConfigItem, InvalidUsageException, ConfigException, ConfigBuilder

from ..decorators import nested_repeatables, named_as, repeat
from ..envs import EnvFactory

from .utils import replace_ids, lineno, to_compact, replace_user_file_line_msg, replace_multiconf_file_line_msg
from .compare_json import compare_json


ef = EnvFactory()


dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


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


_json_dump_simple_expected_json = """{
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

    compare_json(cr, _json_dump_simple_expected_json)


_json_dump_cyclic_references_in_conf_items_expected_json = """{
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

    compare_json(cr, _json_dump_cyclic_references_in_conf_items_expected_json, test_containment=False)


__json_dump_cyclic_references_between_conf_items_and_other_objects_expected_json = """{
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

def test_json_dump_cyclic_references_between_conf_items_and_other_objects():
    cycler = {}

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        with SimpleItem(id='b1', someattr=12, cycl=cycler) as ref_obj2:
            pass
        cycler['cyclic_item_ref'] = ref_obj2

    compare_json(cr, __json_dump_cyclic_references_between_conf_items_and_other_objects_expected_json)


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

    compare_json(cr, _test_json_dump_property_method_expected)


_json_dump_property_method_shadows_attribute_expected_json = """{
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

    compare_json(cr, _json_dump_property_method_shadows_attribute_expected_json)
    assert cr.someitem.m == 1


_json_dump_property_method_raises_InvalidUsageException_expected_json = """{
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

def test_json_dump_property_method_raises_InvalidUsageException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise InvalidUsageException("No m now")

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_raises_InvalidUsageException_expected_json)


_json_dump_property_method_raises_Exception_expected_json = """{
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

    compare_json(cr, _json_dump_property_method_raises_Exception_expected_json)


_e2b_expected_json_output = _json_dump_property_method_raises_Exception_expected_json.replace('Exception', 'ConfigException')

def test_json_dump_property_method_raises_ConfigException():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            raise ConfigException("Something is wrong")

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    compare_json(cr, _e2b_expected_json_output)


_json_dump_property_method_returns_self_expected_json = """{
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

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_returns_self_expected_json)


_json_dump_property_method_returns_already_seen_conf_item_expected_json = """{
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

    compare_json(cr, _json_dump_property_method_returns_already_seen_conf_item_expected_json)


_json_dump_property_method_calls_json_expected_json = """{
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

def test_json_dump_property_method_calls_json():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def other_conf_item(self):
            self.json()

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested()

    compare_json(cr, _json_dump_property_method_calls_json_expected_json)


# TODO: insert information about skipped objects into json output
_json_dump_non_conf_item_not_json_serializable_expected_json = """{
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

def test_json_dump_non_conf_item_not_json_serializable():
    class Key():
        def __repr__(self):
            return "<Key object>"

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        SimpleItem(b={Key():2})

    compare_json(cr, _json_dump_non_conf_item_not_json_serializable_expected_json)


_json_dump_non_conf_item_expected_json = """{
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

def test_json_dump_non_conf_item():
    # This is an old style class
    class SomeClass():
        def __init__(self):
            self.a = 187

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
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
        "func": "__json_error__ # don't know how to handle obj of type: <type 'function'>"
    }
}"""

def test_json_dump_unhandled_item_function_ref():
    def fff():
        pass

    with ConfigRoot(prod, [prod, pp]) as cr:
        SimpleItem(func=fff)

    compare_json(cr, _json_dump_unhandled_item_function_ref_expected_json)


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

    with ConfigRoot(prod, [prod, pp]) as cr:
        SimpleItem(a=MyIterable())

    compare_json(cr, _json_dump_iterable_expected_json)


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

def test_json_dump_uplevel_reference_while_dumping_from_lower_nesting_level():
    with root(prod, [prod, pp], a=0):
        with NestedRepeatable(id='n1', name='Number 1', b=1) as n1:
            with NestedRepeatable(id='n2', c=2) as n2:
                NestedRepeatable(id='n3', uplevel_ref=n1, d=3)

    compare_json(n2, _uplevel_ref_expected_json_output, test_containment=False)


_test_json_dump_dir_error_expected_stderr = """Error in json generation:
Traceback (most recent call last):
  File "fake_multiconf_dir/json_output.py", line 999, in default
    entries = dir(obj)
  File "fake_dir/json_output_test.py", line %s, in __dir__
    raise Exception('Error in dir()')
Exception: Error in dir()
"""

_test_json_dump_dir_error_expected = """{
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
        "__json_error__ # trying to list property methods, failed call to dir(), @properties will not be included": "Exception('Error in dir()',)", 
        "b": 2
    }
}"""

def test_json_dump_dir_error(capsys):
    @named_as('someitem')
    class Nested(ConfigItem):
        _errorline = 0
        def __dir__(self):
            self._errorline = lineno() + 1
            raise Exception('Error in dir()')

        @property
        def c(self):
            return "will-not-show"

    with ConfigRoot(prod, [prod, pp], a=0) as cr:
        Nested(b=2)

    cr.json()
    mc_regexp = re.compile('json_output.py", line [0-9]*')
    _sout, serr = capsys.readouterr()
    # pylint: disable=W0212
    assert replace_user_file_line_msg(replace_multiconf_file_line_msg(serr), cr.someitem._errorline) == _test_json_dump_dir_error_expected_stderr % cr.someitem._errorline
    compare_json(cr, _test_json_dump_dir_error_expected)


_test_json_dump_configbuilder_expected_json_full = """{
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
            "name": "server1", 
            "server_num": 1, 
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
                    "name": "server3", 
                    "server_num": 3, 
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
                    "ys": {}, 
                    "start": 3, 
                    "c": 28
                }, 
                "server4": {
                    "__class__": "Y", 
                    "__id__": 0000, 
                    "name": "server4", 
                    "server_num": 4, 
                    "y_children": {
                        "Hanna": "#ref id: 0000", 
                        "Herbert": "#ref id: 0000"
                    }, 
                    "ys": {}, 
                    "start": 3, 
                    "c": 28
                }
            }, 
            "start": 1, 
            "b": 27, 
            "YBuilder.builder.0000": "#ref later, id: 0000"
        }, 
        "server2": {
            "__class__": "Y", 
            "__id__": 0000, 
            "name": "server2", 
            "server_num": 2, 
            "y_children": {
                "Hugo": "#ref id: 0000"
            }, 
            "ys": {
                "server3": "#ref id: 0000", 
                "server4": "#ref id: 0000"
            }, 
            "start": 1, 
            "b": 27, 
            "YBuilder.builder.0000": {
                "__class__": "YBuilder", 
                "__id__": 0000, 
                "start": 3, 
                "c": 28, 
                "y_children": {
                    "Hanna": "#ref id: 0000", 
                    "Herbert": "#ref id: 0000"
                }
            }
        }
    }, 
    "YBuilder.builder.0000": {
        "__class__": "YBuilder", 
        "__id__": 0000, 
        "start": 1, 
        "b": 27, 
        "y_children": {
            "Hugo": "#ref id: 0000"
        }, 
        "YBuilder.builder.0000": "#ref id: 0000", 
        "ys": {
            "server3": "#ref id: 0000", 
            "server4": "#ref id: 0000"
        }
    }, 
    "aaa": 2, 
    "aaa #calculated": true
}"""

_test_json_dump_configbuilder_expected_json_repeatable_item = """{
    "__class__": "Y", 
    "__id__": 0000, 
    "name": "server2", 
    "server_num": 2, 
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
            "name": "server3", 
            "server_num": 3, 
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
            "ys": {}, 
            "start": 3, 
            "c": 28
        }, 
        "server4": {
            "__class__": "Y", 
            "__id__": 0000, 
            "name": "server4", 
            "server_num": 4, 
            "y_children": {
                "Hanna": "#ref id: 0000", 
                "Herbert": "#ref id: 0000"
            }, 
            "ys": {}, 
            "start": 3, 
            "c": 28
        }
    }, 
    "start": 1, 
    "b": 27, 
    "YBuilder.builder.0000": {
        "__class__": "YBuilder", 
        "__id__": 0000, 
        "start": 3, 
        "c": 28, 
        "y_children": {
            "Hanna": "#ref id: 0000", 
            "Herbert": "#ref id: 0000"
        }
    }
}"""

_test_json_dump_configbuilder_dont_dump_expected_json_full = """{
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
            "name": "server1", 
            "server_num": 1, 
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
                    "name": "server3", 
                    "server_num": 3, 
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
                    "ys": {}, 
                    "start": 3, 
                    "c": 28
                }, 
                "server4": {
                    "__class__": "Y", 
                    "__id__": 0000, 
                    "name": "server4", 
                    "server_num": 4, 
                    "y_children": {
                        "Hanna": "#ref id: 0000", 
                        "Herbert": "#ref id: 0000"
                    }, 
                    "ys": {}, 
                    "start": 3, 
                    "c": 28
                }
            }, 
            "start": 1, 
            "b": 27
        }, 
        "server2": {
            "__class__": "Y", 
            "__id__": 0000, 
            "name": "server2", 
            "server_num": 2, 
            "y_children": {
                "Hugo": "#ref id: 0000"
            }, 
            "ys": {
                "server3": "#ref id: 0000", 
                "server4": "#ref id: 0000"
            }, 
            "start": 1, 
            "b": 27
        }
    }, 
    "aaa": 2, 
    "aaa #calculated": true
}"""

_test_json_dump_configbuilder_dont_dump_expected_json_repeatable_item = """{
    "__class__": "Y", 
    "__id__": 0000, 
    "name": "server2", 
    "server_num": 2, 
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
            "name": "server3", 
            "server_num": 3, 
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
            "ys": {}, 
            "start": 3, 
            "c": 28
        }, 
        "server4": {
            "__class__": "Y", 
            "__id__": 0000, 
            "name": "server4", 
            "server_num": 4, 
            "y_children": {
                "Hanna": "#ref id: 0000", 
                "Herbert": "#ref id: 0000"
            }, 
            "ys": {}, 
            "start": 3, 
            "c": 28
        }
    }, 
    "start": 1, 
    "b": 27
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
    @nested_repeatables('y_children, ys')
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

    compare_json(cr, _test_json_dump_configbuilder_expected_json_full, replace_builders=True, test_decode=True)
    compare_json(cr.ys['server2'], _test_json_dump_configbuilder_expected_json_repeatable_item, replace_builders=True, test_decode=True)

    compare_json(cr, _test_json_dump_configbuilder_dont_dump_expected_json_full, replace_builders=False, dump_builders=False, test_decode=True)
    compare_json(cr.ys['server2'], _test_json_dump_configbuilder_dont_dump_expected_json_repeatable_item, replace_builders=False, dump_builders=False, test_decode=True)


@named_as('someitems')
@nested_repeatables('someitems')
@repeat()
class _NamedNestedRepeatable(ConfigItem):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        super(_NamedNestedRepeatable, self).__init__(name=name)
        self.x = 3

    @abc.abstractproperty
    def m(self):
        pass


# TODO: Not absolutely correct output (not outside ref)
_json_dump_property_method_returns_later_confitem_same_level_expected_json = """{
    "__class__": "root", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "someitems": {
        "one": {
            "__class__": "NamedNestedRepeatable", 
            "__id__": 0000, 
            "name": "one", 
            "someitems": {}, 
            "x": 3, 
            "m": "#ref later, id: 0000", 
            "m #calculated": true
        }, 
        "two": {
            "__class__": "NamedNestedRepeatable", 
            "__id__": 0000, 
            "name": "two", 
            "someitems": {}, 
            "x": 3, 
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

    with root(prod, [prod, pp], a=0) as cr:
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
    "a": 0, 
    "someitems": {
        "one": {
            "__class__": "NamedNestedRepeatable", 
            "__id__": 0000, 
            "name": "one", 
            "someitems": {}, 
            "x": 3, 
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
            "someitems": {}, 
            "x": 3, 
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
            "someitems": {}, 
            "x": 3, 
            "m": [
                "#ref id: 0000", 
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

    with root(prod, [prod, pp], a=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')
        NamedNestedRepeatable(name='three')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_list_same_level_expected_json)


def test_json_dump_property_method_returns_later_confitem_tuple_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return self.contained_in.someitems['two'], self.contained_in.someitems['three']

    with root(prod, [prod, pp], a=0) as cr:
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
    "a": 0, 
    "someitems": {
        "one": {
            "__class__": "NamedNestedRepeatable", 
            "__id__": 0000, 
            "name": "one", 
            "someitems": {}, 
            "x": 3, 
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
            "someitems": {}, 
            "x": 3, 
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
            "someitems": {}, 
            "x": 3, 
            "m": {
                "a": "#ref id: 0000", 
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
            return dict(a=self.contained_in.someitems['two'], b=self.contained_in.someitems['three'])

    with root(prod, [prod, pp], a=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')
        NamedNestedRepeatable(name='three')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_dict_same_level_expected_json, test_decode=True)


def test_json_dump_property_method_returns_later_confitem_ordereddict_same_level():
    class NamedNestedRepeatable(_NamedNestedRepeatable):
        @property
        def m(self):
            return OrderedDict((('a', self.contained_in.someitems['two']), ('b', self.contained_in.someitems['three'])))

    with root(prod, [prod, pp], a=0) as cr:
        NamedNestedRepeatable(name='one')
        NamedNestedRepeatable(name='two')
        NamedNestedRepeatable(name='three')

    compare_json(cr, _json_dump_property_method_returns_later_confitem_dict_same_level_expected_json)


def test_json_dump_with_builders_containment_check():
    @repeat()
    @named_as('inners')
    class InnerItem(ConfigItem):
        def __init__(self, name):
            super(InnerItem, self).__init__(name=name)

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def build(self):
            InnerItem('innermost')

    @repeat()
    @nested_repeatables('inners')
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(id=name)

    class MyMiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MyMiddleBuilder, self).__init__(name=name)

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

    with ConfigRoot(prod, [prod], name='myp') as cr:
        with MyOuterItem():
            MyOuterBuilder()

    cr.json(builders=True)
    assert True

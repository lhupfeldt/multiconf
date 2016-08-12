# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

from .. import ConfigRoot, ConfigItem, MC_REQUIRED

from ..decorators import named_as
from ..envs import EnvFactory

from .utils.utils import py3_local
from .utils.compare_json import compare_json
from .utils.tstclasses import RootWithAA


ef = EnvFactory()

pp = ef.Env('pp')
prod = ef.Env('prod')


_filter_expected_json = """{
    "__class__": "RootWithHideMe1",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "b": 2,
        "a": 1,
        "a #calculated": true
    }
}"""

def test_json_dump_user_defined_attribute_filter():
    def json_filter(_obj, key, value):
        return (False, None) if (key == 'hide_me1' or key == 'hide_me2') else (key, value)

    class RootWithHideMe1(RootWithAA):
        def __init__(self, selected_env, env_factory, mc_allow_todo=False, mc_allow_current_env_todo=False, mc_json_filter=None, aa=MC_REQUIRED):
            super(RootWithHideMe1, self).__init__(selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter,
                                                  mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo,
                                                  aa=aa)
            self.hide_me1 = MC_REQUIRED

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self, b, hide_me1):
            super(Nested, self).__init__()
            self.b = b
            self.hide_me1 = hide_me1
            
        @property
        def hide_me2(self):
            return "FAIL"

        @property
        def a(self):
            return 1

    with RootWithHideMe1(prod, ef, mc_json_filter=json_filter) as cr:
        cr.aa = 0
        cr.hide_me1 = 'FAILED'
        Nested(b=2, hide_me1=7)

    compare_json(cr, _filter_expected_json)


_json_fallback_handler_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "handled_non_item": [
        1,
        2
    ],
    "unhandled_non_item": "__json_error__ # don't know how to handle obj of type: <class 'multiconf.test.json_output_callbacks_test.%(py3_local)sUnHandledNonItem'>",
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "b": 2,
        "a": 1,
        "a #calculated": true
    }
}"""

def test_json_fallback_handler():
    class HandledNonItem(object):
        a = 1
        b = 2

    class UnHandledNonItem(object):
        a = 3

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self, b):
            super(Nested, self).__init__()
            self.b = b

        @property
        def a(self):
            return 1

    def json_fallback_handler(obj):
        if isinstance(obj, HandledNonItem):
            return [obj.a, obj.b], True
        return obj, False

    with RootWithAA(prod, ef, mc_json_fallback=json_fallback_handler) as cr:
        cr.aa = 0
        cr.setattr('handled_non_item?', default=HandledNonItem())
        cr.setattr('unhandled_non_item?', default=UnHandledNonItem())
        Nested(b=2)

    compare_json(cr, _json_fallback_handler_expected_json % dict(py3_local=py3_local()), expect_num_errors=1)


_json_fallback_handler_iterable_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "handled_non_items": [
        [
            1,
            7
        ],
        [
            2,
            7
        ]
    ]
}"""

def test_json_fallback_handler_iterable():
    class HandledNonItem(object):
        b = 7
        def __init__(self, a):
            self.a = a

    def json_fallback_handler(obj):
        if isinstance(obj, HandledNonItem):
            return [obj.a, obj.b], True
        return obj, False

    with RootWithAA(prod, ef, mc_json_fallback=json_fallback_handler) as cr:
        cr.aa = 0
        cr.setattr('handled_non_items?', default=[HandledNonItem(1), HandledNonItem(2)])

    compare_json(cr, _json_fallback_handler_iterable_expected_json)


_json_equivalent_expected_json = """{
    "__class__": "RootWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "handled_non_item": {
        "a": 1,
        "b": "Hi"
    },
    "someitem": {
        "__class__": "Item",
        "__id__": 0000,
        "a": 7
    }
}"""

def test_json_equivalent():
    class NonItemWithEquiv(object):
        def json_equivalent(self):
            return OrderedDict((('a', 1), ('b', 'Hi')))

    @named_as('someitem')
    class Item(ConfigItem):
        def __init__(self):
            super(Item, self).__init__()
            self.a = 7

    with RootWithAA(prod, ef) as cr:
        cr.aa = 0
        cr.setattr('handled_non_item?', default=NonItemWithEquiv())
        Item()

    compare_json(cr, _json_equivalent_expected_json)

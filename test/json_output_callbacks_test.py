# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, ConfigItem

from ..decorators import named_as
from ..envs import EnvFactory

from .utils.compare_json import compare_json

ef = EnvFactory()

pp = ef.Env('pp')
prod = ef.Env('prod')


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

def test_json_dump_user_defined_attribute_filter():
    def json_filter(_obj, key, value):
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

    compare_json(cr, _filter_expected_json_output)


_json_fallback_handler_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
    "handled_non_item": [
        1, 
        2
    ], 
    "unhandled_non_item": "__json_error__ # don't know how to handle obj of type: <class 'multiconf.test.json_output_callbacks_test.UnHandledNonItem'>", 
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
        @property
        def a(self):
            return 1

    def json_fallback_handler(obj):
        if isinstance(obj, HandledNonItem):
            return [obj.a, obj.b], True
        return obj, False

    with ConfigRoot(prod, [prod, pp], json_fallback=json_fallback_handler, a=0) as cr:
        cr.handled_non_item = HandledNonItem()
        cr.unhandled_non_item = UnHandledNonItem()
        Nested(b=2)

    compare_json(cr, _json_fallback_handler_expected_json_output)


_json_fallback_handler_iterable_expected_json_output = """{
    "__class__": "ConfigRoot", 
    "__id__": 0000, 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": 0, 
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

    with ConfigRoot(prod, [prod, pp], json_fallback=json_fallback_handler, a=0) as cr:
        cr.handled_non_items = [HandledNonItem(1), HandledNonItem(2)]

    compare_json(cr, _json_fallback_handler_iterable_expected_json_output)

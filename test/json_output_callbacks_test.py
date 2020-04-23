# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

from pytest import raises

from multiconf import mc_config, ConfigItem, MC_REQUIRED
from multiconf.decorators import named_as
from multiconf.envs import EnvFactory

from .utils.utils import replace_ids
from .utils.utils import local_func, py37_no_exc_comma, lines_in, file_line, next_line_num
from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithAA


ef = EnvFactory()

pp = ef.Env('pp')
prod = ef.Env('prod')


_json_dump_user_defined_attribute_filter_expected_json = """{
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

    class RootWithHideMe1(ItemWithAA):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__(aa=aa)
            self.hide_me1 = MC_REQUIRED

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self, b, hide_me1):
            super().__init__()
            self.b = b
            self.hide_me1 = hide_me1

        @property
        def hide_me2(self):
            return "FAIL"

        @property
        def a(self):
            return 1

    @mc_config(ef, mc_json_filter=json_filter, load_now=True)
    def config(root):
        with RootWithHideMe1() as cr:
            cr.aa = 0
            cr.hide_me1 = 'FAILED'
            with Nested(b=2, hide_me1=7):
                pass

    cr = config(prod).RootWithHideMe1
    assert compare_json(cr, _json_dump_user_defined_attribute_filter_expected_json)


_json_dump_user_defined_attribute_filter_exception_expected_json = """{
    "__class__": "RootWithHideMe1",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "hide_me1": "FAILED",
    "hide_me1 #json_error calling filter": "Exception('Error in filter'%(comma)s)",
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "b": 2,
        "hide_me1": 7,
        "hide_me1 #json_error calling filter": "Exception('Error in filter'%(comma)s)",
        "a": 1,
        "a #calculated": true,
        "hide_me2": "FAIL",
        "hide_me2 #calculated": true,
        "hide_me2 #json_error calling filter": "Exception('Error in filter'%(comma)s)"
    }
}""" % dict(comma=py37_no_exc_comma)

def test_json_dump_user_defined_attribute_filter_exception(capsys):
    def json_filter(_obj, key, value):
        if 'hide' in key:
            raise Exception("Error in filter")
        return key, value

    class RootWithHideMe1(ItemWithAA):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__(aa=aa)
            self.hide_me1 = MC_REQUIRED

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self, b, hide_me1):
            super().__init__()
            self.b = b
            self.hide_me1 = hide_me1

        @property
        def hide_me2(self):
            return "FAIL"

        @property
        def a(self):
            return 1

    @mc_config(ef, mc_json_filter=json_filter, load_now=True)
    def config(root):
        with RootWithHideMe1() as cr:
            cr.aa = 0
            cr.hide_me1 = 'FAILED'
            with Nested(b=2, hide_me1=7):
                pass

    cr = config(prod).RootWithHideMe1
    assert compare_json(cr, _json_dump_user_defined_attribute_filter_exception_expected_json, expect_num_errors=3)

    _sout, serr = capsys.readouterr()
    assert "Error in filter" in serr


_json_fallback_handler_expected_json = """{
    "__class__": "ItemWithAA",
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
    "unhandled_non_item": "__json_error__ # don't know how to handle obj of type: <class 'test.json_output_callbacks_test.%(local_func)sUnHandledNonItem'>",
    "someitem": {
        "__class__": "Nested",
        "__id__": 0000,
        "b": 2,
        "a": 1,
        "a #calculated": true
    }
}"""

def test_json_fallback_handler():
    class HandledNonItem():
        a = 1
        b = 2

    class UnHandledNonItem():
        a = 3

    @named_as('someitem')
    class Nested(ConfigItem):
        def __init__(self, b):
            super().__init__()
            self.b = b

        @property
        def a(self):
            return 1

    def json_fallback_handler(obj):
        if isinstance(obj, HandledNonItem):
            return [obj.a, obj.b], True
        return obj, False

    @mc_config(ef, mc_json_fallback=json_fallback_handler, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.aa = 0
            cr.setattr('handled_non_item', mc_set_unknown=True, default=HandledNonItem())
            cr.setattr('unhandled_non_item', mc_set_unknown=True, default=UnHandledNonItem())
            Nested(b=2)

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_fallback_handler_expected_json % dict(local_func=local_func()), expect_num_errors=1)


_json_fallback_handler_iterable_expected_json = """{
    "__class__": "ItemWithAA",
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
    class HandledNonItem():
        b = 7
        def __init__(self, a):
            self.a = a

    def json_fallback_handler(obj):
        if isinstance(obj, HandledNonItem):
            return [obj.a, obj.b], True
        return obj, False

    @mc_config(ef, mc_json_fallback=json_fallback_handler, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.aa = 0
            cr.setattr('handled_non_items', mc_set_unknown=True, default=[HandledNonItem(1), HandledNonItem(2)])

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_fallback_handler_iterable_expected_json)


_json_equivalent_expected_json = """{
    "__class__": "ItemWithAA",
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
    class NonItemWithEquiv():
        def json_equivalent(self):
            return OrderedDict((('a', 1), ('b', 'Hi')))

    @named_as('someitem')
    class Item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = 7

    @mc_config(ef, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.aa = 0
            cr.setattr('handled_non_item', mc_set_unknown=True, default=NonItemWithEquiv())
            Item()

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_equivalent_expected_json)


_json_equivalent_bad_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "handled_non_item": "__json_error__ calling 'json_equivalent': Exception('bad json_equivalent'%(comma)s)",
    "someitem": {
        "__class__": "Item",
        "__id__": 0000,
        "a": 7
    }
}""" % dict(comma=py37_no_exc_comma)

def test_json_equivalent_bad(capsys):
    errorline = [None]

    class NonItemWithEquiv():
        def json_equivalent(self):
            errorline[0] = next_line_num()
            raise Exception("bad json_equivalent")

    @named_as('someitem')
    class Item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = 7

    @mc_config(ef, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.aa = 0
            cr.setattr('handled_non_item', mc_set_unknown=True, default=NonItemWithEquiv())
            Item()

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_equivalent_bad_expected_json, expect_num_errors=1)

    _sout, serr = capsys.readouterr()

    assert lines_in(
        serr,
        "Traceback (most recent call last):",
        file_line(__file__, errorline[0]),
        "Exception: bad json_equivalent",
    )


_attribute_error_exception_generating_json_bad_json_equivalent_exc_ex = """{
    "__class__": "Xx #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "xxx #no value for Env('prod')": true,
    "egref": "__json_error__ calling 'json_equivalent': Error gettting repr of obj, type: <class 'test.json_output_callbacks_test.test_attribute_error_exception_generating_json_bad_json_equivalent.<locals>.BadException'>, exception: Exception: BadException bad __repr__",
    "xxx #json_error trying to handle property method": "Exception(\\"Error in 'xxx' property impl.\\"%(comma)s)"
}, object of type: <class 'test.json_output_callbacks_test.test_attribute_error_exception_generating_json_bad_json_equivalent.<locals>.Xx'> has no attribute 'xxx'. Attribute 'xxx' is defined as a multiconf attribute and as a @property method but value is undefined for Env('prod') and @property method call failed with: Exception("Error in 'xxx' property impl."%(comma)s)
""" % dict(comma=py37_no_exc_comma)

def test_attribute_error_exception_generating_json_bad_json_equivalent():
    class BadException(Exception):
        def __repr__(self):
            raise Exception("BadException bad __repr__")

    class X():
        def json_equivalent(self):
            raise BadException()

    class Xx(ConfigItem):
        @property
        def xxx(self):
            raise Exception("Error in 'xxx' property impl.")

        def mc_init(self):
            self.setattr('egref', default=X(), mc_set_unknown=True)

    @mc_config(ef, load_now=True)
    def config(root):
        with Xx() as xx:
            xx.setattr('xxx', pp=1, mc_overwrite_property=True)

    cr = config(prod)

    with raises(AttributeError) as exinfo:
        cr.Xx.xxx

    assert replace_ids(str(exinfo.value).strip()) == _attribute_error_exception_generating_json_bad_json_equivalent_exc_ex.strip()


_json_equivalent_attribute_error_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "handled_non_item": "__json_error__ calling 'json_equivalent': AttributeError('attribute error in json_equivalent'%(comma)s)",
    "someitem": {
        "__class__": "Item",
        "__id__": 0000,
        "a": 7
    }
}
""" % dict(comma=py37_no_exc_comma)

def test_json_equivalent_attribute_error(capsys):
    errorline = [None]

    class NonItemWithEquiv():
        def json_equivalent(self):
            errorline[0] = next_line_num()
            raise AttributeError("attribute error in json_equivalent")

    @named_as('someitem')
    class Item(ConfigItem):
        def __init__(self):
            super().__init__()
            self.a = 7

    @mc_config(ef, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.aa = 0
            cr.setattr('handled_non_item', mc_set_unknown=True, default=NonItemWithEquiv())
            Item()

    cr = config(prod).ItemWithAA
    assert compare_json(cr, _json_equivalent_attribute_error_expected_json.strip(), expect_num_errors=1)

    _sout, serr = capsys.readouterr()

    assert lines_in(
        serr,
        "Traceback (most recent call last):",
        file_line(__file__, errorline[0]),
        "AttributeError: attribute error in json_equivalent",
    )

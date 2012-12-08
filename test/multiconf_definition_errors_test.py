#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail, dummy

from .utils import lazy, config_error, lineno, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import nested_repeatables, repeat
from ..envs import EnvFactory

ef = EnvFactory()

dev2ct = ef.Env('dev2CT')
dev2st = ef.Env('dev2ST')
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3CT')
dev3st = ef.Env('dev3ST')
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_i_expected = """'ConfigItem' is defined both as simple value and a contained item: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen, defaults: {}"
}"""


_j_expected = """'RepeatableItems': {
    "__class__": "RepeatableItem #as: 'RepeatableItems', id: 0000, not-frozen, defaults: {}"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"""


_o_expected = """A value is already specified for: Env('dev2CT') from group EnvGroup('g_dev_overlap') {
     Env('dev2CT')
}=3, previous value: EnvGroup('g_dev2') {
     Env('dev2CT'),
     Env('dev2ST')
}=2"""


_p_expected = """A value is already specified for: Env('dev2CT') from group EnvGroup('g_dev_overlap') {
     Env('dev2CT'),
     Env('dev3CT')
}=3, previous value: EnvGroup('g_dev2') {
     Env('dev2CT'),
     Env('dev2ST')
}=2"""


@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass

@repeat()
class RepeatableItem(ConfigItem):
    pass


class MultiConfDefinitionErrorsTest(unittest.TestCase):
    @test("non-env for instantiatiation env")
    def _config_root_args1(self):
        try:
            project('Why?', [prod])
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "project: env must be instance of 'Env'; found type 'str': 'Why?'"

    @test("non-env in valid_envs")
    def _config_root_args2(self):
        try:
            project(prod, [prod, 'Why?'])
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "project: valid_envs items must be instance of 'Env'; found a 'str': 'Why?'"

    @test("valid_envs is not a sequence")
    def _config_root_args3(self):
        try:
            project(prod, 1)
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "project: valid_envs arg must be a 'Sequence'; found type 'int': 1"

    @test("valid_envs is a str")
    def _config_root_args4(self):
        try:
            project(prod, 'Why?')
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "project: valid_envs arg must be a 'Sequence'; found type 'str': 'Why?'"

    @test("valid_envs arg as EnvGroup")
    def _config_root_args5(self):
        ok (lazy(ConfigRoot, prod, valid_envs)).raises(ConfigException)

    @test("selected_conf not in valid_envs")
    def _config_root_args6(self):
        ok (lazy(ConfigRoot, prod, [dev3ct, dev3st])).raises(ConfigException)

    @test("assign to undefine env")
    def _e(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod]) as cr:
                    errorline = lineno() + 1
                    cr.a(pros="hello", prod="hi")
                fail ("Expected exception")
        except ConfigException as ex:
            _sout, serr = d_io
            ok (serr) == ce(errorline, "No such Env or EnvGroup: 'pros'")
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("value not assigned to all envs")
    def _f(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod, pp]) as cr:
                    errorline = lineno() + 1
                    cr.a(prod="hello")
                fail ("Expected exception")
        except ConfigException as ex:
            _sout, serr = d_io
            ok (serr) == ce(errorline, "Attribute: 'a' did not receive a value for env Env('pp')")
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("property defined with different types")
    def _g(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod, pp]) as cr:
                    errorline = lineno() + 1
                    cr.a(prod=1, pp="hello")
                fail ("Expected exception")
        except ConfigException as ex:
            _sout, serr = d_io
            ok (serr) == ce(errorline, "Found different types of property 'a' for different envs: <type 'int'> previously found types: [<type 'str'>]")
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("property redefined")
    def _h(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod]) as cr:
                    cr.a(prod=1)
                    errorline = lineno() + 1
                    cr.a(prod=2)
                fail ("Expected exception")
        except ConfigException as ex:
            _sout, serr = d_io
            ok (serr) == ce(errorline, "Redefined attribute 'a'")
            ok (ex.message) == "Attribute redefinition error: 'a'"

    @test("nested item overrides simple property")
    def _i(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                cr.ConfigItem(prod="hello")
                ConfigItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (replace_ids(ex.message, named_as=False)) == _i_expected

    @test("nested repeatable item overrides simple property - not contained in repeatable")
    def _j(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                cr.RepeatableItems(prod="hello")
                RepeatableItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (replace_ids(ex.message, named_as=False)) == _j_expected

    #@test("nested repeatable item overrides simple property - contained in repeatable")
    #@todo
    #def _k(self):
    #    try:
    #        @nested_repeatables('children')
    #        class root(ConfigRoot):
    #            pass
    #
    #        @named_as('children')
    #        class rchild(RepeatableItem):
    #            pass
    #
    #        with root(prod, [prod]) as cr:
    #            # TODO
    #            #cr.children(prod="hello")
    #            rchild()
    #        fail ("Expected exception")
    #    except ConfigException as ex:
    #        ok (ex.message) == "'children' is defined both as simple value and a contained item: children {\n}"

    @test("simple property overrides contained item")
    def _l(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod]) as cr:
                    ConfigItem()
                    errorline = lineno() + 1
                    cr.ConfigItem(prod="hello")
                fail ("Expected exception")
        except ConfigException as ex:
            _sout, serr = d_io
            ok (serr) == ce(errorline, "Redefined attribute 'ConfigItem'")
            ok (ex.message) == "Attribute redefinition error: 'ConfigItem'"

    @test("repeated non-repeatable item")
    def _m(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                ConfigItem()
                errorline = lineno() + 1
                ConfigItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Repeated non repeatable conf item: 'ConfigItem'"

    @test("nested repeatable items with repeated name")
    def _n(self):
        try:
            with project(prod, [prod]) as cr:
                RepeatableItem(id='my_name')
                RepeatableItem(id='my_name')
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Re-used id/name 'my_name' in nested objects"

    @test("value defined through multiple groups")
    def _o(self):
        try:
            g_dev_overlap = ef.EnvGroup('g_dev_overlap', dev2ct)

            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod, g_dev2, g_dev_overlap]) as cr:
                    errorline = lineno() + 1
                    cr.a(prod=1, g_dev2=2, g_dev_overlap=3)
                fail ("Expected exception")
        except ConfigException as ex:
            _sout, serr = d_io            
            ok (serr) == ce(errorline, _o_expected)
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("value defined through multiple groups")
    def _p(self):
        try:
            g_dev_overlap = ef.EnvGroup('g_dev_overlap', dev2ct, dev3ct)

            with dummy.dummy_io('stdin not used') as d_io:
                with ConfigRoot(prod, [prod, g_dev2, g_dev_overlap]) as cr:
                    errorline = lineno() + 1
                    cr.a(prod=1, g_dev2=2, g_dev_overlap=3)
                fail ("Expected exception")
        except ConfigException as ex:
            _sout, serr = d_io            
            ok (serr) == ce(errorline, _p_expected)
            ok (ex.message) == "There were 1 errors when defining attribute 'a'"

    @test("nested repeatable items with repeated name")
    def _q(self):
        try:
            with project(prod, [prod]) as cr:
                RepeatableItem(id='my_name')
                RepeatableItem(id='my_name')
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Re-used id/name 'my_name' in nested objects"

    @test("assigning to attribute")
    def _r(self):
        try:
            with project(prod, [prod]) as cr:
                cr.a = 1
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Trying to set a property 'a' on a config item"

    # TODO
    #@test("ConfigItem outside of root")
    #def _r(self):
    #    try:
    #        ConfigItem()
    #        fail ("Expected exception")
    #    except ConfigException as ex:
    #        ok (ex.message) == "Trying to set a property 'a' on a config item"

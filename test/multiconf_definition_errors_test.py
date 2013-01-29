#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail, dummy

from .utils import lazy, config_error, lineno, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException
from ..decorators import nested_repeatables, repeat, named_as
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
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen"
}"""


_j_expected = """'RepeatableItems': {
    "__class__": "RepeatableItem #as: 'RepeatableItems', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"""


_k1_expected = """'RepeatableItems': {
    "__class__": "RepeatableItem #as: 'RepeatableItems', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"""


_k4_expected = """'RepeatableItems': {
    "__class__": "RepeatableItems #as: 'RepeatableItems', id: 0000, not-frozen"
} is defined as non-repeatable, but the containing object has repeatable items with the same name: {
    "__class__": "project #as: 'project', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "RepeatableItems": {}
}"""


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


_group_for_selected_env_expected = """project: env must be instance of 'Env'; found type 'EnvGroup': EnvGroup('g_dev3') {
     Env('dev3CT'),
     Env('dev3ST')
}"""


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
            ok (ex.message) == "project: valid_envs items must be instance of 'Env' or 'EnvGroup'; found a 'str': 'Why?'"

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

    @test("attribute defined with different types")
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

    @test("attribute redefinition attempt")
    def _h(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                cr.a(prod=1)
                errorline = lineno() + 1
                cr.a(prod=2)
                fail ("Expected exception")
        except TypeError as ex:
            ok (ex.message) == "'int' object is not callable"

    @test("nested item overrides simple attribute")
    def _i(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                cr.ConfigItem(prod="hello")
                ConfigItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (replace_ids(ex.message, named_as=False)) == _i_expected

    @test("nested repeatable item not defined as repeatable in contained in class")
    def _j(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                RepeatableItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (replace_ids(ex.message, named_as=False)) == _j_expected

    @test("nested repeatable item overrides simple attribute - not contained in repeatable")
    def _k1(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                # cr.RepeatableItems is just an attribute named like an item
                cr.RepeatableItems(prod="hello")
                RepeatableItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (replace_ids(ex.message, named_as=False)) == _k1_expected

    @test("nested repeatable item shadowed by default attribute")
    def _k2(self):
        try:
            # RepeatableItems is just an attribute named like an item
            with project(prod, [prod], RepeatableItems=1) as cr:
                RepeatableItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (replace_ids(ex.message, named_as=False)) == "'RepeatableItems' defined as default value shadows a nested-repeatable"

    # @test("nested repeatable item overrides simple attribute - contained in repeatable")
    # @todo
    # def _k3(self):
    #     try:
    #         @nested_repeatables('children')
    #         class root(ConfigRoot):
    #             pass
    # 
    #         @named_as('children')
    #         class rchild(RepeatableItem):
    #             pass
    # 
    #         with root(prod, [prod]) as cr:
                  # TODO: 'cr' is an OrderedDict, so this call is not possible, which is fine, but the error message is not good
    #             cr.children(prod="hello")
    #             rchild()
    #         fail ("Expected exception")
    #     except ConfigException as ex:
    #         ok (ex.message) == "'children' is defined both as simple value and a contained item: children {\n}"

    @test("non-repeatable but container expects repeatable")
    def _k4(self):
        try:
            # The following class in not repeatable!
            class RepeatableItems(ConfigItem):
                pass

            with project(prod, [prod]) as cr:
                RepeatableItems()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (replace_ids(ex.message, named_as=False)) == _k4_expected

    @test("simple attribute attempt to override contained item")
    def _l(self):
        try:
            with ConfigRoot(prod, [prod]) as cr:
                ConfigItem()
                errorline = lineno() + 1
                cr.ConfigItem(prod="hello")
            fail ("Expected exception")
        except TypeError as ex:
            ok (ex.message) == "'ConfigItem' object is not callable"

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

    @test("assigning to attribute - root")
    def _r1(self):
        try:
            with project(prod, [prod]) as cr:
                cr.a = 1
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Trying to set a property 'a' on a config item"

    # Test that errorhandling in nested items work!
    @test("assigning to attribute - nested item")
    def _r2(self):
        try:
            with project(prod, [prod]) as cr:
                with ConfigItem() as ci:
                    ci.a = 1
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Trying to set a property 'a' on a config item"

    @test("ConfigItem outside of root")
    def _t(self):
        try:
            ConfigItem()
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "ConfigItem object must be nested (indirectly) in a 'ConfigRoot'"

    @test("using group for selected env")
    def _group_for_selected_env(self):
        try:
            project(g_dev3, [g_dev3])
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == _group_for_selected_env_expected

    @test("default value respecified in with_statement - root")
    def _default_respecified(self):
        try:
            with project(prod, [prod], a=1) as pr:
                pr.a(default=1)
            fail ("Expected exception")
        except ConfigException as ex:
            ok (ex.message) == "Attribute already has a default value: 'a'"

    @test("exception in __exit__ must print ex info and raise original exception if any pending")
    def _exception_in_exit(self):
        try:
            class root(ConfigRoot):
                pass
            
            class inner(ConfigBuilder):
                def build(self):
                    raise Exception("in build")

            with dummy.dummy_io('stdin not used') as d_io:
                with root(prod, [prod, pp], a=0):
                    with inner(id='n1', b=1):
                        raise Exception("in with")
            
            fail ("Expected exception")
        except Exception as ex:
            _sout, serr = d_io
            ok (serr) == "Exception in __exit__: Exception('in build',)\nException in with block will be raised\n"
            ok (ex.message) == 'in with'

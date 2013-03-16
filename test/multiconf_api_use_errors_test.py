#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import test, fail, dummy

from .utils import lazy, api_error, lineno, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigException, ConfigApiException
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


_expected_ex_msg = "An error was detected trying to get attribute '%s' on class 'inner'"
_extra_stderr = """
    - Attributes starting with '_' are reserved for internal MultiConf usage. You probably tried to use the
      MultiConf API in a derived class __init__ before calling the parent class __init__"""


def capie(line_num, *lines):
    return api_error(__file__, line_num, *lines)


@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass


@repeat()
class RepeatableItem(ConfigItem):
    pass


class MultiConfApiUseErrorsTest(unittest.TestCase):
    def find_contained_in_called_before_parent___init___test(self):
        try:
            class root(ConfigRoot):
                pass
            
            class inner(ConfigItem):
                def __init__(self, **kwargs):
                    global inner_errorline
                    # Error: find_contained_in must not be called before parent __init__
                    inner_errorline = lineno() + 1
                    self.find_contained_in('a')

            with dummy.dummy_io('stdin not used') as d_io:
                with root(prod, [prod, pp], a=0):
                    inner(id='n1', b=1)
            
            fail ("Expected exception")
        except ConfigApiException as ex:
            _sout, serr = d_io
            eex = _expected_ex_msg % '_contained_in'
            assert serr == capie(inner_errorline, eex + _extra_stderr)
            assert ex.message == eex

    def property_method_called_before_parent___init___test(self):
        try:
            class root(ConfigRoot):
                pass
            
            class inner(ConfigItem):
                def __init__(self, **kwargs):
                    global inner_errorline
                    # Error: env must not be called before parent __init__
                    inner_errorline = lineno() + 1
                    print self.env

            with dummy.dummy_io('stdin not used') as d_io:
                with root(prod, [prod, pp], a=0):
                    inner(id='n1', b=1)
            
            fail ("Expected exception")
        except ConfigApiException as ex:
            _sout, serr = d_io
            eex = _expected_ex_msg % '_root_conf'
            assert serr == capie(inner_errorline, eex + _extra_stderr)
            assert ex.message == eex

    def undefined_method_called_before_parent___init___test(self):
        try:
            class root(ConfigRoot):
                pass
            
            class inner(ConfigItem):
                def __init__(self, **kwargs):
                    global inner_errorline
                    inner_errorline = lineno() + 1
                    self.ttt('')

            with dummy.dummy_io('stdin not used') as d_io:
                with root(prod, [prod, pp], a=0):
                    inner(id='n1', b=1)
            
            fail ("Expected exception")
        except ConfigApiException as ex:
            _sout, serr = d_io
            eex = _expected_ex_msg % '_attributes'
            assert serr == capie(inner_errorline, eex + _extra_stderr)
            assert ex.message == eex

    def undefined_property_method_called_before_parent___init___test(self):
        try:
            class root(ConfigRoot):
                pass
            
            class inner(ConfigItem):
                def __init__(self, **kwargs):
                    global inner_errorline
                    inner_errorline = lineno() + 1
                    self.ttt

            with dummy.dummy_io('stdin not used') as d_io:
                with root(prod, [prod, pp], a=0):
                    inner(id='n1', b=1)
            
            fail ("Expected exception")
        except ConfigApiException as ex:
            _sout, serr = d_io
            eex = _expected_ex_msg % '_attributes'
            assert serr == capie(inner_errorline, eex + _extra_stderr)
            assert ex.message == eex

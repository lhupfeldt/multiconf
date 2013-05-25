#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import required, unchecked

from ..envs import EnvFactory

ef = EnvFactory()

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

dev2ct = ef.Env('dev2ct')
dev2st = ef.Env('dev2st')
g_dev = ef.EnvGroup('g_dev', dev2ct, dev2st)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)


@required('anattr, anotherattr')
@unchecked()
class uitem(ConfigItem):
    def __mc_init__(self):
        self.setattr('anattr', prod=2, g_dev=2)


class item(uitem):
    pass


def test_required_missing_unchecked_for_configroot():
    @required('anattr, anotherattr')
    @unchecked()
    class root(ConfigRoot):
        def __mc_init__(self):
            self.setattr('anattr', prod=2, g_dev=2)

    with root(prod, [g_dev, pp, prod]) as cr:
        cr.setattr('anattr', pp=1, g_dev=1)
        cr.setattr('anotherattr', prod=2)

    assert cr.anattr == 2
    assert cr.anotherattr == 2

    with root(pp, [g_dev, pp, prod]) as cr:
        cr.setattr('anattr', pp=1, g_dev=1)
        cr.setattr('anotherattr', prod=2)

    assert cr.anattr == 1


def test_required_missing_unchecked_for_configitem():
    with ConfigRoot(prod, [g_dev, pp, prod]) as cr:
        with uitem() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2)

    assert cr.uitem.anattr == 2
    assert cr.uitem.anotherattr == 2

    with ConfigRoot(dev2ct, [g_dev, pp, prod]) as cr:
        with uitem() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2)

    assert cr.uitem.anattr == 1


def test_required_missing_unchecked_base_for_configitem():
    with ConfigRoot(prod, [g_dev, pp, prod]) as cr:
        with item() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2, pp=1, g_dev=0)

    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 2

    with ConfigRoot(dev2ct, [g_dev, pp, prod]) as cr:
        with item() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2, pp=1, g_dev=0)

    assert cr.item.anattr == 1
    assert cr.item.anotherattr == 0


_required_missing_unchecked_super_for_configitem_expected1a = \
"""Attribute: 'anotherattr' did not receive a value for env Env('dev2ct'), which is a member of EnvGroup('g_dev') {
     Env('dev2ct'),
     Env('dev2st')
}"""

_required_missing_unchecked_super_for_configitem_expected1b = \
"""Attribute: 'anotherattr' did not receive a value for env Env('dev2st'), which is a member of EnvGroup('g_dev') {
     Env('dev2ct'),
     Env('dev2st')
}"""

_required_missing_unchecked_super_for_configitem_expected1_ex = """There were 2 errors when defining attribute 'anotherattr' on object: {
    "__class__": "item #as: 'item', id: 0000", 
    "anattr": 2, 
    "anotherattr": 2
}"""

_required_missing_unchecked_super_for_configitem_expected2_ex = """There were 1 errors when defining attribute 'anattr' on object: {
    "__class__": "item #as: 'item', id: 0000", 
    "anotherattr": 0, 
    "anattr": 2
}"""

_required_missing_unchecked_super_for_configitem_expected3_ex = """There were 1 errors when defining attribute 'anattr' on object: {
    "__class__": "item #as: 'item', id: 0000", 
    "anattr": 1, 
    "anotherattr": 0
}"""

def test_required_missing_unchecked_super_for_configitem(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [g_dev, pp, prod]) as cr:
            with item() as it:
                it.setattr('anattr', pp=1, g_dev=1)
                it.setattr('anotherattr', prod=2, pp=1)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, 
                      _required_missing_unchecked_super_for_configitem_expected1a,
                      _required_missing_unchecked_super_for_configitem_expected1b,
                      )
    assert replace_ids(exinfo.value.message, False) == _required_missing_unchecked_super_for_configitem_expected1_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev2ct, [g_dev, pp, prod]) as cr:
            with item() as it:
                it.setattr('anotherattr', prod=2, pp=1, g_dev=0)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Attribute: 'anattr' did not receive a value for env Env('pp')")
    assert replace_ids(exinfo.value.message, False) == _required_missing_unchecked_super_for_configitem_expected2_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev2ct, [g_dev, pp, prod]) as cr:
            with item() as it:
                it.setattr('anattr', g_dev=1)
                it.setattr('anotherattr', prod=2, pp=1, g_dev=0)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Attribute: 'anattr' did not receive a value for env Env('pp')")
    assert replace_ids(exinfo.value.message, False) == _required_missing_unchecked_super_for_configitem_expected3_ex

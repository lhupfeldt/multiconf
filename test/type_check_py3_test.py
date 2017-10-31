# Copyright (c) 2012-2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
import pytest
from pytest import raises

from multiconf import mc_config, ConfigException, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.utils import next_line_num, replace_ids, lines_in, start_file_line
from .utils.messages import already_printed_msg
from .utils.tstclasses import ItemWithAA
from .type_check import vcheck, skip_version_reason_unsupported


ef_pp_prod = EnvFactory()
pp = ef_pp_prod.Env('pp')
prod = ef_pp_prod.Env('prod')


_single_error_on_item_expected_ex = r"""There was 1 error when defining item: {{
    "__class__": "{0} #as: '{0}', id: 0000, not-frozen",
    "env": {{
        "__class__": "Env",
        "name": "{1}"
    }},
    "aa": {2}
}}""" + already_printed_msg


class ItemWithIntAA(ItemWithAA):
    def __init__(self, aa: int=MC_REQUIRED):
        super(ItemWithIntAA, self).__init__(aa=aa)


class ItemWithStrAA(ItemWithAA):
    def __init__(self, aa: str=None):
        super(ItemWithStrAA, self).__init__(aa=aa)


@pytest.mark.skipif(not vcheck(), reason=skip_version_reason_unsupported)
def test_attribute_defined_with_correct_types(capsys):
    @mc_config(ef_pp_prod)
    def config(_):
        with ItemWithIntAA() as cr:
            cr.setattr('aa', prod=1, pp=2)

    assert config(pp).ItemWithIntAA.aa == 2

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr


@pytest.mark.skipif(not vcheck(), reason=skip_version_reason_unsupported)
def test_attribute_defined_with_wrong_type(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef_pp_prod)
        def config(_):
            with ItemWithIntAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=1, pp="hello")

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: Expected value of type: <class 'int'>, got <class 'str'> for ItemWithIntAA.aa",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex.format('ItemWithIntAA', 'pp', '"hello"')


@pytest.mark.skipif(not vcheck(), reason=skip_version_reason_unsupported)
def test_attribute_defined_with_wrong_type_explicit_typecheck_enable(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef_pp_prod, do_type_check=True)
        def config(_):
            with ItemWithIntAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=1, pp="hello")

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: Expected value of type: <class 'int'>, got <class 'str'> for ItemWithIntAA.aa",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex.format('ItemWithIntAA', 'pp', '"hello"')


@pytest.mark.skipif(not vcheck(), reason=skip_version_reason_unsupported)
def test_attribute_defined_with_wrong_type_typecheck_disable(capsys):
    @mc_config(ef_pp_prod, do_type_check=False)
    def config(_):
        with ItemWithIntAA() as cr:
            cr.setattr('aa', prod=1, pp="hello")

    assert config(pp).ItemWithIntAA.aa == "hello"  # Don't do this at home

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr


@pytest.mark.skipif(not vcheck(), reason=skip_version_reason_unsupported)
def test_attribute_defined_with_wrong_type_default(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef_pp_prod)
        def config(_):
            with ItemWithIntAA() as cr:
                errorline[0] = next_line_num()
                cr.aa ="hello"

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: Expected value of type: <class 'int'>, got <class 'str'> for ItemWithIntAA.aa",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex.format('ItemWithIntAA', 'pp', '"hello"')


@pytest.mark.skipif(not vcheck(), reason=skip_version_reason_unsupported)
def test_attribute_defined_with_wrong_type_init_none(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef_pp_prod)
        def config(_):
            with ItemWithStrAA() as cr:
                errorline[0] = next_line_num()
                cr.setattr('aa', prod=1, pp={})

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        "^ConfigError: Expected value with one of following types: (<class 'str'>, <class 'NoneType'>), got <class 'dict'> for ItemWithStrAA.aa",
    )
    assert replace_ids(str(exinfo.value), False) == _single_error_on_item_expected_ex.format('ItemWithStrAA', 'pp', '{}')

# Copyright (c) 2012-2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
import pytest
from pytest import raises

from .utils.utils import next_line_num, replace_ids, lines_in, start_file_line
from .utils.messages import already_printed_msg

from multiconf import mc_config, ConfigException
from multiconf.envs import EnvFactory


ef_pp_prod = EnvFactory()
pp = ef_pp_prod.Env('pp')
prod = ef_pp_prod.Env('prod')



def test_type_check_enable_not_allowed_for_py2(capsys):
    with raises(ConfigException) as exinfo:
        @mc_config(ef_pp_prod, do_type_check=True)
        def _(_):
            pass

    assert str(exinfo.value) == "Type checking only supported from Python 3.6.1"

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr


def test_type_check_disable_allowed_for_py2(capsys):
    @mc_config(ef_pp_prod, do_type_check=False)
    def _(_):
        pass

    ef_pp_prod.config(pp)

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

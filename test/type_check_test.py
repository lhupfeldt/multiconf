# Copyright (c) 2012-2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys

# pylint: disable=E0611
import pytest
from pytest import raises

from multiconf import mc_config, ConfigException
from multiconf.envs import EnvFactory

from .type_check import vcheck, skip_version_reason_supported


_major_version = sys.version_info[0]

ef_pp_prod = EnvFactory()
pp = ef_pp_prod.Env('pp')
prod = ef_pp_prod.Env('prod')


@pytest.mark.skipif(vcheck() and _major_version >= 3, reason=skip_version_reason_supported)
def test_type_check_enable_not_allowed_for_older_python(capsys):
    with raises(ConfigException) as exinfo:
        @mc_config(ef_pp_prod, do_type_check=True)
        def config(_):
            pass

    assert str(exinfo.value) == "Type checking only supported from Python 3.6.1"

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr


def test_type_check_disable_allowed(capsys):
    @mc_config(ef_pp_prod, do_type_check=False)
    def config(_):
        pass

    config(pp)

    sout, serr = capsys.readouterr()
    assert not sout
    assert not serr

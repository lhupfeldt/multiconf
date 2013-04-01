#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..envs import EnvFactory


ef = EnvFactory()
prod = ef.Env('prod')


def test_root_user_validate_error():
    class root(ConfigRoot):
        def validate(self):
            raise Exception("Error in root validate")

    with raises(Exception) as exinfo:
        with root(prod, [prod]):
            pass

    assert exinfo.value.message == "Error in root validate"


def test_item_user_validate_error():
    class item(ConfigItem):
        def validate(self):
            raise Exception("Error in item validate")

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, [prod]):
            item()

    assert exinfo.value.message == "Error in item validate"


def test_builder_user_validate_error():
    class builder(ConfigBuilder):
        def build(self):
            pass

        def validate(self):
            raise Exception("Error in builder validate")

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, [prod]):
            builder()

    assert exinfo.value.message == "Error in builder validate"

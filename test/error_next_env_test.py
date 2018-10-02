# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os.path

from pytest import raises

from multiconf import mc_config, ConfigException, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.utils import next_line_num, lines_in, start_file_line, file_line
from .utils.messages import already_printed_msg
from .utils.messages import config_error_mc_required_expected
from .utils.tstclasses import ItemWithAA


_here = os.path.dirname(__file__)

ef_prod_pp_tst_dev = EnvFactory()
dev = ef_prod_pp_tst_dev.Env('dev')
tst = ef_prod_pp_tst_dev.Env('tst')
pp = ef_prod_pp_tst_dev.Env('pp')
prod = ef_prod_pp_tst_dev.Env('prod')


def test_attribute_mc_required_error_next_env(capsys):
    errorline = [None]

    @mc_config(ef_prod_pp_tst_dev)
    def config(root):
        with ItemWithAA() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', dev=MC_REQUIRED, tst="hello", pp=MC_REQUIRED, prod=MC_REQUIRED)

    with raises(ConfigException) as exinfo:
        config.load(error_next_env=True)

    # config(prod3)
    sout, serr = capsys.readouterr()
    print(serr)

    assert sout == ""

    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='aa', env=dev),
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='aa', env=pp),
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='aa', env=prod),
    )
    assert str(exinfo.value) == "The following envs had errors [Env('dev'), Env('pp'), Env('prod')]"


def test_attribute_mc_required_mc_select_envs_error_next_env(capsys):
    errorline_mc_select_envs = [None]
    errorline_setattr = [None]

    @mc_config(ef_prod_pp_tst_dev)
    def config(root):
        with ItemWithAA() as cr:
            errorline_mc_select_envs[0] = next_line_num()
            cr.mc_select_envs(exclude=[pp], include=[dev, tst, prod, pp])
            errorline_setattr[0] = next_line_num()
            cr.setattr('aa', dev=MC_REQUIRED, tst="hello", prod=MC_REQUIRED)

    with raises(ConfigException) as exinfo:
        config.load(error_next_env=True)

    # config(prod3)
    sout, serr = capsys.readouterr()
    print(serr)

    assert sout == ""

    assert lines_in(
        serr,
        start_file_line(__file__, errorline_setattr[0]),
        config_error_mc_required_expected.format(attr='aa', env=dev),
        "^ConfigException: There was 1 error when defining item: {",
        start_file_line(__file__, errorline_mc_select_envs[0]),
        "ConfigError: Env('pp') is specified in both include and exclude, with no single most specific group or direct env:",
        " - from exclude: Env('pp')",
        " - from include: Env('pp')",
        start_file_line(__file__, errorline_setattr[0]),
        config_error_mc_required_expected.format(attr='aa', env=pp),
        "^ConfigException: There were 2 errors when defining item: {",
        start_file_line(__file__, errorline_setattr[0]),
        config_error_mc_required_expected.format(attr='aa', env=prod),
        "^ConfigException: There was 1 error when defining item: {",
    )
    assert str(exinfo.value) == "The following envs had errors [Env('dev'), Env('pp'), Env('prod')]"


def test_stacktrace_error_next_env(capsys):
    errorline_setattr = [None]
    errorline_repeated_obj = [None]

    @mc_config(ef_prod_pp_tst_dev)
    def config(root):
        with ItemWithAA() as cr:
            cr.mc_select_envs(exclude=[pp])
            errorline_setattr[0] = next_line_num()
            cr.setattr('aa', dev=MC_REQUIRED, tst="hello", prod=MC_REQUIRED)
        errorline_repeated_obj[0] = next_line_num()
        ItemWithAA()

    with raises(ConfigException) as exinfo:
        config.load(error_next_env=True)

    # config(prod3)
    sout, serr = capsys.readouterr()
    print(serr)

    assert sout == ""

    tb_msg = "Traceback (most recent call last):"
    repeated_msg = "ConfigException: Repeated non repeatable conf item: 'ItemWithAA': <class 'test.utils.tstclasses.ItemWithAA'>"
    assert lines_in(
        serr,
        start_file_line(__file__, errorline_setattr[0]),
        config_error_mc_required_expected.format(attr='aa', env=dev),
        "ConfigException: There was 1 error when defining item: {",
        already_printed_msg[1:],
        "Error in config for Env('dev') above.",
        tb_msg,
        file_line(__file__, errorline_repeated_obj[0]),
        "ItemWithAA()",
        repeated_msg,
        "Error in config for Env('tst') above.",
        "Error in config for Env('pp') above.",
        start_file_line(__file__, errorline_setattr[0]),
        config_error_mc_required_expected.format(attr='aa', env=prod),
        "Error in config for Env('prod') above.",
    )

    assert str(exinfo.value) == "The following envs had errors [Env('dev'), Env('tst'), Env('pp'), Env('prod')]"

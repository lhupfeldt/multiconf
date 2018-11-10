# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises # pylint: disable=no-name-in-module

from multiconf import mc_config, ConfigItem, ConfigBuilder, ConfigException, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.utils import line_num, replace_ids, lines_in, start_file_line
from .utils.messages import already_printed_msg
from .utils.messages import config_error_mc_required_expected

ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')


_attribute_mc_required_init_args_missing_env_values_builder_expected_ex = """There was 1 error when defining item: {
    "__class__": "Requires #as: 'Requires', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg

def test_attribute_mc_required_init_args_missing_env_values_builder(capsys):
    errorline = [None]
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super().__init__()
            self.aa = aa

    class Builder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            Requires()

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, load_now=True)
        def config(_):
            with Builder():
                errorline[0] = line_num()

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline[0]),
        config_error_mc_required_expected.format(attr='aa', env=pp1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_init_args_missing_env_values_builder_expected_ex

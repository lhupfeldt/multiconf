# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem
from multiconf.decorators import named_as, nested_repeatables

from .utils.utils import config_error, replace_ids
from .utils.tstclasses import ItemWithName

from multiconf.envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_dev2ct = EnvFactory()
pp2 = ef2_prod_dev2ct.Env('dev2ct')
prod2 = ef2_prod_dev2ct.Env('prod')


_g_expected = """{
    "__class__": "root #as: 'project', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "name": "abc"
}"""

def test_named_as():
    @named_as('project')
    class root(ItemWithName):
        pass

    @mc_config(ef2_prod_dev2ct)
    def config(croot):
        with root() as proj:
            proj.name = 'abc'
        return proj

    cfg = ef2_prod_dev2ct.config(prod2)
    assert replace_ids(repr(cfg.mc_config_result), named_as=False) == _g_expected


def test_nested_repeatables():
    @nested_repeatables('ritm1', 'ritm2')
    class root(ConfigItem):
        pass

    @mc_config(ef1_prod)
    def config(croot):
        root()

    cr = ef1_prod.config(prod1).root
    assert cr.ritm1 == {}
    assert cr.ritm2 == {}

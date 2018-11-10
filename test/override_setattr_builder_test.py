# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


from multiconf import mc_config
from multiconf.envs import EnvFactory

from .utils.tstclasses import BuilderWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


class MeSetterBuilder(BuilderWithAA):
    def mc_build(self):
        pass

    def setme(self, name, mc_overwrite_property=False, mc_set_unknown=False, mc_force=False, **mevalues):
        super().setattr(
            name, mc_overwrite_property=mc_overwrite_property, mc_set_unknown=mc_set_unknown, mc_force=mc_force,
            mc_error_info_up_level=3, **mevalues)


def test_override_setattr():
    cb = [None]

    @mc_config(ef, load_now=True)
    def config(_):
        with MeSetterBuilder() as bb:
            bb.setme('aa', prod="hi3", pp="hello")
        cb[0] = bb

    config(prod)
    assert cb[0].aa == "hi3"

    config(pp)
    assert cb[0].aa == "hello"

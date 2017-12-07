# Copyright (c) 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from multiconf import mc_config, ConfigItem, ConfigBuilder
from multiconf.decorators import named_as
from multiconf.envs import EnvFactory


efac = EnvFactory()

e1 = efac.Env('e1')
e2 = efac.Env('e2')


@named_as('root')
class Root(ConfigItem):
    def __init__(self):
        super(Root, self).__init__()
        self.version = None

    def mc_init(self):
        Version(self.version)
        super(Root, self).mc_init()


class Version(ConfigBuilder):
    def __init__(self, version):
        super(Version, self).__init__()
        self.version = version

    def mc_build(self):
        ConfigItem()


def test_key():
    @mc_config(efac)
    def config(_):
        with Root() as cr:
            cr.setattr('version', default="1.0", e2="1.1")

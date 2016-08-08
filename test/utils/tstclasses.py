# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


from ... import ConfigRoot


class name_root(ConfigRoot):
    def __init__(self, selected_env, env_factory, name=None):
        super(name_root, self).__init__(selected_env, env_factory)
        self.name = name

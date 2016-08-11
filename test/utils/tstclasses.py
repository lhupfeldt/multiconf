# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


from ... import ConfigRoot, MC_REQUIRED


class name_root(ConfigRoot):
    def __init__(self, selected_env, env_factory, name=MC_REQUIRED):
        super(name_root, self).__init__(selected_env, env_factory)
        self.name = name


class RootWithA(ConfigRoot):
    def __init__(self, selected_env, env_factory, mc_allow_todo=False, mc_allow_current_env_todo=False, a=MC_REQUIRED):
        super(RootWithA, self).__init__(selected_env=selected_env, env_factory=env_factory,
                                        mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
        self.a = a

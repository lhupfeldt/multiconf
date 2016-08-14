# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


from ... import ConfigRoot, ConfigItem, MC_REQUIRED


class RootWithName(ConfigRoot):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                 mc_allow_todo=False, mc_allow_current_env_todo=False,
                 name=MC_REQUIRED):
        super(RootWithName, self).__init__(
            selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
            mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
        self.name = name


class RootWithAA(ConfigRoot):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                 mc_allow_todo=False, mc_allow_current_env_todo=False,
                 aa=MC_REQUIRED):
        super(RootWithAA, self).__init__(
            selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
            mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
        self.aa = aa


class RootWithAABB(ConfigRoot):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                 mc_allow_todo=False, mc_allow_current_env_todo=False,
                 aa=MC_REQUIRED, bb=None):
        super(RootWithAABB, self).__init__(
            selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
            mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
        self.aa = aa
        self.bb = bb


class ItemWithAA(ConfigItem):
    def __init__(self, aa=MC_REQUIRED):
        super(ItemWithAA, self).__init__()
        self.aa = aa


class ItemWithAABB(ConfigItem):
    def __init__(self, aa=MC_REQUIRED, bb=None):
        super(ItemWithAABB, self).__init__()
        self.aa = aa
        self.bb = bb

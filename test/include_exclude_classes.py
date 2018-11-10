# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import ConfigItem


# This is defined in a separate file to ensure the test of the file:line message handling is valid
class McSelectOverrideItem(ConfigItem):
    def mc_select_envs(self, include=None, exclude=None, mc_error_info_up_level=3):
        super().mc_select_envs(include, exclude, mc_error_info_up_level=mc_error_info_up_level)


# This is defined in a separate file to ensure the test of the file:line message handling is valid
class McSelectOverrideItem2(McSelectOverrideItem):
    def mc_select_envs(self, include=None, exclude=None):
        super().mc_select_envs(include, exclude, mc_error_info_up_level=4)

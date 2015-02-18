# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import abc

from .multiconf import _ConfigBuilder


class ConfigBuilder(_ConfigBuilder, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build(self):
        """Override this in derived classes. This is where child ConfigItems are declared"""

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from enum import Enum


class McInvalidValue(Enum):
    """Special values which may be assigned to attributes.

    Attributes:
        MC_NO_VALUE: This is the initial value for attribute until it receives a value for an Env. This will only be observed
            when iterating over the env values of an attribute and the ConfigItem was excluded from some Envs. See :meth:`~multiconf.ConfigItem.attr_env_items`.
            You should never set an attribute to this value.

        MC_REQUIRED: This is used as the default value for attributes in __init__ when there is no reasonable default.
            Multiconf will verify that a real value is assigned to the attribute during the config instantiation.

        MC_TODO: This can be used in the configuration as a temporary place holder for values which are currently unknown.
            There are various options to make multiconf report on MC_TODO values.
    """

    MC_NO_VALUE = 0
    MC_REQUIRED = 1
    MC_TODO = 2

    def __bool__(self):
        return False

    def __repr__(self):
        return self.name

    def json_equivalent(self):
        return self.__repr__()

    def __add__(self, _):
        return self

    def __radd__(self, _):
        return self

    def append(self, _):
        return self


MC_NO_VALUE = McInvalidValue.MC_NO_VALUE
MC_REQUIRED = McInvalidValue.MC_REQUIRED
MC_TODO = McInvalidValue.MC_TODO


class McTodoHandling(Enum):
    """Specify how to handle MC_TODO values in the configuration.

    Attributes:
        SILENT: Do not report MC_TODO
        WARNING: Print a warning about each MC_TODO value.
        ERROR: Print an error message about each MC_TODO value and raise an Exception.
    """

    SILENT = 0
    WARNING = 1
    ERROR = 2

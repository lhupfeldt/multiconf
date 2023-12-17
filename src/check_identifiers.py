# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
import keyword

from .config_errors import ConfigDefinitionException


def _isidentifier(name):
    if name in keyword.kwlist:
        return False
    return re.match(r'^[a-z_][a-z0-9_]*$', name, re.I) is not None


def check_valid_identifier(name):
    if not _isidentifier(name):
        raise ConfigDefinitionException(repr(name) + " is not a valid identifier.")


def check_valid_identifiers(names):
    invalid = []
    for name in names:
        if not _isidentifier(name):
            invalid.append(name)
    if not invalid:
        return
    if len(invalid) == 1:
        raise ConfigDefinitionException(repr(invalid[0]) + " is not a valid identifier.")
    raise ConfigDefinitionException(repr(invalid) + " are not valid identifiers.")

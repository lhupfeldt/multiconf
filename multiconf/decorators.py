# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys
import re
import keyword

from .config_errors import ConfigDefinitionException, _line_msg, _error_msg, _warning_msg
from .repeatable import RepeatableDict
#from . import ConfigBuilder


def _isidentifier(name):
    if name in keyword.kwlist:
        return False
    return re.match(r'^[a-z_][a-z0-9_]*$', name, re.I) is not None


# def _not_config_builder(cls, decorator_name):
#     if issubclass(cls, ConfigBuilder):
#         print(_line_msg(up_level=2), file=sys.stderr)
#         msg = "Decorator '@" + decorator_name + "' is not allowed on instance of " + ConfigBuilder.__name__ + "."
#         print(_error_msg(msg), file=sys.stderr)
#         raise ConfigDefinitionException(msg)


def _check_valid_identifier(name):
    if not _isidentifier(name):
        raise ConfigDefinitionException(repr(name) + " is not a valid identifier.")


def _check_valid_identifiers(names):
    invalid = []
    for name in names:
        if not _isidentifier(name):
            invalid.append(name)
    if not invalid:
        return
    if len(invalid) == 1:
        raise ConfigDefinitionException(repr(invalid[0]) + " is not a valid identifier.")
    raise ConfigDefinitionException(repr(invalid) + " are not valid identifiers.")


def _add_super_list_deco_values(cls, attr_names, deco_attr_name):
    _check_valid_identifiers(attr_names)

    super_names = getattr(super(cls, cls), '_mc_deco_' + deco_attr_name)
    for attr in super_names:
        if attr in attr_names:
            print(_line_msg(3), file=sys.stderr)
            msg = "Item name: '{name}' re-specified as '@{deco_attr_name}' on class: '{class_name}', was already inherited from a super class."
            print(_warning_msg(msg.format(name=attr, deco_attr_name=deco_attr_name, class_name=cls.__name__)), file=sys.stderr)

    return attr_names + super_names


def named_as(insert_as_name):
    def deco(cls):
        # _not_config_builder(cls, 'named_as')
        _check_valid_identifier(insert_as_name)
        cls._mc_deco_named_as = insert_as_name
        return cls

    return deco


def nested_repeatables(*attr_names):
    def deco(cls):
        # _not_config_builder(cls, 'nested_repeatables')
        cls._mc_deco_nested_repeatables = _add_super_list_deco_values(cls, attr_names, 'nested_repeatables')

        # Make descriptor work, an instance of the descriptor class mut be assigened at the class level
        for name in attr_names:
            setattr(cls, name, RepeatableDict(name, None))

        return cls

    return deco


def required(*attr_names):
    def deco(cls):
        cls._mc_deco_required = _add_super_list_deco_values(cls, attr_names, 'required')
        return cls

    return deco

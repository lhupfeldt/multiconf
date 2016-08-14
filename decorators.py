# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys
import re
import keyword

from .config_errors import ConfigDefinitionException, _line_msg, _error_msg, _warning_msg
from . import ConfigBuilder


def _isidentifier(name):
    if name in keyword.kwlist:
        return False
    return re.match(r'^[a-z_][a-z0-9_]*$', name, re.I) is not None


def _not_config_builder(cls, decorator_name):
    if issubclass(cls, ConfigBuilder):
        print(_line_msg(up_level=2), file=sys.stderr)
        msg = "Decorator '@" + decorator_name + "' is not allowed on instance of " + ConfigBuilder.__name__ + "."
        print(_error_msg(msg), file=sys.stderr)
        raise ConfigDefinitionException(msg)


def _check_valid_identifier(name):
    if not _isidentifier(name):
        raise ConfigDefinitionException(repr(name) + " is not a valid identifier")


def _check_valid_identifiers(names):
    invalid = []
    for name in names:
        if not _isidentifier(name):
            invalid.append(name)
    if not invalid:
        return
    if len(invalid) == 1:
        raise ConfigDefinitionException(repr(invalid[0]) + " is not a valid identifier")
    raise ConfigDefinitionException(repr(invalid) + " are not valid identifiers")


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
        _not_config_builder(cls, 'named_as')
        _check_valid_identifier(insert_as_name)
        cls._mc_deco_named_as = insert_as_name
        return cls

    return deco


def nested_repeatables(attr_names, *more_attr_names):
    def deco(cls):
        _not_config_builder(cls, 'nested_repeatables')
        names = [attr.strip() for attr in attr_names.split(',')] + list(more_attr_names)
        cls._mc_deco_nested_repeatables = _add_super_list_deco_values(cls, names, 'nested_repeatables')
        return cls

    return deco


def required(attr_names, *more_attr_names):
    def deco(cls):
        names = [attr.strip() for attr in attr_names.split(',')] + list(more_attr_names)
        cls._mc_deco_required = _add_super_list_deco_values(cls, names, 'required')
        return cls

    return deco


def unchecked():
    def deco(cls):
        cls._mc_deco_unchecked = cls
        return cls

    return deco


def strict_setattr():
    """Marks the class as having strict setattr behaviour, meaning that it is not allowed to set an unknown atributes outside of __init__.

    This is a transitional decorator to allow more seamless upgrading. Strict will become the only mode in a later version.
    """
    def deco(cls):
        cls._mc_deco_strict_setattr = True
        return cls

    return deco


def relaxed_setattr():
    """Marks the class as having relaxed setattr behaviour, meaning that it is allowed to set an unknown atributes outside of __init__.

    This is a transitional decorator to allow more seamless upgrading, by converting a class to the old behaviour.
    Strict will become the unly mode in a later version.
    """
    def deco(cls):
        cls._mc_deco_strict_setattr = False
        return cls

    return deco

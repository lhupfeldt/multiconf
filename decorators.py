# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
import keyword

from .config_errors import ConfigDefinitionException, _warning_msg as warn, _error_msg as error
from . import ConfigBuilder


def _isidentifier(name):
    if name in keyword.kwlist:
        return False
    return re.match(r'^[a-z_][a-z0-9_]*$', name, re.I) is not None


def _not_config_builder(cls, decorator_name):
    if issubclass(cls, ConfigBuilder):
        msg = "Decorator '@" + decorator_name + "' is not allowed on instance of ConfigBuilder."
        error(0, msg)
        raise ConfigDefinitionException(msg)


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


def _add_super_list_deco_values(cls, attr_names_str, deco_attr_name):
    attr_names = [attr.strip() for attr in attr_names_str.split(',')]
    _check_valid_identifiers(attr_names)

    super_names = getattr(super(cls, cls), '_deco_' + deco_attr_name)
    for attr in super_names:
        if attr in attr_names:
            warn(0, "Attribute name: " + repr(attr) + " re-specified as " + repr(deco_attr_name) + " on class: " + repr(cls.__name__) + " , was already inherited from a super class.",
                 up_level=3)

    return attr_names + super_names


def named_as(insert_as_name):
    def deco(cls):
        _not_config_builder(cls, 'named_as')
        _check_valid_identifiers((insert_as_name,))
        cls._deco_named_as = insert_as_name
        return cls

    return deco


def repeat():
    def deco(cls):
        _not_config_builder(cls, 'repeat')
        cls._deco_repeatable = True
        return cls

    return deco


def nested_repeatables(attr_names):
    def deco(cls):
        _not_config_builder(cls, 'nested_repeatables')
        cls._deco_nested_repeatables = _add_super_list_deco_values(cls, attr_names, 'nested_repeatables')
        return cls

    return deco


def required(attr_names):
    def deco(cls):
        cls._deco_required = _add_super_list_deco_values(cls, attr_names, 'required')
        return cls

    return deco


def required_if(attr_name, attr_names):
    def deco(cls):
        attributes = [attr.strip() for attr in attr_names.split(',')]
        _check_valid_identifiers([attr_name] + attributes)
        cls._deco_required_if = attr_name, attributes
        return cls

    return deco


def optional(attr_name):
    # TODO: Implement this cleanly so the a reasonable error message will be given
    return required_if(attr_name, attr_name)

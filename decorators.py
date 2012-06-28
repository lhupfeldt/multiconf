# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import re
import keyword
from config_errors import _warning_msg

class ConfigDefinitionException(Exception):
    def __init__(self, msg):
        super(ConfigDefinitionException, self).__init__(msg)


def _isidentifier(s):
    if s in keyword.kwlist:
        return False
    return re.match(r'^[a-z_][a-z0-9_]*$', s, re.I) is not None


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


def named_as(insert_as_name):
    def deco(cls):
        _check_valid_identifiers((insert_as_name,))
        cls._deco_named_as = insert_as_name
        return cls

    return deco


def repeat():
    def deco(cls):
        cls._deco_repeatable = True
        return cls

    return deco


def nested_repeatables(attr_names):
    def deco(cls):
        attributes = [attr.strip() for attr in attr_names.split(',')]
        _check_valid_identifiers(attributes)
        super_deco_nested_repeatables = super(cls, cls)._deco_nested_repeatables
        for attr in super_deco_nested_repeatables:
            if attr in attributes:
                _warning_msg("Attribute name: " + repr(attr) + " re-specified as 'nested_repeatables' on class: " + repr(cls.__name__) + " , was already inherited from a super class.")
        cls._deco_nested_repeatables = attributes + super_deco_nested_repeatables
        return cls

    return deco


def required(attr_names):
    def deco(cls):
        attributes = [attr.strip() for attr in attr_names.split(',')]
        _check_valid_identifiers(attributes)
        super_deco_required = super(cls, cls)._deco_required_attributes
        for attr in super_deco_required:
            if attr in attributes:
                _warning_msg("Attribute name: " + repr(attr) + " re-specified as 'required' on class: " + repr(cls.__name__) + " , was already inherited from a super class.")
        cls._deco_required_attributes = attributes + super_deco_required
        return cls

    return deco


def required_if(attr_name, attr_names):
    def deco(cls):
        attributes = [attr.strip() for attr in attr_names.split(',')]
        _check_valid_identifiers([attr_name] + attributes)
        cls._deco_required_if_attributes = attr_name, attributes
        return cls

    return deco


def override(attr_names):
    def deco(cls):
        attributes = [attr.strip() for attr in attr_names.split(',')]
        _check_valid_identifiers(attributes)
        super_deco_override = super(cls, cls)._deco_override_attributes
        for attr in super_deco_override:
            if attr in attributes:
                _warning_msg("Attribute name: " + repr(attr) + " re-specified as 'override' on class: " + repr(cls.__name__) + " , was already inherited from a super class.")
        cls._deco_override_attributes = attributes + super_deco_override
        return cls

    return deco


def optional(attr_name):
    # TODO: Implement this cleanly so the a reasonable error message will be given
    return required_if(attr_name, attr_name)

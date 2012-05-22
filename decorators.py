# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import re
import keyword

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
        cls._deco_nested_repeatables = attributes
        return cls

    return deco


def required(attr_names):
    def deco(cls):
        attributes = [attr.strip() for attr in attr_names.split(',')]
        _check_valid_identifiers(attributes)
        cls._deco_required_attributes = attributes
        return cls

    return deco


def required_if(attr_name, attr_names):
    def deco(cls):
        attributes = [attr.strip() for attr in attr_names.split(',')]
        _check_valid_identifiers([attr_name] + attributes)
        cls._deco_required_if_attributes = attr_name, attributes
        return cls

    return deco


def optional(attr_name):
    return required_if(attr_name, attr_name)

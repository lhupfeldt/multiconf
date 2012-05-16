# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

def required(attr_names):
    def deco(cls):
        cls._deco_required_attributes = [attr.strip() for attr in attr_names.split(',')]
        return cls

    return deco


def required_if(attr_name, attr_names):
    def deco(cls):
        cls._deco_required_if_attributes = attr_name, [attr.strip() for attr in attr_names.split(',')]
        return cls

    return deco


def optional(attr_name):
    return required_if(attr_name, attr_name)

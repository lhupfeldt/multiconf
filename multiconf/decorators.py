# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from .envs import EnvFactory
from .config_errors import ConfigException, ConfigDefinitionException, _line_msg, _error_msg, _warning_msg
from .repeatable import RepeatableDict
from .multiconf import McConfigRoot
from . import ConfigBuilder, RepeatableConfigItem, DefaultItems
from .check_identifiers import check_valid_identifier, check_valid_identifiers


def _not_allowed_on_class(cls, decorator_name, not_cls):
    if issubclass(cls, not_cls):
        print(_line_msg(up_level=2), file=sys.stderr)
        msg = "Decorator '@" + decorator_name + "' is not allowed on instance of " + not_cls.__name__ + "."
        print(_error_msg(msg), file=sys.stderr)
        raise ConfigDefinitionException(msg)


def _only_allowed_on_class(cls, decorator_name, only_cls):
    if issubclass(cls, RepeatableConfigItem):
        return

    print(_line_msg(up_level=2), file=sys.stderr)
    msg = "Decorator '@" + decorator_name + "' is only allowed on instance of " + only_cls.__name__ + "."
    print(_error_msg(msg), file=sys.stderr)
    raise ConfigDefinitionException(msg)


def _add_super_list_deco_values(cls, attr_names, deco_attr_name):
    check_valid_identifiers(attr_names)

    super_names = getattr(super(cls, cls), '_mc_deco_' + deco_attr_name)
    for attr in super_names:
        if attr in attr_names:
            print(_line_msg(3), file=sys.stderr)
            msg = "Item name: '{name}' re-specified as '@{deco_attr_name}' on class: '{class_name}', was already inherited from a super class."
            print(_warning_msg(msg.format(name=attr, deco_attr_name=deco_attr_name, class_name=cls.__name__)), file=sys.stderr)

    return attr_names + super_names


def named_as(insert_as_name):
    """Determine the name used to insert item in parent"""
    def deco(cls):
        _not_allowed_on_class(cls, named_as.__name__, ConfigBuilder)
        _not_allowed_on_class(cls, named_as.__name__, DefaultItems)
        check_valid_identifier(insert_as_name)
        cls._mc_deco_named_as = insert_as_name
        return cls

    return deco


def nested_repeatables(*attr_names):
    """Specify which nested (child) items will be repeatable."""
    def deco(cls):
        _not_allowed_on_class(cls, nested_repeatables.__name__, ConfigBuilder)
        _not_allowed_on_class(cls, nested_repeatables.__name__, DefaultItems)
        cls._mc_deco_nested_repeatables = _add_super_list_deco_values(cls, attr_names, 'nested_repeatables')

        # Make descriptor work, an instance of the descriptor class mut be assigened at the class level
        for name in attr_names:
            setattr(cls, name, RepeatableDict())

        return cls

    return deco


def required(*attr_names):
    """Specify nested (child) items that must be defined."""
    def deco(cls):
        _not_allowed_on_class(cls, required.__name__, DefaultItems)
        cls._mc_deco_required = _add_super_list_deco_values(cls, attr_names, 'required')
        return cls

    return deco


def repeatable_key(**name_value):
    """Set name and default value for the mc_key repeatable item __init__ argument.

    Arguments:
        **name_value (dict[name, val]): There must be exactly one name/value pair.
            E.g.:

            Use 'name' argument as the mc_key.::

                @named_as('xses')
                @repeatable_key(name=None)
                class X1(RepeatableConfigItem):
                    def __init__(name, ...)

            Only a single item of the following class can be created in the 'xses' repeatable.
            Use 'name' argument as the mc_key for the parent class, use value 'xxx' as the mc_key.::

                @repeatable_key(name='xxx')
                class X2(X1):
                    def __init__(...)  # No 'name' argument
                        super()._init__(name=None, ...)

            Only a single item of the following class can be created in the 'ys' repeatable.
            Use value 'nicekey' as the mc_key.::

                @named_as('ys')
                @repeatable_key(mc_key='nicekey')
                class X2(X1):
                    def __init__(...)  # No 'mc_key' argument
                        super()._init__(...)

    """

    def deco(cls):
        _only_allowed_on_class(cls, repeatable_key.__name__, RepeatableConfigItem)
        for key, value in name_value.items():
            cls._mc_key_name = key
            cls._mc_key_value = value
            return cls

        print(_line_msg(up_level=1), file=sys.stderr)
        msg = "Decorator '@" + repeatable_key.__name__ + "' takes exactly one key-value pair."
        print(_error_msg(msg), file=sys.stderr)
        raise ConfigDefinitionException(msg)

    return deco


def mc_config(env_factory, mc_json_filter=None, mc_json_fallback=None, load_now=False):
    """Function decorator for ConfigItem hierarchy for all Envs defined in 'env_factory'.

       This decorator creates a wrapped config in a object which is then used for loading the config (for all envs) and
       retrieving the configuration for a specific env. The name of the object will be the name of the wrapped function.

       The class will have two public methods, `load` and `__call__`, see `McConfigRoot` for details.

       E.g.::

           @mc_config(envf)
           def conf(root):
               with someitem() as it:
                   it.setattr('aa', default=1, tst=2, prod=3)

           # Load the configuration for all envs
           conf.load()

           # Get the cfg instantiated for 'prod'
           prod_cfg = conf(prod)

       NOTE, There can only be one current config env!
       It is possible to get the config multiple times for different envs, but storing references to items in the configuration, and accessing attributes
       at a later time, will return the value from the last env specified in '__call__'.

    Arguments:
        env_factory (EnvFactory): The EnvFactory defining the envs for which we instantiate the configuration.

        mc_json_filter (func(obj, key, value)): User defined function for filtering objects in json output.
            - filter_callable is called for each key/value pair of attributes on each ConfigItem obj.
            - It must return a tuple of (key, value). If key is False, the key/value pair is removed from the json output

        mc_json_fallback (func(obj)): User defined function for handling objects not otherwise encoded in json output.
            - fallback_callable is called for objects that are not handled by the builtin encoder.
            - It must return a tuple (object, handled). If handled is True, the object must be encodable by the standard json encoder.

        load_now (bool): Load the configuration now instead of calling `load` later. Note: this is only for simple cases, to get more control use `load`.
    """

    if not isinstance(env_factory, EnvFactory):
        msg = "'env_factory' arg must be instance of {ef_typ!r}; found type {got_typ!r}: {val!r}"
        raise ConfigException(msg.format(ef_typ=EnvFactory.__name__, got_typ=env_factory.__class__.__name__, val=env_factory))

    for _ in env_factory.envs:
        # There is at least one env
        break
    else:
        raise ConfigException("The specified 'env_factory' is empty. It must have at least one Env.")

    def deco(conf_func):
        conf = McConfigRoot(mc_json_filter, mc_json_fallback, env_factory, conf_func)
        if load_now:
            conf.load()
        return conf

    return deco

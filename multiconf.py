# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import abc
import os
from collections import Sequence, OrderedDict
import json

from .envs import BaseEnv, Env, EnvGroup
from .attribute_collector import AttributeCollector
from .config_errors import ConfigBaseException, ConfigException, NoAttributeException, _error_msg, _user_file_line
import json_output

_debug_exc = str(os.environ.get('MULTICONF_DEBUG_EXCEPTIONS')).lower() == 'true'


class ConfigApiException(ConfigBaseException):
    pass


def error(num_errors, message, up_level, error_type='MultiConfApiError'):
    return _error_msg(num_errors, message, up_level, error_type)


class _ConfigBase(object):
    _nested = []

    # Decoration attributes
    _deco_named_as = None
    _deco_repeatable = False
    _deco_nested_repeatables = []
    _deco_required = []
    _deco_required_if = (None, ())

    def __init__(self, json_filter=None, **attr):
        self._json_filter = json_filter
        self._root_conf = None
        self._attributes = OrderedDict()
        self._frozen = False
        self._may_freeze_validate = True
        self._in_exit = False
        self._in_build = False
        self._user_validated = False        

        # Prepare collectors with default values
        for key, value in attr.iteritems():
            if key in self.__class__._deco_nested_repeatables:
                raise ConfigException(repr(key) + ' defined as default value shadows a nested-repeatable')
            AttributeCollector(key, self, default_value=value, default_user_file_line=_user_file_line())

        for key in self.__class__._deco_nested_repeatables:
            self._attributes[key] = OrderedDict()

        # Builders are only inserted here so that they can be frozen
        self._builders = []

    def named_as(self):
        if self.__class__._deco_named_as:
            return self.__class__._deco_named_as
        if self.__class__._deco_repeatable:
            return self.__class__.__name__ + 's'
        return self.__class__.__name__

    # def irepr(self, indent_level):
    #     """Indented repr"""
    #     indent1 = '  ' * indent_level
    #     indent2 =  indent1 + '     '
    #     # + ':' + self.__class__.__name__
    #     not_frozen_msg = "" if self._frozen else " not-frozen"
    #     return self.named_as() + not_frozen_msg + ' {\n' + \
    #         ''.join([indent2 + name + ': ' + repr(value) + ',\n' for name, value in self.iteritems()]) + \
    #         indent1 + '}'

    def __repr__(self):
        # Don't call property methods i repr, it is too dangerous, leading to double errors in case of incorrect user implemented property methods
        return self.json(compact=True, property_methods=False)
        # TODO proper pythonic repr, but until indentation is fixed, json is better
        # return self.irepr(len(self.__class__._nested) -1)

    def json(self, compact=False, property_methods=True, skipkeys=True):
        filter_callable = self.json_filter_callable()
        class Encoder(json_output.ConfigItemEncoder):
            def __init__(self, **kwargs):
                super(Encoder, self).__init__(filter_callable=filter_callable, compact=compact, property_methods=property_methods, **kwargs)

        return json.dumps(self, skipkeys=skipkeys, cls=Encoder, check_circular=False, sort_keys=False, indent=4)

    def __enter__(self):
        assert not self._frozen
        self._may_freeze_validate = False
        self.__class__._nested.append(self)
        return self

    def freeze_validate_required(self):
        missing = []
        for req in self.__class__._deco_required:
            if not req in self._attributes:
                missing.append(req)
        if missing:
            raise ConfigException("No value given for required attributes: " + repr(missing))

    def freeze_validate_required_if(self):
        required_if_key = self.__class__._deco_required_if[0]
        if not required_if_key:
            return

        try:
            required_if = self._attributes[required_if_key].value()
            if not required_if:
                return
        except KeyError:
            return
        except NoAttributeException:
            return

        missing = []
        for req in self.__class__._deco_required_if[1]:
            if not req in self._attributes:
                missing.append(req)
        if missing:
            raise ConfigException("Missing required_if attributes. Condition attribute: " + repr(required_if_key) + "==" +  repr(required_if) + ", missing: " + repr(missing))

    def freeze_validation(self):
        """Override this method if you need special checks"""
        self.freeze_validate_required()
        self.freeze_validate_required_if()

    def freeze(self):
        """
        Recursively freeze contained items bottom up.
        If self is ready to be validated (exit from with_statement or not declared in a with_statement),
        then self will be frozen and validated
        """
        for _child_name, child_value in self._attributes.iteritems():
            if isinstance(child_value, OrderedDict):
                for item in child_value.itervalues():
                    if not item._frozen:
                        item.freeze()
                continue

            if not child_value._frozen:
                child_value.freeze()

        for builder in self._builders:
            if not builder._frozen:
                builder.freeze()

        if not self._may_freeze_validate:
            return self

        # Freeze item
        self._frozen = True
        try:
            self.freeze_validation()
            return self
        except ConfigBaseException as ex:
            if _debug_exc:
                raise
            # Strip stack
            raise ex

    @property
    def frozen(self):
        """Return frozen state"""
        return self._frozen

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._may_freeze_validate = True
            self._in_exit = True
            self.freeze()
            self.__class__._nested.pop()
            self._in_exit = False
        except Exception as ex:
            if not exc_type:
                if _debug_exc and isinstance(ex, ConfigBaseException):
                    # Strip stack for ConfigBaseException
                    raise ex
                raise ex

            print >> sys.stderr, "Exception in __exit__:", repr(ex)
            print >> sys.stderr, "Exception in with block will be raised"

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__
            super(_ConfigBase, self).__setattr__(name, value)
            return
        raise ConfigException("Trying to set a property " + repr(name) + " on a config item")

    def _check_valid_env(self, env, valid_envs):
        if not isinstance(env, Env):
            raise ConfigException(self.__class__.__name__ + ': env must be instance of ' + repr(Env.__name__) + '; found type ' + repr(env.__class__.__name__) + ': ' + repr(env))

        for valid_env in valid_envs:
            if env in valid_env:
                return
        raise ConfigException("The env " + repr(env) + " must be in the (nested) list of valid_envs " + repr(valid_envs))

    def _env_specific_value(self, attr_name, attr_coll, env):
        if isinstance(attr_coll, ConfigItem) or isinstance(attr_coll, OrderedDict):
            return attr_coll

        try:
            return attr_coll.env_values[env][0]
        except KeyError:
            self._check_valid_env(env, self.valid_envs)
            raise NoAttributeException("Attribute " + repr(attr_name) + " undefined for env " + repr(env))

    def getattr_env(self, name, env):
        try:
            attr_coll = self._attributes[name]
        except KeyError:
            error_message = ""
            repeatable_name = name + 's'
            if self._attributes.get(repeatable_name):
                error_message = ", but found attribute " + repr(repeatable_name)
            raise ConfigException(repr(self) + " has no attribute " + repr(name) + error_message)

        return self._env_specific_value(name, attr_coll, env)

    def __getattr__(self, name):
        if name.startswith('__'):
            super(_ConfigBase, self).__getattr__(name)

        if name.startswith('_'):
            ex_msg = "An error was detected trying to get attribute " + repr(name) + " on class " + repr(self.__class__.__name__)
            msg  = "\n    - Attributes starting with '_' are reserved for internal MultiConf usage. You probably tried to use the"
            msg += "\n      MultiConf API in a derived class __init__ before calling the parent class __init__"
            error(1, ex_msg + msg, 4)
            raise ConfigApiException(ex_msg)

        try:
            # Return existing collector/(dict of)nested item(s) if any
            coll = self._attributes[name]
            if isinstance(coll, (ConfigItem, OrderedDict)):
                return coll
            assert isinstance(coll, AttributeCollector), "Expected AttributeCollector, got: " + repr(type(coll))
            if not coll._frozen:
                return coll
        except KeyError:
            if not self._frozen:
                return AttributeCollector(name, self, default_value=None, default_user_file_line=None)

        try:
            return self.getattr_env(name, self.env)
        except ConfigException as ex:
            if _debug_exc:
                raise
            raise ex

    def iteritems(self):
        for key, value in self._attributes.iteritems():
            try:
                yield key, self._env_specific_value(key, value, self.env)
            except NoAttributeException:
                # This should only happen in case of  a conditional attribute
                pass

    @property
    def contained_in(self):
        return self._contained_in

    @property
    def root_conf(self):
        return self._root_conf

    @property
    def attributes(self):
        return self._attributes

    @property
    def env(self):
        return self._root_conf._selected_env

    @property
    def valid_envs(self):
        return self._root_conf.valid_envs

    def json_filter_callable(self):
        contained_in = self
        while contained_in:
            if contained_in._json_filter:
                return contained_in._json_filter
            contained_in = contained_in.contained_in
        return None

    def find_contained_in(self, named_as):
        """Find first parent container named as 'named_as', by searching backwards towards root_conf, starting with parent container"""
        contained_in = self.contained_in
        while contained_in:
            if contained_in.named_as() == named_as:
                return contained_in
            contained_in = contained_in.contained_in

        # Error, create error message
        contained_in = self.contained_in
        contained_in_names = []
        while contained_in:
            contained_in_names.append(contained_in.named_as())
            contained_in = contained_in.contained_in

        raise ConfigException('Could not find a parent container named as: ' + repr(named_as) + ' in hieracy with names: ' + repr(contained_in_names))

    def find_attribute(self, attribute_name):
        """Find first occurence of attribute 'attribute_name', by searching backwards towards root_conf, starting with self."""
        contained_in = self
        while contained_in:
            attr_coll = contained_in.attributes.get(attribute_name)
            if attr_coll:
                return contained_in.__getattr__(attribute_name)
            contained_in = contained_in.contained_in

        # Error, create error message
        contained_in = self
        contained_in_names = []
        while contained_in:
            contained_in_names.append(contained_in.named_as())
            contained_in = contained_in.contained_in

        raise ConfigException('Could not find an attribute named: ' + repr(attribute_name) + ' in hieracy with names: ' + repr(contained_in_names))

    def _user_validate_recursively(self):
        """Call the user defined 'validate' methods on all items"""
        if self._user_validated:
            return

        self.validate()
        self._user_validated = True

        for _child_name, child_value in self.iteritems():
            if isinstance(child_value, OrderedDict):
                for dict_entry in child_value.values():
                    if isinstance(dict_entry, _ConfigBase):
                        dict_entry._user_validate_recursively()

            if isinstance(child_value, _ConfigBase):
                child_value._user_validate_recursively()

    def validate(self):
        """Can be overridden to provide post-frozen validation"""
        pass


class ConfigRoot(_ConfigBase):
    def __init__(self, selected_env, valid_envs, json_filter=None, **attr):
        if not isinstance(valid_envs, Sequence) or isinstance(valid_envs, str):
            raise ConfigException(self.__class__.__name__ + ": valid_envs arg must be a 'Sequence'; found type " + repr(valid_envs.__class__.__name__) + ': ' + repr(valid_envs))

        for env in valid_envs:
            if not isinstance(env, BaseEnv):
                raise ConfigException(self.__class__.__name__ + ": valid_envs items must be instance of " + repr(Env.__name__) + " or " + repr(EnvGroup.__name__) + "; found a " + repr(env.__class__.__name__) + ': ' + repr(env))

        self._check_valid_env(selected_env, valid_envs)

        del self.__class__._nested[:]

        self._selected_env = selected_env
        self._valid_envs = valid_envs
        super(ConfigRoot, self).__init__(json_filter=json_filter, **attr)
        self._root_conf = self
        self._contained_in = None
        self._nesting_level = 0

    def __exit__(self, exc_type, exc_value, traceback):
        super(ConfigRoot, self).__exit__(exc_type, exc_value, traceback)
        try:
            self._user_validate_recursively()
        except Exception as ex:
            if not exc_type:
                raise
            print >> sys.stderr, "Exception in validate:", ex
            print >> sys.stderr, "Exception in with block will be raised"


    @property
    def valid_envs(self):
        return self._valid_envs


class _ContainedConfigBase(_ConfigBase):
    def __init__(self, json_filter=None, **attr):
        super(_ContainedConfigBase, self).__init__(json_filter=json_filter, **attr)

        if not self.__class__._nested:
            raise ConfigException(self.__class__.__name__ + " object must be nested (indirectly) in a " + repr(ConfigRoot.__name__))
        self._nesting_level = len(self.__class__._nested)

        # Set back reference to containing Item and root item
        self._contained_in = self.__class__._nested[-1]
        self._root_conf = self._contained_in.root_conf

        # Freeze attributes on parent-container and previously defined siblings
        try:
            self._contained_in.freeze()
        except ConfigBaseException as ex:
            if _debug_exc:
                raise
            raise ex


class ConfigItem(_ContainedConfigBase):
    def __init__(self, json_filter=None, **attr):
        super(ConfigItem, self).__init__(json_filter=json_filter, **attr)

        # Automatic Nested Insert in parent, insert self in containing Item's attributes
        my_key = self.named_as()

        if self.__class__._deco_repeatable:
            # Validate that the containing item has specified this item as repeatable
            if not my_key in self._contained_in.__class__._deco_nested_repeatables:
                msg = repr(my_key) + ': ' + repr(self) + ' is defined as repeatable, but this is not defined as a repeatable item in the containing class: ' + \
                    repr(self._contained_in.named_as())
                raise ConfigException(msg)
                # TODO?: type check of list items (isinstance(ConfigItem). Same type?

            # Insert in Ordered dict by 'id' or 'name', 'id' is preferred if given
            try:
                try:
                    obj_key = self._attributes['id']
                except KeyError:
                    obj_key = self._attributes['name']
                if not obj_key._has_default():
                    raise KeyError()
                obj_key = obj_key._default_value()[0]

                # Check that we are not replacing an object with the same id/name
                if self._contained_in.attributes[my_key].get(obj_key):
                    raise ConfigException("Re-used id/name " + repr(obj_key) + " in nested objects")
            except KeyError:
                obj_key = id(self)

            self._contained_in.attributes[my_key][obj_key] = self
            return

        if my_key in self._contained_in.attributes:
            if isinstance(self._contained_in.attributes[my_key], ConfigItem):
                raise ConfigException("Repeated non repeatable conf item: " + repr(my_key))
            if isinstance(self._contained_in.attributes[my_key], OrderedDict):
                msg = repr(my_key) + ': ' + repr(self) + ' is defined as non-repeatable, but the containing object has repeatable items with the same name: ' + \
                    repr(self._contained_in)
                raise ConfigException(msg)
            raise ConfigException(repr(my_key) + ' is defined both as simple value and a contained item: ' + repr(self))

        self._contained_in.attributes[my_key] = self


class ConfigBuilder(_ContainedConfigBase):
    # Decoration attributes
    _deco_override = []

    def __init__(self, json_filter=None, **attr):
        super(ConfigBuilder, self).__init__(json_filter=json_filter, **attr)
        self._override_keys = attr.keys()

        # Append self to containing Item's builders list so that parent can freeze us
        self._contained_in._builders.append(self)
        self._freezing = False

    def freeze(self):
        if self._freezing:
            return
        self._freezing = True

        super(ConfigBuilder, self).freeze()
        if self._may_freeze_validate:
            # The items we are building goes into the parent object, not the builder!
            if self._in_exit:
                self.__class__._nested.pop()
            try:
                self._in_build = True
                self.build()
            finally:
                self._in_build = False
                if self._in_exit:
                    self.__class__._nested.append(self)
        self._freezing = False
        return self

    @abc.abstractmethod
    def build(self):
        """Override this in derived classes. This is where child ConfigItems are declared"""
        raise Exception("AbstractNotImplemented")

    def override(self, config_item, *keys):
        """Assign attributes that that match 'override' decorator keys or 'keys' from builder to child Item"""
        for key in self.__class__._deco_override + list(keys):
            value = self.attributes.get(key)
            if value:
                config_item_attr = config_item.attributes.get(key)
                if config_item_attr:
                    config_item_attr.override(value)
                    continue
                config_item.attributes[key] = value



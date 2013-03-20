# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import abc
import os
from collections import Sequence, OrderedDict
import json

from .envs import BaseEnv, Env, EnvGroup, EnvException
from .attribute import Attribute
from .repeatable import Repeatable
from .config_errors import ConfigBaseException, ConfigException, NoAttributeException, _api_error_msg, _user_file_line
import json_output

_debug_exc = str(os.environ.get('MULTICONF_DEBUG_EXCEPTIONS')).lower() == 'true'


class ConfigApiException(ConfigBaseException):
    pass

class _ConfigBase(object):
    _mc_nested = []

    # Decoration attributes
    _mc_deco_named_as = None
    _mc_deco_repeatable = False
    _mc_deco_nested_repeatables = []
    _mc_deco_required = []
    _mc_deco_required_if = (None, ())

    def __init__(self, json_filter=None, **attr):
        self._mc_json_filter = json_filter
        self._mc_root_conf = None
        self._mc_attributes = Repeatable()
        self._mc_frozen = False
        self._mc_may_freeze_validate = True
        self._mc_in_build = False
        self._mc_user_validated = False
        self._mc_in_init = True

        # Prepare collectors with default values
        for key, value in attr.iteritems():
            if key in self.__class__._mc_deco_nested_repeatables:
                raise ConfigException(repr(key) + ' defined as default value shadows a nested-repeatable')
            attribute = Attribute(key)
            attribute.env_values['__init__'] = (value, _user_file_line())
            self._mc_attributes[key] = attribute

        for key in self.__class__._mc_deco_nested_repeatables:
            self._mc_attributes[key] = Repeatable()

    def named_as(self):
        if self.__class__._mc_deco_named_as:
            return self.__class__._mc_deco_named_as
        if self.__class__._mc_deco_repeatable:
            return self.__class__.__name__ + 's'
        return self.__class__.__name__

    # def irepr(self, indent_level):
    #     """Indented repr"""
    #     indent1 = '  ' * indent_level
    #     indent2 =  indent1 + '     '
    #     # + ':' + self.__class__.__name__
    #     not_frozen_msg = "" if self._mc_frozen else " not-frozen"
    #     return self.named_as() + not_frozen_msg + ' {\n' + \
    #         ''.join([indent2 + name + ': ' + repr(value) + ',\n' for name, value in self.iteritems()]) + \
    #         indent1 + '}'

    def __repr__(self):
        # Don't call property methods i repr, it is too dangerous, leading to double errors in case of incorrect user implemented property methods
        return self.json(compact=True, property_methods=False)
        # TODO proper pythonic repr, but until indentation is fixed, json is better
        # return self.irepr(len(self.__class__._mc_nested) -1)

    def json(self, compact=False, property_methods=True, skipkeys=True):
        filter_callable = self.json_filter_callable()
        class Encoder(json_output.ConfigItemEncoder):
            def __init__(self, **kwargs):
                super(Encoder, self).__init__(filter_callable=filter_callable, compact=compact, property_methods=property_methods, **kwargs)

        return json.dumps(self, skipkeys=skipkeys, cls=Encoder, check_circular=False, sort_keys=False, indent=4)

    def __enter__(self):
        assert not self._mc_frozen
        self._mc_may_freeze_validate = False
        self._mc_in_init = False
        self.__class__._mc_nested.append(self)
        return self

    def freeze_validate_required(self):
        missing = []
        for req in self.__class__._mc_deco_required:
            if not req in self._mc_attributes:
                missing.append(req)
        if missing:
            raise ConfigException("No value given for required attributes: " + repr(missing))

    def freeze_validate_required_if(self):
        required_if_key = self.__class__._mc_deco_required_if[0]
        if not required_if_key:
            return

        try:
            required_if_condition_attr = self._mc_attributes[required_if_key]
            if not required_if_condition_attr:
                return
        except KeyError:
            return

        missing = []
        for req in self.__class__._mc_deco_required_if[1]:
            if not req in self._mc_attributes:
                try:
                    required_if_condition = required_if_condition_attr.value(self.env)
                except NoAttributeException:
                    continue
                if required_if_condition:
                    missing.append(req)
            else:
                attr = self._mc_attributes[req]
                if isinstance(attr, Attribute):
                    # Avoid double errors
                    if not attr.num_errors:
                        self.check_attr_fully_defined(attr)
        if missing:
            raise ConfigException("Missing required_if attributes. Condition attribute: " + repr(required_if_key) + " == " + repr(required_if_condition) + ", missing attributes: " + repr(missing))

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
        for _child_name, child_value in self._mc_attributes.iteritems():
            if not child_value._mc_frozen:
                child_value.freeze()

        if not self._mc_may_freeze_validate:
            return self

        # Freeze item
        self._mc_frozen = True
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
        return self._mc_frozen

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._mc_may_freeze_validate = True
            self.freeze()
        except Exception as ex:
            if not exc_type:
                if _debug_exc:
                    raise
                raise ex

            print >> sys.stderr, "Exception in __exit__:", repr(ex)
            print >> sys.stderr, "Exception in with block will be raised"
        finally:
            self.__class__._mc_nested.pop()

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__
            super(_ConfigBase, self).__setattr__(name, value)
            return
        self.setattr(name, default=value)

    def setattr(self, name, **kwargs):
        if name.startswith('_mc'):
            raise ConfigException("Trying to set attribute " + repr(name) + " on a config item. " + 
                                  "Atributes starting with '_mc' are reserved for multiconf internal usage.")

        # For error messages
        ufl = _user_file_line()
        eg_from = {}

        attribute = self._mc_attributes.setdefault(name, Attribute(name))
        if attribute._mc_frozen:
            msg = "The attribute " + repr(name) + " is already fully defined"
            attribute.error(msg)
            raise ConfigException(msg + " on object " + repr(self))

        if not self._mc_in_init and not ('default' in kwargs and len(kwargs) == 1):
            attribute._mc_frozen = True

        # Validate and assign given env values
        for eg_name, value in kwargs.iteritems():
            v_ufl = (value, ufl)
            try:
                attribute.validate_types(eg_name, v_ufl)

                if eg_name == 'default':
                    attribute.env_values['default'] = v_ufl
                    continue

                eg = self.env.factory.env_or_group(eg_name)
                for env in eg.envs():
                    # If env == eg then this is a direct env specification, allow overwriting value previously specified through a group
                    if env not in attribute.env_values or (isinstance(eg_from[env], EnvGroup) and (env == eg)):
                        attribute.env_values[env] = v_ufl
                        eg_from[env] = eg
                        continue

                    # If env != eg then this is specified through a group, if it was previously specified directly, just ignore
                    if (not isinstance(eg_from[env], EnvGroup)) and (env != eg):
                        continue

                    new_eg_msg = repr(env) + ("" if env == eg else " from group " + repr(eg))
                    prev_eg_msg = repr(eg_from[env])
                    msg = "A value is already specified for: " + new_eg_msg + '=' + repr(v_ufl) + ", previous value: " + prev_eg_msg + '=' + repr(attribute.env_values[env])
                    attribute.error(msg)

            except EnvException as ex:
                attribute.error(ex.message)

        self.check_attr_fully_defined(attribute)

    def check_attr_fully_defined(self, attribute):
        name = attribute.attribute_name

        if not attribute.has_default():
            # Check whether we need to check for conditionally required attributes
            required_if_key = self.__class__._mc_deco_required_if[0]
            if required_if_key:
                # A required_if CONDITION attribute is optional, so it is ok if it is not set or not set for all environments
                if name == required_if_key:
                    return

                try:
                    required_if_condition_attr = self.attributes[required_if_key]
                    required_if_attribute_names = self.__class__._mc_deco_required_if[1]
                except KeyError:
                    # The condition property was not specified, so the conditional properties are not required
                    required_if_key = False

            # Validate that the attribute is defined for all envs
            attribute.all_envs_initialized = True
            for eg in self.root_conf._mc_valid_envs:
                for env in eg.envs():
                    if env in attribute.env_values:
                        # The attribute is set with an env specific value
                        continue

                    # Check for required_if, the required_if atributes are optional if required_if_condition value is false or not specified for the env
                    try:
                        if required_if_key and not required_if_condition_attr.value(env) and name in required_if_attribute_names:
                            continue
                    except NoAttributeException:
                        continue

                    attribute.all_envs_initialized = False
                    group_msg = ", which is a member of " + repr(eg) if isinstance(eg, EnvGroup) else ""
                    msg = "Attribute: " + repr(name) + " did not receive a value for env " + repr(env)
                    attribute.error(msg + group_msg)

                    # ci = container
                    # while ci != None:
                    #     print ci._nesting_level, ci._mc_in_build
                    #     ci = ci._mc_contained_in
                    #
                    # if not container.contained_in._mc_in_build:
                    #     attribute.num_errors = error(attribute.num_errors, msg + group_msg)
                    # else:
                    #     warning(msg + group_msg)

        if attribute.num_errors:
            raise ConfigException("There were " + repr(attribute.num_errors) + " errors when defining attribute " + repr(name) + " on object: " + repr(self))

    def _check_valid_env(self, env, valid_envs):
        if not isinstance(env, Env):
            raise ConfigException(self.__class__.__name__ + ': env must be instance of ' + repr(Env.__name__) + '; found type ' + repr(env.__class__.__name__) + ': ' + repr(env))

        for valid_env in valid_envs:
            if env in valid_env:
                return
        raise ConfigException("The env " + repr(env) + " must be in the (nested) list of valid_envs " + repr(valid_envs))

    def __getattr__(self, name):
        if name.startswith('__'):
            super(_ConfigBase, self).__getattr__(name)

        if name.startswith('_mc'):
            ex_msg = "An error was detected trying to get attribute " + repr(name) + " on class " + repr(self.__class__.__name__)
            msg  = "\n    - Attributes starting with '_mc' are reserved for internal MultiConf usage. You probably tried to use the"
            msg += "\n      MultiConf API in a derived class __init__ before calling the parent class __init__"
            _api_error_msg(1, ex_msg + msg)
            raise ConfigApiException(ex_msg)

        try:
            attr = self._mc_attributes[name]
        except KeyError:
            error_message = ""
            repeatable_name = name + 's'
            if self._mc_attributes.get(repeatable_name):
                error_message = ", but found attribute " + repr(repeatable_name)
            raise AttributeError(repr(self) + " has no attribute " + repr(name) + error_message)

        try:
            return attr.value(self.env)
        except NoAttributeException as ex:
            raise AttributeError(ex.message)

    def iteritems(self):
        for key, item in self._mc_attributes.iteritems():
            try:
                yield key, item.value(self.env)
            except NoAttributeException:
                # This should only happen in case of  a conditional attribute
                pass

    @property
    def contained_in(self):
        contained_in = self._mc_contained_in
        while 1:
            if not isinstance(contained_in, ConfigBuilder):                
                return contained_in
            contained_in = contained_in._mc_contained_in

    @property
    def root_conf(self):
        return self._mc_root_conf

    @property
    def attributes(self):
        return self._mc_attributes

    @property
    def env(self):
        return self._mc_root_conf._mc_selected_env

    @property
    def valid_envs(self):
        return self._mc_root_conf.valid_envs

    def json_filter_callable(self):
        contained_in = self
        while contained_in:
            if contained_in._mc_json_filter:
                return contained_in._mc_json_filter
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
            attr = contained_in.attributes.get(attribute_name)
            if attr:
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
        if self._mc_user_validated:
            return

        self.validate()
        self._mc_user_validated = True

        for child_value in self._mc_attributes.values():
            child_value._user_validate_recursively()

    def validate(self):
        """Can be overridden to provide post-frozen validation"""
        pass

    def value(self, env):
        return self


class ConfigRoot(_ConfigBase):
    def __init__(self, selected_env, valid_envs, json_filter=None, **attr):
        if not isinstance(valid_envs, Sequence) or isinstance(valid_envs, str):
            raise ConfigException(self.__class__.__name__ + ": valid_envs arg must be a 'Sequence'; found type " + repr(valid_envs.__class__.__name__) + ': ' + repr(valid_envs))

        for env in valid_envs:
            if not isinstance(env, BaseEnv):
                raise ConfigException(self.__class__.__name__ + ": valid_envs items must be instance of " + repr(Env.__name__) + " or " + repr(EnvGroup.__name__) + "; found a " + repr(env.__class__.__name__) + ': ' + repr(env))

        self._check_valid_env(selected_env, valid_envs)

        del self.__class__._mc_nested[:]

        self._mc_selected_env = selected_env
        self._mc_valid_envs = valid_envs
        super(ConfigRoot, self).__init__(json_filter=json_filter, **attr)
        self._mc_root_conf = self
        self._mc_contained_in = None
        self._mc_nesting_level = 0

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
        return self._mc_valid_envs


class ConfigItem(_ConfigBase):
    def __init__(self, json_filter=None, **attr):
        super(ConfigItem, self).__init__(json_filter=json_filter, **attr)

        if not self.__class__._mc_nested:
            raise ConfigException(self.__class__.__name__ + " object must be nested (indirectly) in a " + repr(ConfigRoot.__name__))
        self._mc_nesting_level = len(self.__class__._mc_nested)

        # Set back reference to containing Item and root item
        self._mc_contained_in = self.__class__._mc_nested[-1]
        self._mc_root_conf = self._mc_contained_in.root_conf

        # Freeze attributes on parent-container and previously defined siblings
        try:
            self._mc_contained_in.freeze()
        except ConfigBaseException as ex:
            if _debug_exc:
                raise
            raise ex

        # Automatic Nested Insert in parent, insert self in containing Item's attributes
        my_key = self.named_as()

        if self.__class__._mc_deco_repeatable:
            # Validate that the containing item has specified this item as repeatable
            if not my_key in self._mc_contained_in.__class__._mc_deco_nested_repeatables:
                if isinstance(self._mc_contained_in, ConfigBuilder):
                    # Builders don't declare nested repeatables, since the items are ultimately to be assigned to the built items
                    if not my_key in self._mc_contained_in.attributes:
                        self._mc_contained_in.attributes[my_key] = Repeatable()
                else:
                    msg = repr(my_key) + ': ' + repr(self) + ' is defined as repeatable, but this is not defined as a repeatable item in the containing class: ' + \
                        repr(self._mc_contained_in.named_as())
                    raise ConfigException(msg)
                    # TODO?: type check of list items (isinstance(ConfigItem). Same type?

            # Insert in Ordered dict by 'id' or 'name', 'id' is preferred if given
            try:
                try:
                    obj_key = self._mc_attributes['id']
                except KeyError:
                    obj_key = self._mc_attributes['name']
                if not obj_key.has_default():
                    raise KeyError()
                obj_key = obj_key.default_value()[0]

                # Check that we are not replacing an object with the same id/name
                if self._mc_contained_in.attributes[my_key].get(obj_key):
                    raise ConfigException("Re-used id/name " + repr(obj_key) + " in nested objects")
            except KeyError:
                obj_key = id(self)

            self._mc_contained_in.attributes[my_key][obj_key] = self
            return

        if my_key in self._mc_contained_in.attributes:
            if isinstance(self._mc_contained_in.attributes[my_key], ConfigItem):
                raise ConfigException("Repeated non repeatable conf item: " + repr(my_key))
            if isinstance(self._mc_contained_in.attributes[my_key], Repeatable):
                msg = repr(my_key) + ': ' + repr(self) + ' is defined as non-repeatable, but the containing object has repeatable items with the same name: ' + \
                    repr(self._mc_contained_in)
                raise ConfigException(msg)
            raise ConfigException(repr(my_key) + ' is defined both as simple value and a contained item: ' + repr(self))

        self._mc_contained_in.attributes[my_key] = self


class ConfigBuilder(ConfigItem):
    def __init__(self, json_filter=None, **attr):
        super(ConfigBuilder, self).__init__(json_filter=json_filter, **attr)
        self._mc_what_built = OrderedDict()
        self._mc_freezing = False

    def freeze(self):
        if self._mc_freezing:
            return
        self._mc_freezing = True

        def override(item, attributes):
            if isinstance(item, ConfigItem):
                for override_key, override_value in attributes.iteritems():
                    item._mc_attributes[override_key] = override_value

        super(ConfigBuilder, self).freeze()
        if self._mc_may_freeze_validate:
            existing_attributes = self._mc_attributes.copy()

            # We need to allow the same nested repeatables as the parent item
            for key in self.contained_in.__class__._mc_deco_nested_repeatables:
                self._mc_attributes[key] = Repeatable()

            self._mc_in_build = True
            self.build()
            self._mc_in_build = False

            # Attributes/Items on builder are copied to items created in build
            # Loop over attributes created in build
            for build_key, build_value in self._mc_attributes.iteritems():
                if build_key in existing_attributes:
                    continue
                self._mc_what_built[build_key] = build_value.value(self.env)

                if isinstance(build_value, Repeatable):
                    for key, value in build_value.iteritems():
                        override(value, existing_attributes)
                    continue

                override(build_value, existing_attributes)

            # Items and attributes created in 'build' goes into parent
            for key, value in self._mc_attributes.iteritems():
                if key in existing_attributes:
                    continue

                # Merge repeatable items in to parent
                if isinstance(value, Repeatable):
                    for obj_key, ovalue in value.iteritems():
                        if obj_key in self.contained_in.attributes[key]:
                            raise ConfigException("Nested repeatable from 'build', key: " + repr(obj_key) + ", value: " + repr(ovalue) +
                                                  " overwrites existing entry in parent: " + repr(self._mc_contained_in))
                        self.contained_in.attributes[key][obj_key] = ovalue
                    continue

                # TODO validation
                self._mc_contained_in.attributes[key] = value
        self._mc_freezing = False
        return self

    @abc.abstractmethod
    def build(self):
        """Override this in derived classes. This is where child ConfigItems are declared"""
        raise Exception("AbstractNotImplemented")

    def what_built(self):
        return self._mc_what_built

    def named_as(self):
        return super(ConfigBuilder, self).named_as() + '.builder.' + repr(id(self))

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, abc, os, copy
from collections import Sequence, OrderedDict
import json

from .envs import BaseEnv, Env, EnvGroup, EnvException
from .attribute import Attribute
from .repeatable import Repeatable
from .excluded import Excluded
from .config_errors import ConfigBaseException, ConfigException, ConfigApiException, NoAttributeException, _api_error_msg, _user_file_line
from . import json_output

_debug_exc = str(os.environ.get('MULTICONF_DEBUG_EXCEPTIONS')).lower() == 'true'
_warn_json_nesting = str(os.environ.get('MULTICONF_WARN_JSON_NESTING')).lower() == 'true'


class _ConfigBase(object):
    _mc_nested = []

    # Decoration attributes
    _mc_deco_named_as = None
    _mc_deco_repeatable = False
    _mc_deco_nested_repeatables = []
    _mc_deco_required = []
    _mc_deco_required_if = (None, ())
    _mc_deco_unchecked = None

    def __init__(self, mc_json_filter=None, mc_json_fallback=None, **attr):
        self._mc_json_filter = mc_json_filter
        self._mc_json_fallback = mc_json_fallback
        self._mc_root_conf = None
        self._mc_attributes = Repeatable()
        self._mc_build_attributes = Repeatable()
        self._mc_frozen = False
        self._mc_built = False
        self._mc_in_init = True
        self._mc_in_build = False
        self._mc_user_validated = False
        self._mc_previous_child = None
        self._mc_is_excluded = False
        self._mc_include_in_envs = None # Means 'all'
        self._mc_exclude_from_envs = []
        self._mc_override = False

        # Prepare attributes with default values
        for key, value in attr.iteritems():
            if key in self.__class__._mc_deco_nested_repeatables:
                raise ConfigException(repr(key) + ' defined as default value shadows a nested-repeatable')
            attribute = Attribute(key)
            attribute.env_values['__init__'] = (value, _user_file_line())
            self._mc_attributes[key] = attribute

        for key in self.__class__._mc_deco_nested_repeatables:
            self._mc_attributes[key] = Repeatable()

    def named_as(self):
        """Return the named_as property set by the @named_as decorator"""
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
        # Don't call property methods in repr, it is too dangerous, leading to double errors in case of incorrect user implemented property methods
        return self.json(compact=True, property_methods=False, builders=True)
        # TODO proper pythonic repr, but until indentation is fixed, json is better
        # return self.irepr(len(self.__class__._mc_nested) -1)

    def _mc_freeze_previous_child(self):
        # Freeze attributes on previously defined child
        previous_item = self._mc_previous_child
        if previous_item and not previous_item.frozen:
            try:
                return previous_item._mc_freeze()
            except Exception as ex:
                print("Exception validating previously defined object -", file=sys.stderr)
                print("  type:", type(previous_item), file=sys.stderr)
                print("Stack trace will be misleading!", file=sys.stderr)
                print("This happens if there is an error (e.g. missing required attributes) in an object that was not", file=sys.stderr)
                print("directly enclosed in a with statement. Objects that are not arguments to a with statement will", file=sys.stderr)
                print("not be validated until the next ConfigItem is declared or an outer with statement is exited.", file=sys.stderr)

                if hasattr(ex, '_mc_in_user_code') or _debug_exc:
                    raise
                raise ex

    def _mc_insert_item(self, child_item):
        self._mc_freeze_previous_child()
        if not child_item._mc_is_excluded:
            self._mc_previous_child = child_item

        # Insert child_item in attributes
        child_key = child_item.named_as()
        attributes = self._mc_build_attributes if self._mc_in_build else self._mc_attributes

        if child_item.__class__._mc_deco_repeatable:
            # Repeatable excluded items are simply excluded
            if child_item._mc_is_excluded:
                return

            # Validate that this class specifies item as repeatable
            if isinstance(self, ConfigBuilder):
                attributes.setdefault(child_key, Repeatable())
            elif not child_key in self.__class__._mc_deco_nested_repeatables:
                raise ConfigException(child_item._error_msg_not_repeatable_in_container(child_key, self))
            elif self._mc_in_build:
                attributes.setdefault(child_key, Repeatable())

            # Calculate key to use when inserting repeatable item in Repeatable dict
            # Key is calculated as 'obj.id', 'obj.name' or id(obj) in that preferred order
            try:
                try:
                    obj_key = child_item._mc_attributes['id']
                except KeyError:
                    obj_key = child_item._mc_attributes['name']
                obj_key = obj_key.default_value()[0]

                # Check that we are not replacing an object with the same id/name
                if attributes[child_key].get(obj_key):
                    raise ConfigException("Re-used id/name " + repr(obj_key) + " in nested objects")
            except KeyError:
                obj_key = id(child_item)

            attributes[child_key][obj_key] = child_item
            return

        if child_key in attributes:
            if isinstance(attributes[child_key], ConfigItem):
                raise ConfigException("Repeated non repeatable conf item: " + repr(child_key))
            if isinstance(attributes[child_key], Repeatable):
                msg = repr(child_key) + ': ' + repr(child_item) + \
                    ' is defined as non-repeatable, but the containing object has repeatable items with the same name: ' + repr(self)
                raise ConfigException(msg)
            raise ConfigException(repr(child_key) + ' is defined both as simple value and a contained item: ' + repr(child_item))

        if not child_item._mc_is_excluded:
            attributes[child_key] = child_item
            return

        # In case of a Non-Repeatable excluded item we insert an Excluded object which is always False
        # This makes it possible to do 'if x.item: ...' instead of hasattr(x, 'item') and allows for a nicer json dump
        attributes[child_key] = Excluded(child_item)

    def _mc_post_init_update(self):
        # Merge items from build into items from with block
        for child_key, child_item in self._mc_build_attributes.iteritems():
            if isinstance(child_item, Repeatable):
                for rep_key, rep_item in child_item.iteritems():
                    if rep_item._mc_override:
                        self._mc_attributes[child_key][rep_key] = rep_item
                    else:
                        self._mc_attributes[child_key].setdefault(rep_key, rep_item)
                continue
            if child_item._mc_override:
                self._mc_attributes[child_key] = child_item
            else:
                self._mc_attributes.setdefault(child_key, child_item)

    def json(self, compact=False, property_methods=True, builders=False, skipkeys=True):
        """See json_output.ConfigItemEncoder for parameters"""
        filter_callable = self._mc_find_json_filter_callable()
        fallback_callable = self._mc_find_json_fallback_callable()
        class Encoder(json_output.ConfigItemEncoder):
            def __init__(self, **kwargs):
                super(Encoder, self).__init__(filter_callable=filter_callable, fallback_callable=fallback_callable,
                                              compact=compact, property_methods=property_methods, builders=builders,
                                              warn_nesting=_warn_json_nesting, **kwargs)

        return json.dumps(self, skipkeys=skipkeys, cls=Encoder, check_circular=False, sort_keys=False, indent=4)

    def __enter__(self):
        assert not self._mc_frozen
        self._mc_in_init = False
        self.__class__._mc_nested.append(self)
        return self

    def _mc_freeze_validation(self):
        # Validate all unfrozen attributes
        for attr in self._mc_attributes.itervalues():
            if not attr._mc_frozen and isinstance(attr, Attribute):
                self.check_attr_fully_defined(attr)

        # Validate @required
        missing = []
        for req in self.__class__._mc_deco_required:
            if not req in self._mc_attributes:
                missing.append(req)
        if missing:
            raise ConfigException("No value given for required attributes: " + repr(missing))

        # Validate @required_if
        required_if_key = self.__class__._mc_deco_required_if[0]
        if not required_if_key:
            return

        try:
            required_if_condition_attr = self._mc_attributes[required_if_key]
            try:
                required_if_condition = required_if_condition_attr._mc_value(self.env)
                if not required_if_condition:
                    return
            except NoAttributeException:
                return
        except KeyError:
            return

        missing = []
        for req in self.__class__._mc_deco_required_if[1]:
            if not req in self._mc_attributes:
                missing.append(req)
            else:
                attr = self._mc_attributes[req]
                if isinstance(attr, Attribute):
                    # Avoid double errors
                    if not attr.num_errors:
                        self.check_attr_fully_defined(attr)
        if missing:
            raise ConfigException("Missing required_if attributes. Condition attribute: " + repr(required_if_key) + " == " + repr(required_if_condition) + ", missing attributes: " + repr(missing))

    def _mc_freeze(self):
        """
        Recursively freeze contained items bottom up.
        If self is ready to be validated (exit from with_statement or not declared in a with_statement),
        then self will be frozen and validated
        """
        if self._mc_frozen or self._mc_is_excluded:
            return True

        self._mc_frozen = self._mc_deco_unchecked != self.__class__ and not self._mc_root_conf._mc_under_proxy_build
        for _child_name, child_value in self._mc_attributes.iteritems():
            self._mc_frozen &= child_value._mc_freeze()

        if not self._mc_built:
            must_pop = False
            self._mc_in_init = False
            if self._mc_nested[-1] != self:
                must_pop = True
                self._mc_nested.append(self)
            try:
                self._mc_in_build = True
                was_under_proxy_build = self._mc_root_conf._mc_under_proxy_build
                self.mc_init()
                self._mc_post_init_update()
                if isinstance(self, ConfigBuilder):
                    self._mc_root_conf._mc_under_proxy_build = True
                    self.build()
                for _name, value in self._mc_build_attributes.iteritems():
                    self._mc_frozen &= value._mc_freeze()
                if isinstance(self, ConfigBuilder):
                    self._mc_post_build_update()
                self._mc_in_build = False
            except Exception as ex:
                ex._mc_in_user_code = True
                raise
            finally:
                self._mc_root_conf._mc_under_proxy_build = was_under_proxy_build
                if must_pop:
                    self._mc_nested.pop()
                self._mc_built = True

        if self._mc_frozen:
            self._mc_freeze_validation()

        return self._mc_frozen

    @property
    def frozen(self):
        """Return frozen state"""
        return self._mc_frozen

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._mc_freeze()
        except Exception as ex:
            ex._mc_in_exit = True
            if not exc_type:
                if hasattr(ex, '_mc_in_user_code') or _debug_exc:
                    raise
                raise ex

            if not hasattr(exc_value, '_mc_in_exit') or hasattr(ex, '_mc_in_user_code'):
                print("Exception in __exit__:", repr(ex), file=sys.stderr)
                print("Exception in with block will be raised", file=sys.stderr)
        finally:
            self.__class__._mc_nested.pop()

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__
            super(_ConfigBase, self).__setattr__(name, value)
            return
        self._setattr(name, _mc_override=False, default=value)

    def _setattr(self, name, _mc_override, **kwargs):
        """Set attributes with environment specific values"""
        if name[0] == '_':
            if name.startswith('_mc'):
                raise ConfigException("Trying to set attribute " + repr(name) + " on a config item. " +
                                      "Atributes starting with '_mc' are reserved for multiconf internal usage.")

            raise ConfigException("Trying to set attribute " + repr(name) + " on a config item. " +
                                  "Atributes starting with '_' can not be set using item.setattr. Use assignment instead.")

        # For error messages
        ufl = _user_file_line()
        eg_from = {}
        local = {}

        attributes = self._mc_build_attributes if self._mc_in_build else self._mc_attributes

        if _mc_override:
            attribute = attributes[name] = Attribute(name, _mc_override=True)
        else:
            attribute = attributes.setdefault(name, Attribute(name))

        if attribute._mc_frozen:
            msg = "The attribute " + repr(name) + " is already fully defined"
            attribute.error(msg)
            raise ConfigException(msg + " on object " + repr(self))

        # If a base class is unchecked, the attribute need not be fully defined, here. The remaining envs may receive values in the base class mc_init
        check = self._mc_deco_unchecked != self.__class__ and self._mc_deco_unchecked not in self.__class__.__bases__
        if not self._mc_in_init and not ('default' in kwargs and len(kwargs) == 1) and check:
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
                    self._check_env_is_valid(env, self.valid_envs)

                    # Locally set attribute alway overwrite previously set 'unchecked'
                    if env not in local:
                        attribute.env_values[env] = v_ufl
                        local[env] = True
                        eg_from[env] = eg
                        continue

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

        if check:
            self.check_attr_fully_defined(attribute)

    def setattr(self, name, **kwargs):
        try:
            self._setattr(name, _mc_override=False, **kwargs)
        except ConfigBaseException as ex:
            if _debug_exc:
                raise
            raise ex

    def override(self, name, value):
        try:
            self._setattr(name, _mc_override=True, default=value)
        except ConfigBaseException as ex:
            if _debug_exc:
                raise
            raise ex

    def check_attr_fully_defined(self, attribute):
        name = attribute.attribute_name

        if not attribute.has_default() and not hasattr(attribute, 'already_checked'):
            # Check whether we need to check for conditionally required attributes
            required_if_key = self.__class__._mc_deco_required_if[0]
            if required_if_key:
                # A required_if CONDITION attribute is optional, so it is ok if it is not set or not set for all environments
                if name == required_if_key:
                    return

                try:
                    required_if_condition_attr = self._mc_attributes[required_if_key]
                    required_if_attribute_names = self.__class__._mc_deco_required_if[1]
                except KeyError:
                    # The condition property was not specified, so the conditional properties are not required
                    required_if_key = False

            # Validate that the attribute is defined for all envs
            valid_envs = self.root_conf._mc_valid_envs if not self._mc_include_in_envs else self._mc_include_in_envs
            for eg in valid_envs:
                for env in eg.envs():
                    if env in attribute.env_values:
                        # The attribute is set with an env specific value
                        continue

                    # Check for required_if, the required_if atributes are optional if required_if_condition value is false or not specified for the env
                    try:
                        if required_if_key and not required_if_condition_attr._mc_value(env) and name in required_if_attribute_names:
                            continue
                    except NoAttributeException:
                        continue

                    for ex_eg in self._mc_exclude_from_envs:
                        if env in ex_eg:
                            break
                    else:
                        group_msg = ", which is a member of " + repr(eg) if isinstance(eg, EnvGroup) else ""
                        msg = "Attribute: " + repr(name) + " did not receive a value for env " + repr(env)
                        attribute.error(msg + group_msg)

        if attribute.num_errors:
            attribute.already_checked = True
            raise ConfigException("There were " + repr(attribute.num_errors) + " errors when defining attribute " + repr(name) + " on object: " + repr(self))

    def _check_env_is_valid(self, env, valid_envs):
        """Expects env to be of type env"""
        for valid_env in valid_envs:
            if env in valid_env:
                return
        raise ConfigException("The env " + repr(env) + " must be in the (nested) list of valid_envs " + repr(valid_envs))

    def _check_valid_env(self, env, valid_envs):
        if not isinstance(env, Env):
            raise ConfigException(self.__class__.__name__ + ': env must be instance of ' + repr(Env.__name__) + '; found type ' + repr(env.__class__.__name__) + ': ' + repr(env))

        return self._check_env_is_valid(env, valid_envs)

    def __getattr__(self, name):
        if name.startswith('__'):
            return super(_ConfigBase, self).__getattr__(name)

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
            try:
                self_repr = repr(self)
            except:
                self_repr = repr(type(self))
            raise AttributeError(self_repr + " has no attribute " + repr(name) + error_message)

        try:
            return attr._mc_value(self.env)
        except NoAttributeException as ex:
            raise AttributeError(ex.message)

    def iteritems(self):
        for key, item in self._mc_attributes.iteritems():
            try:
                yield key, item._mc_value(self.env)
            except NoAttributeException:
                # This should only happen in case of  a conditional attribute
                pass

    @property
    def contained_in(self):
        if not isinstance(self._mc_contained_in, ConfigBuilder):
            return self._mc_contained_in
        if self._mc_root_conf._mc_under_proxy_build:
            return self._mc_contained_in.contained_in
        raise ConfigApiException("Use of 'contained_in' in not allowed in object while under a ConfigBuilder")

    @property
    def root_conf(self):
        return self._mc_root_conf

    @property
    def env(self):
        return self._mc_root_conf._mc_selected_env

    @property
    def valid_envs(self):
        return self._mc_root_conf.valid_envs

    def _mc_find_json_filter_callable(self):
        contained_in = self
        while contained_in:
            if contained_in._mc_json_filter:
                return contained_in._mc_json_filter
            contained_in = contained_in._mc_contained_in
        return None

    def _mc_find_json_fallback_callable(self):
        contained_in = self
        while contained_in:
            if contained_in._mc_json_fallback:
                return contained_in._mc_json_fallback
            contained_in = contained_in._mc_contained_in
        return None

    def find_contained_in_or_none(self, named_as):
        """Find first parent container named as 'named_as', by searching backwards towards root_conf, starting with parent container"""
        contained_in = self.contained_in
        while contained_in:
            if contained_in.named_as() == named_as:
                return contained_in
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

        msg = ': Could not find a parent container named as: ' + repr(named_as) + ' in hieracy with names: ' + repr(contained_in_names)
        raise ConfigException("Searching from: " + repr(type(self)) + msg)

    def find_attribute_or_none(self, attribute_name):
        """Find first occurence of attribute 'attribute_name', by searching backwards towards root_conf, starting with self."""
        contained_in = self
        while contained_in:
            attr = contained_in._mc_attributes.get(attribute_name)
            if attr:
                return contained_in.__getattr__(attribute_name)
            contained_in = contained_in.contained_in
        return None

    def find_attribute(self, attribute_name):
        """Find first occurence of attribute 'attribute_name', by searching backwards towards root_conf, starting with self."""
        contained_in = self
        while contained_in:
            attr = contained_in._mc_attributes.get(attribute_name)
            if attr:
                return contained_in.__getattr__(attribute_name)
            contained_in = contained_in.contained_in

        # Error, create error message
        contained_in = self
        contained_in_names = []
        while contained_in:
            contained_in_names.append(contained_in.named_as())
            contained_in = contained_in.contained_in

        msg = ': Could not find an attribute named: ' + repr(attribute_name) + ' in hieracy with names: ' + repr(contained_in_names)
        raise ConfigException("Searching from: " + repr(type(self)) + msg)

    def _user_validate_recursively(self):
        """Call the user defined 'validate' methods on all items"""
        if self._mc_user_validated:
            return

        try:
            self.validate()
        except Exception as ex:
            ex._mc_in_user_code = True
            raise
        finally:
            self._mc_user_validated = True

        for child_value in self._mc_attributes.values():
            child_value._user_validate_recursively()

    def validate(self):
        """Can be overridden to provide post-frozen validation"""
        pass

    def mc_init(self):
        """Can be overridden in derived classes to instantiate default child objects"""
        pass

    def _mc_value(self, env):
        return self


class ConfigRoot(_ConfigBase):
    def __init__(self, selected_env, valid_envs, mc_json_filter=None, mc_json_fallback=None, **attr):
        if not isinstance(valid_envs, Sequence) or isinstance(valid_envs, str):
            raise ConfigException(self.__class__.__name__ + ": valid_envs arg must be a 'Sequence'; found type " + repr(valid_envs.__class__.__name__) + ': ' + repr(valid_envs))

        for env in valid_envs:
            if not isinstance(env, BaseEnv):
                raise ConfigException(self.__class__.__name__ + ": valid_envs items must be instance of " + repr(Env.__name__) + " or " + repr(EnvGroup.__name__) + "; found a " + repr(env.__class__.__name__) + ': ' + repr(env))

        self._check_valid_env(selected_env, valid_envs)

        del self.__class__._mc_nested[:]

        self._mc_selected_env = selected_env
        self._mc_valid_envs = valid_envs
        super(ConfigRoot, self).__init__(mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback, **attr)
        self._mc_root_conf = self
        self._mc_contained_in = None
        self._mc_nesting_level = 0
        self._mc_under_proxy_build = False

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            super(ConfigRoot, self).__exit__(exc_type, exc_value, traceback)
            self._user_validate_recursively()
        except Exception as ex:
            if not exc_type:
                if hasattr(ex, '_mc_in_user_code') or _debug_exc:
                    raise
                raise ex

    @property
    def valid_envs(self):
        return self._mc_valid_envs


class ConfigItem(_ConfigBase):
    def __init__(self, mc_json_filter=None, mc_json_fallback=None, mc_include=None, mc_exclude=None, **attr):
        super(ConfigItem, self).__init__(mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback, **attr)

        if not self.__class__._mc_nested:
            raise ConfigException(self.__class__.__name__ + " object must be nested (indirectly) in a " + repr(ConfigRoot.__name__))
        self._mc_nesting_level = len(self.__class__._mc_nested)

        # Set back reference to containing Item and root item
        self._mc_contained_in = self.__class__._mc_nested[-1]
        self._mc_root_conf = self._mc_contained_in.root_conf

        if mc_exclude:
            self._mc_exclude_from_envs = mc_exclude
            for eg in mc_exclude:
                if self.env in eg.envs():
                    self._mc_is_excluded = True

        if mc_include:
            self._mc_include_in_envs = mc_include
            for eg in mc_include:
                if self.env in eg.envs():
                    break
            else:
                self._mc_is_excluded = True

        self._mc_contained_in._mc_insert_item(self)

    def _error_msg_not_repeatable_in_container(self, key, containing_class):
        return repr(key) + ': ' + repr(self) + ' is defined as repeatable, but this is not defined as a repeatable item in the containing class: ' + \
            repr(containing_class.named_as())


class ConfigBuilder(ConfigItem):
    __metaclass__ = abc.ABCMeta

    def __init__(self, mc_json_filter=None, mc_include=None, mc_exclude=None, **attr):
        super(ConfigBuilder, self).__init__(mc_json_filter=mc_json_filter, mc_include=mc_include, mc_exclude=mc_exclude, **attr)

    def _mc_post_build_update(self):
        def set_my_attributes_on_item_from_build(item_from_build, clone):
            for override_key, override_value in self._mc_attributes.iteritems():
                if override_value._mc_value(self.env) == None:
                    continue

                if isinstance(override_value, Repeatable):
                    for rep_override_key, rep_override_value in override_value.iteritems():
                        if not override_key in item_from_build.__class__._mc_deco_nested_repeatables:
                            raise ConfigException(rep_override_value._error_msg_not_repeatable_in_container(override_key, item_from_build))
                        ov = copy.copy(rep_override_value) if clone else rep_override_value
                        ov._mc_contained_in = item_from_build

                        item_from_build._mc_attributes[override_key][rep_override_key] = ov
                    continue

                if isinstance(override_value, ConfigItem):
                    ov = copy.copy(override_value) if clone else override_value
                    ov._mc_contained_in = item_from_build
                    item_from_build._mc_attributes[override_key] = ov
                    continue

                item_from_build._mc_attributes[override_key] = override_value

        def from_build_to_parent(build_key, build_value, clone):
            """Copy/Merge all items/attributes defined in 'build' into parent object"""
            parent = self._mc_contained_in
            parent_attributes = parent._mc_build_attributes if parent._mc_in_build else parent._mc_attributes

            # Merge repeatable items into parent
            if isinstance(build_value, Repeatable):
                for rep_key, rep_value in build_value.iteritems():
                    rep_value._mc_contained_in = parent
                    set_my_attributes_on_item_from_build(rep_value, clone=clone)

                    if isinstance(parent, ConfigBuilder):
                        parent_attributes.setdefault(build_key, Repeatable())
                    elif not build_key in parent.__class__._mc_deco_nested_repeatables:
                        raise ConfigException(rep_value._error_msg_not_repeatable_in_container(build_key, parent))

                    if rep_key in parent_attributes[build_key]:
                        # TODO: Silently skip insert instead (optional warning)?
                        raise ConfigException("Nested repeatable from 'build', key: " + repr(rep_key) + ", value: " + repr(rep_value) +
                                              " overwrites existing entry in parent: " + repr(parent))

                    parent_attributes[build_key][rep_key] = rep_value
                return

            if isinstance(build_value, ConfigItem):
                build_value._mc_contained_in = parent
                set_my_attributes_on_item_from_build(build_value, clone=clone)

            # Set non-repeatable items on parent
            # TODO validation
            parent_attributes[build_key] = build_value

        def move_items_around():
            # Loop over attributes created in build
            # Items and attributes created in 'build' goes into parent
            # Attributes/Items on builder are copied to items created in build
            clone = False
            for build_key, build_value in self._mc_build_attributes.iteritems():
                from_build_to_parent(build_key, build_value, clone)
                clone = True

        move_items_around()

    @abc.abstractmethod
    def build(self):
        """Override this in derived classes. This is where child ConfigItems are declared"""
        raise Exception("AbstractNotImplemented")

    def what_built(self):
        return OrderedDict([(key, attr._mc_value(self.env)) for key, attr in self._mc_build_attributes.iteritems()])

    def named_as(self):
        return super(ConfigBuilder, self).named_as() + '.builder.' + repr(id(self))

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, abc, os, copy
from collections import OrderedDict
import json

from .envs import EnvFactory, Env, EnvException
from .attribute import Attribute, mc_where_from_nowhere, mc_where_from_init, mc_where_from_with, mc_where_from_mc_init
from .values import MC_TODO, _MC_NO_VALUE, _mc_invalid_values
from .repeatable import Repeatable
from .excluded import Excluded
from .config_errors import ConfigBaseException, ConfigException, ConfigApiException, ConfigAttributeError
from .config_errors import _api_error_msg, caller_file_line, find_user_file_line, _line_msg as line_msg
from .config_errors import _error_msg, _warning_msg, _error_type_msg
from .json_output import ConfigItemEncoder

_debug_exc = str(os.environ.get('MULTICONF_DEBUG_EXCEPTIONS')).lower() == 'true'
_warn_json_nesting = str(os.environ.get('MULTICONF_WARN_JSON_NESTING')).lower() == 'true'


# pylint: disable=protected-access


def debug(*args):
    print(*args)


class _ConfigBase(object):
    _mc_nested = []

    # Decoration attributes
    _mc_deco_named_as = None
    _mc_deco_repeatable = False
    _mc_deco_nested_repeatables = []
    _mc_deco_required = []
    _mc_deco_required_if = (None, ())
    _mc_deco_unchecked = None

    def __init__(self, _mc_root_conf, _mc_env_factory, mc_json_filter=None, mc_json_fallback=None, **attr):
        self._mc_json_filter = mc_json_filter
        self._mc_json_fallback = mc_json_fallback
        self._mc_root_conf = _mc_root_conf
        _mc_attributes = Repeatable()
        self._mc_attributes = _mc_attributes
        self._mc_build_attributes = Repeatable()
        self._mc_frozen = False
        self._mc_built = False
        self._mc_in_init = True
        self._mc_in_mc_init = False
        self._mc_in_build = False
        self._mc_user_validated = False
        self._mc_previous_child = None
        self._mc_is_excluded = False
        self._mc_included_envs_mask = _mc_env_factory._all_envs_mask
        self._mc_json_errors = 0

        # Prepare attributes with default values
        file_name, line_num = find_user_file_line(up_level_start=3)

        __class__ = object.__getattribute__(self, '__class__')
        _mc_deco_nested_repeatables = __class__._mc_deco_nested_repeatables
        for key, value in attr.iteritems():
            if key in _mc_deco_nested_repeatables:
                raise ConfigException(repr(key) + ' defined as default value shadows a nested-repeatable')
            try:
                object.__getattribute__(__class__, key)
                raise ConfigException("The attribute " + repr(key) + " (not ending in '!') clashes with a property or method")
            except AttributeError:
                pass
            attribute = Attribute(key)
            if not value in _mc_invalid_values:
                attribute.set_env_provided(_mc_env_factory._mc_init_group)
                attribute.set_current_env_value(value, _mc_env_factory._mc_init_group, mc_where_from_init, file_name, line_num)
            else:
                attribute.set_invalid_value(value, _mc_env_factory._mc_init_group, mc_where_from_init, file_name, line_num)
            _mc_attributes[key] = attribute

        for key in _mc_deco_nested_repeatables:
            _mc_attributes[key] = Repeatable()

        # If a base class is unchecked, the attribute need not be fully defined, here. The remaining envs may receive values in the base class mc_init
        _mc_deco_unchecked = object.__getattribute__(self, '_mc_deco_unchecked')
        self._mc_check = _mc_deco_unchecked != __class__ and _mc_deco_unchecked not in __class__.__bases__

    def named_as(self):
        """Return the named_as property set by the @named_as decorator"""
        __class__ = object.__getattribute__(self, '__class__')
        if __class__._mc_deco_named_as:
            return __class__._mc_deco_named_as
        if __class__._mc_deco_repeatable:
            return __class__.__name__ + 's'
        return __class__.__name__

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
        json_method = object.__getattribute__(self, 'json')
        return json_method(compact=True, property_methods=False, builders=True)
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
        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        _mc_build_attributes = object.__getattribute__(self, '_mc_build_attributes')
        _mc_in_build = object.__getattribute__(self, '_mc_in_build')
        attributes = _mc_build_attributes if _mc_in_build else _mc_attributes

        if child_item.__class__._mc_deco_repeatable:
            # Repeatable excluded items are simply excluded
            if child_item._mc_is_excluded:
                return

            # Validate that this class specifies item as repeatable
            if isinstance(self, ConfigBuilder):
                attributes.setdefault(child_key, Repeatable())
            elif not child_key in self.__class__._mc_deco_nested_repeatables:
                raise ConfigException(child_item._error_msg_not_repeatable_in_container(child_key, self))
            elif self._mc_in_mc_init or self._mc_in_build:
                attributes.setdefault(child_key, Repeatable())

            # Calculate key to use when inserting repeatable item in Repeatable dict
            # Key is calculated as 'obj.id', 'obj.name' or id(obj) in that preferred order
            cha = child_item._mc_attributes
            specified_key = cha.get('id') or cha.get('name')
            # specified_key._value will be the __init__ value at this point if set
            obj_key = specified_key._value if specified_key is not None and not specified_key._value in _mc_invalid_values else id(child_item)
            item = attributes[child_key].setdefault(obj_key, child_item)

            if item is not child_item and not self._mc_in_mc_init:
                # We are trying to replace an object with the same id/name
                raise ConfigException("Re-used id/name " + repr(obj_key) + " in nested objects")
            return

        if child_key in attributes:
            if self._mc_in_mc_init:
                return

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

    def json(self, compact=False, property_methods=True, builders=False, skipkeys=True):
        """See json_output.ConfigItemEncoder for parameters"""
        filter_callable = self._mc_find_json_filter_callable()
        fallback_callable = self._mc_find_json_fallback_callable()
        encoder = ConfigItemEncoder(filter_callable=filter_callable, fallback_callable=fallback_callable,
                                    compact=compact, property_methods=property_methods, builders=builders, warn_nesting=_warn_json_nesting)
        json_str = json.dumps(self, skipkeys=skipkeys, default=encoder, check_circular=False, sort_keys=False, indent=4, separators=(',', ': '))
        self._mc_json_errors = encoder.num_errors
        return json_str

    def num_json_errors(self):
        """
        Returns number of errors encountered when generating json
        Return None if json() has not been called
        """
        return self._mc_json_errors

    def __enter__(self):
        assert not self._mc_frozen
        self._mc_in_init = False
        self.__class__._mc_nested.append(self)
        return self

    def _mc_freeze_validation(self):
        # Validate all unfrozen attributes
        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        for attr in _mc_attributes.itervalues():
            if not attr._mc_frozen and isinstance(attr, Attribute):
                self.check_attr_fully_defined(attr, num_errors=0)

        # Validate @required
        missing = []
        for req in self.__class__._mc_deco_required:
            if not req in _mc_attributes:
                missing.append(req)
        if missing:
            raise ConfigException("No value given for required attributes: " + repr(missing))

        # Validate @required_if
        required_if_key = self.__class__._mc_deco_required_if[0]
        if not required_if_key:
            return

        try:
            required_if_condition_attr = _mc_attributes[required_if_key]
            required_if_condition = required_if_condition_attr._mc_value()
            if not required_if_condition:
                return
        except KeyError:
            return

        missing = []
        for req in self.__class__._mc_deco_required_if[1]:
            if not req in _mc_attributes:
                missing.append(req)
            else:
                attr = _mc_attributes[req]
                if isinstance(attr, Attribute):
                    self.check_attr_fully_defined(attr, 0)

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
        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        for _child_name, child_value in _mc_attributes.iteritems():
            self._mc_frozen &= child_value._mc_freeze()

        if not self._mc_built:
            must_pop = False
            self._mc_in_init = False
            if self._mc_nested[-1] != self:
                must_pop = True
                self._mc_nested.append(self)
            try:
                was_under_proxy_build = self._mc_root_conf._mc_under_proxy_build
                self._mc_in_mc_init = True
                self.mc_init()
                self._mc_in_mc_init = False
                for _name, value in _mc_attributes.iteritems():
                    self._mc_frozen &= value._mc_freeze()

                if isinstance(self, ConfigBuilder):
                    self._mc_in_build = True
                    self._mc_root_conf._mc_under_proxy_build = True
                    self.build()
                    for _name, value in self._mc_build_attributes.iteritems():
                        self._mc_frozen &= value._mc_freeze()
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
        mc_caller_file_name, mc_caller_line_num = caller_file_line()
        self.setattr(name, mc_caller_file_name=mc_caller_file_name, mc_caller_line_num=mc_caller_line_num, default=value)

    def setattr(self, name, mc_caller_file_name=None, mc_caller_line_num=None, **kwargs):
        """Set attributes with environment specific values"""
        if name[0] == '_':
            msg = "Trying to set attribute " + repr(name) + " on a config item. "
            if name.startswith('_mc'):
                raise ConfigException(msg + "Atributes starting with '_mc' are reserved for multiconf internal usage.")
            raise ConfigException(msg + "Atributes starting with '_' can not be set using item.setattr. Use assignment instead.")

        # For error messages
        num_errors = 0
        if not mc_caller_file_name:
            mc_caller_file_name, mc_caller_line_num = caller_file_line()

        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        _mc_build_attributes = object.__getattribute__(self, '_mc_build_attributes')
        _mc_in_build = object.__getattribute__(self, '_mc_in_build')
        attributes = _mc_build_attributes if _mc_in_build else _mc_attributes

        __class__ = object.__getattribute__(self, '__class__')
        if name.endswith('!'):
            override_method = True
            name = name.strip('!')
            try:
                real_attr = object.__getattribute__(__class__, name)
                if not isinstance(real_attr, property):
                    raise ConfigException(name + "! specifies overriding a property method, but " + repr(name) + " is not a property.")
            except AttributeError:
                raise ConfigException(name + "! specifies overriding a property method, but no property named " + repr(name) + " exists.")
        else:
            override_method = False
            try:
                object.__getattribute__(__class__, name)
                raise ConfigException("The attribute " + repr(name) + " (not ending in '!') clashes with a property or method")
            except AttributeError:
                pass
        attribute = attributes.setdefault(name, Attribute(name, override_method=override_method))

        _mc_in_mc_init = object.__getattribute__(self, '_mc_in_mc_init')
        if attribute._mc_frozen and not _mc_in_mc_init:
            msg = "The attribute " + repr(name) + " is already fully defined"
            num_errors = _error_msg(num_errors, msg, file_name=mc_caller_file_name, line_num=mc_caller_line_num)
            raise ConfigException(msg + " on object " + repr(self))

        def type_error(value, other_env, other_type, num_errors):
            line_msg(file_name=mc_caller_file_name, line_num=mc_caller_line_num, msg=eg.name + ' ' + repr(type(value)))
            other_file_name, other_line_num = mc_caller_file_name, mc_caller_line_num
            if not other_env:
                other_env = other_env or self._mc_root_conf._mc_env_factory.env_or_group_from_bit(attribute.value_from_eg_bit)
                other_file_name, other_line_num = attribute.file_name, attribute.line_num
            line_msg(file_name=other_file_name, line_num=other_line_num, msg=other_env.name + ' ' + repr(other_type))
            msg = "Found different value types for property " + repr(name) + " for different envs"
            return _error_type_msg(num_errors, msg)

        def repeated_env_error(env, conflicting_egs, num_errors):
            # TODO __file__ line of attribute set in any scope!
            #new_eg_msg = repr(self._mc_root_conf._mc_selected_env) + ("" if isinstance(eg, EnvGroup) else " from group " + repr(eg))
            #new_vfl = (value, (mc_caller_file_name, mc_caller_line_num))
            #prev_eg_msg = repr(previous_eg)
            #prev_vfl = (attribute._value, (attribute.file_name, attribute.line_num))
            #msg = "A value is already specified for: " + new_eg_msg + '=' + repr(new_vfl) + ", previous value: " + prev_eg_msg + '=' + repr(prev_vfl)
            msg = "Value for env " + repr(env.name) + " is specified more than once, with no single most specific group or direct env:"
            for eg in sorted(conflicting_egs):
                value = kwargs[eg.name]
                msg += "\nvalue: " + repr(value) + ", from: " + repr(eg)
            return _error_msg(num_errors, msg, file_name=mc_caller_file_name, line_num=mc_caller_line_num)

        _mc_in_init = object.__getattribute__(self, '_mc_in_init')
        if not _mc_in_init and self._mc_check:
            attribute._mc_frozen = True

        other_env = None
        other_value = attribute._value
        other_type = type(other_value) if other_value is not None and other_value not in _mc_invalid_values else None

        orig_attr_where_from = attribute.where_from
        if orig_attr_where_from != mc_where_from_nowhere:
            orig_attr_value_from_eg_bit = attribute.value_from_eg_bit
            orig_attr_eg = self._mc_root_conf._mc_env_factory.env_or_group_from_bit(orig_attr_value_from_eg_bit)

        where_from = mc_where_from_init if _mc_in_init else mc_where_from_mc_init if _mc_in_mc_init else mc_where_from_with

        selected_env = self._mc_root_conf._mc_selected_env
        current_env_from_eg = None
        all_ambiguous = {}
        seen_egs = OrderedDict()

        # Validate given env values, assign current env value from most specific argument
        for eg_name, value in kwargs.iteritems():
            #debug("eg_name:", eg_name)
            try:
                eg = self._mc_root_conf._mc_env_factory.env_or_group_from_name(eg_name)
                if value not in _mc_invalid_values:
                    attribute.set_env_provided(eg)

                    # Validate that attribute has the same type for all envs
                    if type(value) != other_type and value is not None:
                        if other_type is not None:
                            num_errors = type_error(value, other_env, other_type, num_errors)
                        else:
                            other_env = eg
                            other_type = type(value)
                else:
                    attribute.set_invalid_value(value, eg, where_from, mc_caller_file_name, mc_caller_line_num)

                # Check if this eg provides a more specific value for selected_env
                if selected_env in eg or selected_env == eg:
                    if current_env_from_eg is not None:
                        if eg in current_env_from_eg:
                            current_env_from_eg = eg
                            attribute.set_current_env_value(value, eg, where_from, mc_caller_file_name, mc_caller_line_num)
                    else:
                        # Check against already set value from another scope
                        update_value = True
                        if orig_attr_where_from != mc_where_from_nowhere:
                            if eg in orig_attr_eg:
                                #debug("New eg is more specific than orig, new:", eg, "orig:", orig_attr_eg)
                                pass
                            elif orig_attr_eg == eg:
                                #debug("Same eg, new:", eg.name, "orig:", orig_attr_eg.name)
                                if orig_attr_where_from < where_from or orig_attr_where_from in (mc_where_from_init, mc_where_from_mc_init):
                                    #debug("orig where_from < where_from or orig_attr_where_from == mc_where_from_init")
                                    pass
                                else:
                                    #debug("orig where_from > where_from")
                                    update_value = False
                            elif orig_attr_eg in eg:
                                #debug("Orig eg is the more specific, new", eg.name, "orig:", orig_attr_eg.name)
                                update_value = False

                        if update_value:
                            current_env_from_eg = eg
                            attribute.set_current_env_value(value, eg, where_from, mc_caller_file_name, mc_caller_line_num)

                # Check if this is more specific than a previous eg or not overlapping, and collect bitmask of all seen and ambigous envs
                for other_eg in seen_egs.values():
                    more_specific = eg in other_eg
                    less_specific = other_eg in eg

                    ambiguous = 0x0
                    if not (less_specific or more_specific):
                        ambiguous = eg.mask & other_eg.mask
                        if ambiguous:
                            all_ambiguous[(other_eg, eg)] = ambiguous

                seen_egs[eg_name] = eg
            except EnvException as ex:
                num_errors = _error_msg(num_errors, ex.message, file_name=mc_caller_file_name, line_num=mc_caller_line_num)

        # Clear resolved conflicts
        for eg_name, eg in seen_egs.items():
            cleared = []
            for conflicting_egs, ambiguous in all_ambiguous.items():
                if eg.mask & ambiguous == eg.mask:  # mask in or equal to ambiguous
                    ambiguous ^= eg.mask & ambiguous
                    if ambiguous:
                        all_ambiguous[conflicting_egs] = ambiguous
                    else:
                        cleared.append(conflicting_egs)

            for conflicting_egs in cleared:
                del all_ambiguous[conflicting_egs]

        # If we still have unresolved conflicts, it is an error
        if all_ambiguous:
            # Reorder to generate one error per ambiguous env
            all_ambiguous_by_envs = {}
            for conflicting_egs, ambiguous in all_ambiguous.items():
                for env in self._mc_root_conf._mc_env_factory.envs_from_mask(ambiguous):
                    all_ambiguous_by_envs.setdefault(env, set()).update(conflicting_egs)

            for env, conflicting_egs in sorted(all_ambiguous_by_envs.items()):
                num_errors = repeated_env_error(env, conflicting_egs, num_errors)

        if self._mc_check:
            try:
                self.check_attr_fully_defined(attribute, num_errors, file_name=mc_caller_file_name, line_num=mc_caller_line_num)
            except ConfigBaseException as ex:
                if _debug_exc:
                    raise
                raise ex

    def override(self, name, value):
        """Set attributes with environment specific values"""
        if name[0] == '_':
            msg = "Trying to set attribute " + repr(name) + " on a config item. "
            if name.startswith('_mc'):
                raise ConfigException(msg + "Atributes starting with '_mc' are reserved for multiconf internal usage.")
            raise ConfigException(msg + "Atributes starting with '_' can not be set using item.override. Use assignment instead.")

        mc_caller_file_name, mc_caller_line_num = caller_file_line()

        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        attributes = self._mc_build_attributes if self._mc_in_build else _mc_attributes
        attribute = attributes[name] = Attribute(name)

        if not self._mc_in_init and self._mc_check:
            attribute._mc_frozen = True

        where_from = mc_where_from_init if self._mc_in_init else mc_where_from_mc_init if self._mc_in_mc_init else mc_where_from_with
        default_group = self._mc_root_conf._mc_env_factory._mc_default_group
        if value in _mc_invalid_values:
            attribute.set_invalid_value(value, default_group, where_from, mc_caller_file_name, mc_caller_line_num)
            if self._mc_check:
                try:
                    self.check_attr_fully_defined(attribute, 0)
                except ConfigBaseException as ex:
                    if _debug_exc:
                        raise
                    raise ex
            return

        attribute.set_env_provided(default_group)
        attribute.set_current_env_value(value, default_group, where_from, mc_caller_file_name, mc_caller_line_num)

    def check_attr_fully_defined(self, attribute, num_errors, file_name=None, line_num=None):
        # In case of override_method, the attribute need not be fully defined, the property method will handle remaining values
        if not attribute.all_set(self._mc_included_envs_mask) and not hasattr(attribute, 'already_checked') and not attribute.override_method:
            # Check whether we need to check for conditionally required attributes
            required_if_key = self.__class__._mc_deco_required_if[0]
            if required_if_key:
                # A required_if CONDITION attribute is optional, so it is ok if it is not set or not set for all environments
                if attribute.name == required_if_key:
                    return

                required_if_attribute_names = self.__class__._mc_deco_required_if[1]
                try:
                    _mc_attributes = object.__getattribute__(self, '_mc_attributes')
                    required_if_condition_attr = _mc_attributes[required_if_key]
                except KeyError:
                    # The condition property was not specified, so the conditional attributes are not required
                    if attribute.name in required_if_attribute_names:
                        return

            # Check for which envs the attribute is not defined
            missing_envs_mask = self._mc_included_envs_mask & ~attribute.envs_set_mask
            for env in self._mc_root_conf._mc_env_factory.envs_from_mask(missing_envs_mask):
                # Check for required_if, the required_if atributes are optional if required_if_condition value is false or not specified for the env
                # Required if condition value is only checked for current env
                # TODO MC_TODO  with required_if tests
                if required_if_key and attribute.name in required_if_attribute_names:
                    if self._mc_root_conf._mc_selected_env != env or not required_if_condition_attr._value or not required_if_condition_attr.envs_set_mask & env.bit:
                        continue  # pragma: no cover

                # Check for which envs the attribute is MC_TODO
                value = _MC_NO_VALUE
                for inv_value, inv_eg, inv_where_from, inv_file_name, inv_line_num in attribute.invalid_values if hasattr(attribute, 'invalid_values') else ():
                    #debug("Checking MC_TODO, env, inv_value, inv_eg:", env, inv_value, inv_eg)
                    if env.bit & inv_eg.mask:
                        if self._mc_root_conf._mc_selected_env == env:
                            attribute._value = inv_value
                        value = inv_value
                        break

                #debug("attribute._value, value:", attribute._value, value)
                value_msg = (' ' + repr(value)) if value in _mc_invalid_values and value != _MC_NO_VALUE else ''
                current_env_msg = " current" if env == self.env else ''
                msg = "Attribute: " + repr(attribute.name) + value_msg + " did not receive a value for" + current_env_msg + " env " + repr(env)

                if value == MC_TODO:
                    if env != self.env and self.root_conf._mc_allow_todo:
                        self._warning_msg(msg, file_name=file_name, line_num=line_num)
                        continue
                    if self.root_conf._mc_allow_current_env_todo:
                        self._warning_msg(msg + ". Continuing with invalid configuration!", file_name=file_name, line_num=line_num)
                        continue

                num_errors = _error_msg(num_errors, msg, file_name=file_name, line_num=line_num)

        if num_errors:
            attribute.already_checked = True
            raise ConfigException("There were " + repr(num_errors) + " errors when defining attribute " + repr(attribute.name) + " on object: " + repr(self))

    def __getattribute__(self, name):
        if name[0] == '_':
            return object.__getattribute__(self, name)

        try:
            _mc_attributes = object.__getattribute__(self, '_mc_attributes')
            attr = _mc_attributes[name]
        except KeyError:
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                raise ConfigAttributeError(mc_object=self, attr_name=name)
        except AttributeError:
            __class__ = object.__getattribute__(self, '__class__')
            ex_msg = "An error was detected trying to get attribute " + repr(name) + " on class " + repr(__class__.__name__)
            msg  = "\n    - You did not initailize the parent class (parent __init__ method has not been called)."
            _api_error_msg(1, ex_msg + msg)
            raise ConfigApiException(ex_msg)

        mc_value = attr._mc_value()
        if mc_value != _MC_NO_VALUE:
            return mc_value

        if attr.override_method:
            try:
                return object.__getattribute__(self, name)
            except Exception:
                # We have both an mc_attribute and a property method on the object
                _mc_root_conf = object.__getattribute__(self, '_mc_root_conf')
                _mc_selected_env = object.__getattribute__(_mc_root_conf, '_mc_selected_env')
                raise AttributeError("Attribute " + repr(name) +
                                     " is defined as muticonf attribute and as property method, but value is undefined for env " +
                                     repr(_mc_selected_env) + " and method call failed")

        # This can only happen for conditional properties
        _mc_root_conf = object.__getattribute__(self, '_mc_root_conf')
        _mc_selected_env = object.__getattribute__(_mc_root_conf, '_mc_selected_env')
        raise AttributeError("Attribute " + repr(name) + " undefined for env " + repr(_mc_selected_env))

    def iteritems(self):
        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        for key, item in _mc_attributes.iteritems():
            value = item._mc_value()
            if value != _MC_NO_VALUE:  # _MC_NO_VALUE should only happen in case of  a conditional attribute
                yield key, value

    def _iterattributes(self):
        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        for key, item in _mc_attributes.iteritems():
            yield key, item

    @property
    def contained_in(self):
        _mc_contained_in = object.__getattribute__(self, '_mc_contained_in')
        if not isinstance(_mc_contained_in, ConfigBuilder):
            return _mc_contained_in
        if self._mc_root_conf._mc_under_proxy_build:
            return self._mc_contained_in.contained_in
        raise ConfigApiException("Use of 'contained_in' in not allowed in object while under a ConfigBuilder")

    @property
    def root_conf(self):
        return object.__getattribute__(self, '_mc_root_conf')

    @property
    def env(self):
        return object.__getattribute__(self, '_mc_root_conf')._mc_selected_env

    @property
    def env_factory(self):
        return self._mc_root_conf._mc_env_factory

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
            _mc_attributes = object.__getattribute__(contained_in, '_mc_attributes')
            attr = _mc_attributes.get(attribute_name)
            if attr:
                return getattr(contained_in, attribute_name)
            contained_in = contained_in.contained_in
        return None

    def find_attribute(self, attribute_name):
        """Find first occurence of attribute 'attribute_name', by searching backwards towards root_conf, starting with self."""
        contained_in = self
        while contained_in:
            _mc_attributes = object.__getattribute__(contained_in, '_mc_attributes')
            attr = _mc_attributes.get(attribute_name)
            if attr:
                return getattr(contained_in, attribute_name)
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

        _mc_attributes = object.__getattribute__(self, '_mc_attributes')
        for child_value in _mc_attributes.values():
            child_value._user_validate_recursively()

    def validate(self):
        """Can be overridden to provide post-frozen validation"""
        pass

    def mc_init(self):
        """Can be overridden in derived classes to instantiate default child objects"""
        pass

    def _mc_value(self):
        return self

    def _warning_msg(self, msg, file_name, line_num):
        self._mc_root_conf._mc_num_warnings = _warning_msg(self._mc_root_conf._mc_num_warnings, msg, file_name=file_name, line_num=line_num)


class ConfigRoot(_ConfigBase):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None, mc_allow_todo=False, mc_allow_current_env_todo=False, **attr):
        __class__ = object.__getattribute__(self, '__class__')
        if not isinstance(env_factory, EnvFactory):
            raise ConfigException(__class__.__name__ + ': env_factory arg must be instance of ' + repr(EnvFactory.__name__) + '; found type ' \
                                  + repr(env_factory.__class__.__name__) + ': ' + repr(env_factory))

        if not isinstance(selected_env, Env):
            raise ConfigException(__class__.__name__ + ': env must be instance of ' + repr(Env.__name__) + '; found type ' \
                                  + repr(selected_env.__class__.__name__) + ': ' + repr(selected_env))

        if selected_env.factory != env_factory:
            raise ConfigException("The selected env " + repr(selected_env) + " must be from the specified 'env_factory'")

        del __class__._mc_nested[:]

        self._mc_selected_env = selected_env
        self._mc_env_factory = env_factory
        self._mc_allow_todo = mc_allow_todo or mc_allow_current_env_todo
        self._mc_allow_current_env_todo = mc_allow_current_env_todo
        _mc_env_factory = object.__getattribute__(self, '_mc_env_factory')
        _mc_env_factory._mc_init_and_default_groups()
        super(ConfigRoot, self).__init__(_mc_root_conf=self, _mc_env_factory=_mc_env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback, **attr)
        self._mc_contained_in = None
        self._mc_under_proxy_build = False
        self._mc_num_warnings = 0

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
    def env_factory(self):
        return self._mc_env_factory


class ConfigItem(_ConfigBase):
    def __init__(self, mc_json_filter=None, mc_json_fallback=None, mc_include=None, mc_exclude=None, **attr):
        # Set back reference to containing Item and root item
        __class__ = object.__getattribute__(self, '__class__')
        if not __class__._mc_nested:
            raise ConfigException(__class__.__name__ + " object must be nested (indirectly) in a " + repr(ConfigRoot.__name__))

        _mc_contained_in = __class__._mc_nested[-1]
        self._mc_contained_in = _mc_contained_in
        _mc_root_conf = object.__getattribute__(_mc_contained_in, '_mc_root_conf')
        _mc_env_factory = object.__getattribute__(_mc_root_conf, '_mc_env_factory')
        super(ConfigItem, self).__init__(_mc_root_conf=_mc_root_conf, _mc_env_factory=_mc_env_factory,
                                         mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback, **attr)

        _mc_included_envs_mask = object.__getattribute__(self, '_mc_included_envs_mask')
        if mc_exclude:
            for eg in mc_exclude:
                _mc_included_envs_mask &= ~eg.mask

        _mc_contained_in_included_envs_mask = object.__getattribute__(_mc_contained_in, '_mc_included_envs_mask')
        if mc_include:
            include_masks = 0b0
            for eg in mc_include:
                if eg.mask & _mc_contained_in_included_envs_mask != eg.mask:
                    # TODO: proper error message listing envs
                    raise ConfigException("Inner mc_include has envs excluded at outer level")
                include_masks |= eg.mask
            _mc_included_envs_mask &= include_masks

        if not (self.env.mask & _mc_included_envs_mask) or _mc_contained_in._mc_is_excluded:
            self._mc_is_excluded = True
        self._mc_included_envs_mask = _mc_included_envs_mask & _mc_contained_in_included_envs_mask

        _mc_contained_in._mc_insert_item(self)

    def _error_msg_not_repeatable_in_container(self, key, containing_class):
        return repr(key) + ': ' + repr(self) + ' is defined as repeatable, but this is not defined as a repeatable item in the containing class: ' + \
            repr(containing_class.named_as())


class ConfigBuilder(ConfigItem):
    __metaclass__ = abc.ABCMeta

    def _mc_post_build_update(self):
        def set_my_attributes_on_item_from_build(item_from_build, clone):
            _mc_attributes = object.__getattribute__(self, '_mc_attributes')
            for override_key, override_value in _mc_attributes.iteritems():
                if override_value._mc_value() == None:
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
        return OrderedDict([(key, attr._mc_value()) for key, attr in self._mc_build_attributes.iteritems()])

    def named_as(self):
        return super(ConfigBuilder, self).named_as() + '.builder.' + repr(id(self))

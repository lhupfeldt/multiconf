# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, os, copy
from collections import OrderedDict
import json

from .envs import EnvFactory, Env, EnvGroup, EnvException
from .attribute import new_attribute, Attribute, Where
from .values import McInvalidValue
from .repeatable import Repeatable, UserRepeatable
from .excluded import Excluded
from .config_errors import ConfigBaseException, ConfigException, ConfigApiException, ConfigAttributeError
from .config_errors import _api_error_msg, caller_file_line, find_user_file_line, find_init_call_file_line, _line_msg
from .config_errors import _error_msg, _error_type_msg, _warning_type_msg, _mc_print_messages


from .json_output import ConfigItemEncoder

_debug_exc = str(os.environ.get('MULTICONF_DEBUG_EXCEPTIONS')).lower() == 'true'


# pylint: disable=protected-access

class _McExcludedException(Exception):
    pass


def debug(*args):
    print(*args)


class _ConfigBase(object):
    _mc_nested = []

    # Decoration attributes
    _mc_deco_named_as = None
    _mc_deco_nested_repeatables = []
    _mc_deco_required = []
    _mc_deco_unchecked = None
    _mc_deco_strict_setattr = False

    def __init__(self, root_conf, env_factory):
        self._mc_root_conf = root_conf
        _mc_attributes = Repeatable()
        self._mc_attributes = _mc_attributes
        self._mc_frozen = False
        self._mc_built = False
        self._mc_where = Where.IN_INIT
        self._mc_user_validated = False
        self._mc_previous_child = None
        self._mc_is_excluded = False
        self._mc_included_envs_mask = env_factory._all_envs_mask
        self._mc_json_errors = 0

        self._mc_file_name, self._mc_line_num = find_init_call_file_line(up_level_start=3)

        __class__ = object.__getattribute__(self, '__class__')
        _mc_deco_nested_repeatables = __class__._mc_deco_nested_repeatables
        for key in _mc_deco_nested_repeatables:
            ur = UserRepeatable()
            ur.contained_in = self
            _mc_attributes[key] = ur

        # If a base class is unchecked, the attribute need not be fully defined, here. The remaining envs may receive values in the base class mc_init
        _mc_deco_unchecked = object.__getattribute__(self, '_mc_deco_unchecked')
        self._mc_check = _mc_deco_unchecked != __class__ and _mc_deco_unchecked not in __class__.__bases__

    def _mc_error(self):
        if not hasattr(self, '_mc_num_errors'):
            self._mc_num_errors = 0
        self._mc_num_errors += 1

    def _mc_error_msg(self, message, up_level=2, file_name=None, line_num=None):
        _error_msg(message, up_level, file_name, line_num)
        self._mc_error()

    def _mc_error_type_msg(self, message):
        self._mc_error()
        return _error_type_msg(message)

    def _mc_warning_type_msg(self, msg):
        self._mc_root_conf._mc_num_warnings += 1
        return _warning_type_msg(msg)

    def _mc_raise_if_errors(self, already="\nCheck already printed error messages"):
        if hasattr(self, '_mc_num_errors'):
            num_errors = self._mc_num_errors
            ww, err = ('were', 'errors') if num_errors > 1 else ('was', 'error')
            raise ConfigException("There {ww} {num_errors} {err} when defining item: {self}{already}.".format(
                ww=ww, num_errors=num_errors, err=err, self=self, already=already))

    @classmethod
    def named_as(cls):
        """Return the named_as property set by the @named_as decorator"""
        return cls._mc_deco_named_as or cls.__name__

    def _mc_get_attributes_where(self):
        where = object.__getattribute__(self, '_mc_where')
        if where == Where.IN_BUILD:
            return object.__getattribute__(self, '_mc_build_attributes'), where
        else:
            return object.__getattribute__(self, '_mc_attributes'), where

    def __repr__(self):
        # Don't call property methods in repr, it is too dangerous, leading to double errors in case of incorrect user implemented property methods
        json_method = object.__getattribute__(self, 'json')
        return json_method(compact=True, property_methods=False, builders=True)

    def json(self, compact=False, property_methods=True, builders=False, skipkeys=True, warn_nesting=None):
        """See json_output.ConfigItemEncoder for parameters"""
        filter_callable = self._mc_root_conf._mc_json_filter
        fallback_callable = self._mc_root_conf._mc_json_fallback
        encoder = ConfigItemEncoder(filter_callable=filter_callable, fallback_callable=fallback_callable,
                                    compact=compact, property_methods=property_methods, builders=builders, warn_nesting=warn_nesting,
                                    multiconf_base_type=_ConfigBase, multiconf_root_type=ConfigRoot, multiconf_builder_type=_ConfigBuilder)
        # python3 doesn't need  separators=(',', ': ')
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
        self._mc_where = Where.IN_WITH
        self.__class__._mc_nested.append(self)
        return self

    def _mc_freeze(self, previous_child):
        """
        Recursively freeze contained items bottom up.
        If self is ready to be validated (exit from with_statement or not declared in a with_statement),
        then self will be frozen and validated
        """

        if self._mc_frozen:
            return True

        root_conf = object.__getattribute__(self, '_mc_root_conf')

        self._mc_frozen = self._mc_deco_unchecked != self.__class__ and not root_conf._mc_under_proxy_build
        attributes = object.__getattribute__(self, '_mc_attributes')
        for _child_name, child_value in attributes.items():
            self._mc_frozen &= child_value._mc_freeze(previous_child)

        if not self._mc_built:
            must_pop = False
            if self._mc_nested[-1] != self:
                must_pop = True
                self._mc_nested.append(self)
            try:
                was_under_proxy_build = root_conf._mc_under_proxy_build
                where = self._mc_where
                self._mc_where = Where.IN_MC_INIT
                self.mc_init()
                self._mc_where = where
                for _name, value in attributes.items():
                    self._mc_frozen &= value._mc_freeze(previous_child)

                if isinstance(self, _ConfigBuilder):
                    self._mc_where = Where.IN_BUILD
                    root_conf._mc_under_proxy_build = True
                    try:
                        self.build()
                    except _McExcludedException:
                        pass
                    for _name, value in self._mc_build_attributes.items():
                        self._mc_frozen &= value._mc_freeze(previous_child)
                    self._mc_post_build_update()
                    self._mc_where = where
            except Exception as ex:
                ex._mc_in_user_code = True
                raise
            finally:
                root_conf._mc_under_proxy_build = was_under_proxy_build
                if must_pop:
                    self._mc_nested.pop()
                self._mc_built = True

        if self._mc_frozen:
            # Self was just frozen

            # Now validate all unfrozen attributes

            # If we are validating 'previsous_child' then that was not defined in a 'with' statement, so we make sure the
            # file/line is pointing to the item declaration. If not the file/line will point to the end of the 'with' block
            if previous_child:
                file_name = self._mc_file_name
                line_num = self._mc_line_num
            else:
                file_name = None
                line_num = None

            _mc_attributes = object.__getattribute__(self, '_mc_attributes')
            messages = []
            for attr_name, attr in _mc_attributes.items():
                if not attr._mc_frozen and isinstance(attr, Attribute):
                    messages.extend(self._mc_check_attr_fully_defined_messages(attr_name, attr))
            if messages:
                _mc_print_messages(messages, file_name=file_name, line_num=line_num)

            # Validate @required
            missing = []
            for req in self.__class__._mc_deco_required:
                if req not in _mc_attributes:
                    missing.append(req)
            if missing:
                self._mc_error_msg("No value given for required attributes: " + repr(missing), file_name=file_name, line_num=line_num)
            self._mc_raise_if_errors()

        return self._mc_frozen

    @property
    def frozen(self):
        """Return frozen state"""
        return self._mc_frozen

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is _McExcludedException:
                self._mc_raise_if_errors()
                return True
            if not exc_type:
                self._mc_freeze(False)
        except Exception as ex:
            ex._mc_in_exit = True
            if hasattr(ex, '_mc_in_user_code') or _debug_exc:
                raise
            raise ex
        finally:
            self.__class__._mc_nested.pop()

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__
            super(_ConfigBase, self).__setattr__(name, value)
            return
        mc_caller_file_name, mc_caller_line_num = caller_file_line()
        self.setattr(name, mc_caller_file_name=mc_caller_file_name, mc_caller_line_num=mc_caller_line_num, default=value)

    @staticmethod
    def _mc_check_reserved_name(name, method_name):
        if name[0] == '_':
            msg = "Trying to set attribute " + repr(name) + " on a config item. "
            if name.startswith('_mc'):
                raise ConfigException(msg + "Atributes starting with '_mc' are reserved for multiconf internal usage.")
            raise ConfigException(msg + "Atributes starting with '_' can not be set using item." + method_name + ". Use assignment instead.")

    def _mc_setattr_common(self, name, attributes, attribute, where, mc_caller_file_name, mc_caller_line_num, overriding_property, **kwargs):
        """Set attributes with environment specific values"""
        existing_attr = attributes.get(name)

        if existing_attr is not None:
            if attribute.set_unknown and where != Where.IN_INIT and self.__class__._mc_deco_strict_setattr:
                # we are trying to set an undefined attribute outside of __init__
                raise ConfigException("Atempting to use '?' postfix to set attribute " + repr(name) + "  which exists on item: " + repr(self))

            if not isinstance(existing_attr, Attribute):
                if name in self._mc_deco_nested_repeatables:
                    raise ConfigException(repr(name) + ' is already defined as a nested-repeatable and may not be replaced with an attribute.')
                raise ConfigException(repr(name) + ' ' + repr(type(existing_attr)) + ' is already defined and may not be replaced with an attribute.')

            attribute = existing_attr
        else:
            if not attribute.set_unknown and where != Where.IN_INIT and self.__class__._mc_deco_strict_setattr and not overriding_property:
                # we are trying to set an already defined attribute using the '?' syntax
                raise ConfigException(
                    "All attributes must be defined in __init__ or set with the '?' postfix. " +
                    "Atempting to set attribute " + repr(name) + " which does not exist on item: " + repr(self))

            self._mc_check_reserved_name(name, 'setattr')
            attributes[name] = attribute

        if attribute._mc_frozen and where != Where.IN_MC_INIT:
            raise ConfigException("The attribute " + repr(name) + " is already fully defined")

        if not kwargs:
            self._mc_error_msg("No " + Env.__name__ + " or " + EnvGroup.__name__ + " names specified.")

        root_conf = object.__getattribute__(self, '_mc_root_conf')
        env_factory = object.__getattribute__(root_conf, '_mc_env_factory')
        selected_env = object.__getattribute__(root_conf, '_mc_selected_env')

        def type_error(value, other_env, other_type):
            _line_msg(file_name=mc_caller_file_name, line_num=mc_caller_line_num, msg=eg.name + ' ' + repr(type(value)))
            other_file_name, other_line_num = mc_caller_file_name, mc_caller_line_num
            if not other_env:
                other_env = other_env or env_factory.env_or_group_from_bit(attribute.value_from_eg_bit)
                other_file_name, other_line_num = attribute.file_name, attribute.line_num
            _line_msg(file_name=other_file_name, line_num=other_line_num, msg=other_env.name + ' ' + repr(other_type))
            msg = "Found different value types for property " + repr(name) + " for different envs"
            self._mc_error_msg(msg)

        def repeated_env_error(env, conflicting_egs):
            # TODO __file__ line of attribute set in any scope!
            # new_eg_msg = repr(selected_env) + ("" if isinstance(eg, EnvGroup) else " from group " + repr(eg))
            # new_vfl = (value, (mc_caller_file_name, mc_caller_line_num))
            # prev_eg_msg = repr(previous_eg)
            # prev_vfl = (attribute._value, (attribute.file_name, attribute.line_num))
            # msg = "A value is already specified for: " + new_eg_msg + '=' + repr(new_vfl) + ", previous value: " + prev_eg_msg + '=' + repr(prev_vfl)
            msg = "Value for env " + repr(env.name) + " is specified more than once, with no single most specific group or direct env:"
            for eg in sorted(conflicting_egs):
                value = kwargs[eg.name]
                msg += "\nvalue: " + repr(value) + ", from: " + repr(eg)
            self._mc_error_msg(msg, file_name=mc_caller_file_name, line_num=mc_caller_line_num)

        if where != Where.IN_INIT and self._mc_check:
            attribute._mc_frozen = True

        other_env = None
        other_value = attribute._value
        other_type = type(other_value) if other_value is not None and not isinstance(other_value, McInvalidValue) else None

        orig_attr_where_from = attribute.where_from
        if orig_attr_where_from != Where.NOWHERE:
            orig_attr_value_from_eg_bit = attribute.value_from_eg_bit
            orig_attr_eg = env_factory.env_or_group_from_bit(orig_attr_value_from_eg_bit)

        current_env_from_eg = None
        all_ambiguous = {}
        seen_egs = OrderedDict()

        # Validate given env values, assign current env value from most specific argument
        for eg_name, value in kwargs.items():
            # debug("eg_name:", eg_name)
            try:
                eg = env_factory.env_or_group_from_name(eg_name)
                if not isinstance(value, McInvalidValue) :
                    attribute.set_env_provided(eg)

                    # Validate that attribute has the same type for all envs
                    if type(value) != other_type and value is not None:
                        if other_type is not None:
                            type_error(value, other_env, other_type)
                        else:
                            other_env = eg
                            other_type = type(value)
                else:
                    attribute.set_invalid_value(value, eg, where, mc_caller_file_name, mc_caller_line_num)

                # Check if this eg provides a more specific value for selected_env
                if selected_env in eg or selected_env == eg:
                    if current_env_from_eg is not None:
                        if eg in current_env_from_eg:
                            current_env_from_eg = eg
                            attribute.set_current_env_value(value, eg, where, mc_caller_file_name, mc_caller_line_num)
                    else:
                        # Check against already set value from another scope
                        update_value = True
                        if orig_attr_where_from != Where.NOWHERE:
                            if attribute._value == McInvalidValue.MC_REQUIRED or attribute._value is None:
                                # debug("Existing value is overridable:", attribute._value)
                                pass
                            elif eg in orig_attr_eg:
                                # debug("New eg is more specific than orig, new:", eg, "orig:", orig_attr_eg)
                                pass
                            elif orig_attr_eg == eg:
                                # debug("Same eg, new:", eg.name, "orig:", orig_attr_eg.name)
                                if orig_attr_where_from < where or orig_attr_where_from in (Where.IN_INIT, Where.IN_MC_INIT):
                                    # debug("orig where_from < where_from or orig_attr_where_from == mc_where_from_init")
                                    pass
                                else:
                                    # debug("orig where_from > where_from")
                                    update_value = False
                            else:  # orig_attr_eg in eg:
                                # debug("Orig eg is the more specific, new", eg.name, "orig:", orig_attr_eg.name)
                                update_value = False

                        if update_value:
                            current_env_from_eg = eg
                            attribute.set_current_env_value(value, eg, where, mc_caller_file_name, mc_caller_line_num)

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
                self._mc_error_msg(str(ex), file_name=mc_caller_file_name, line_num=mc_caller_line_num)

        # Clear resolved conflicts
        for _eg_name, eg in seen_egs.items():
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
                for env in env_factory.envs_from_mask(ambiguous):
                    all_ambiguous_by_envs.setdefault(env, set()).update(conflicting_egs)

            for env, conflicting_egs in sorted(all_ambiguous_by_envs.items()):
                repeated_env_error(env, conflicting_egs)

        if where != Where.IN_INIT and self._mc_check:
            messages = self._mc_check_attr_fully_defined_messages(name, attribute)
            if messages:            
                _mc_print_messages(messages, file_name=mc_caller_file_name, line_num=mc_caller_line_num)

    def _mc_check_override_common(self, item, name, attribute):
        try:
            object.__getattribute__(item, name)
        except AttributeError:
            if not attribute.override_method:
                return False
            err_msg = "%(name)s! specifies overriding a property method, but no property named '%(name)s' exists."
            raise ConfigException(err_msg % dict(name=name))
        except:
            # Error in property implemetation
            pass

        if attribute.override_method:
            # This is expensive so do the quick __getattribute__ above first and only do this when necessary, i.e. we found an attribute
            def get_bases(cls):
                yield cls
                for cls1 in cls.__bases__:
                    for cls2 in get_bases(cls1):
                        yield cls2

            for cls in get_bases(object.__getattribute__(item, '__class__')):
                try:
                    real_attr = object.__getattribute__(cls, name)
                    if isinstance(real_attr, property):
                        return True

                    err_msg = "%(name)s! specifies overriding a property method, but attribute '%(name)s' with value '%(value)s' is not a property."
                    raise ConfigException(err_msg % dict(name=name, value=real_attr))
                except AttributeError:
                    pass

        raise ConfigException("The attribute '%(name)s' (not ending in '!') clashes with a property or method" % dict(name=name))

    def setattr(self, name, mc_caller_file_name=None, mc_caller_line_num=None, **kwargs):
        if not mc_caller_file_name or not mc_caller_line_num or not '.py' in mc_caller_file_name:  # TODO remove when switching to Python3
            mc_caller_file_name, mc_caller_line_num = caller_file_line()

        attribute, name = new_attribute(name)
        try:
            overriding_property = self._mc_check_override_common(self, name, attribute)
            attributes = object.__getattribute__(self, '_mc_attributes')
            where = object.__getattribute__(self, '_mc_where')
            self._mc_setattr_common(name, attributes, attribute, where, mc_caller_file_name, mc_caller_line_num, overriding_property, **kwargs)
        except ConfigException as ex:
            self._mc_error_msg(str(ex), file_name=mc_caller_file_name, line_num=mc_caller_line_num)

    def _mc_override_common(self, name, attributes, where, mc_caller_file_name, mc_caller_line_num, value):
        """Set attributes with environment specific values"""
        self._mc_check_reserved_name(name, 'override')

        attribute, name = new_attribute(name)
        attributes[name] = attribute

        root_conf = object.__getattribute__(self, '_mc_root_conf')
        env_factory = object.__getattribute__(root_conf, '_mc_env_factory')

        if where != Where.IN_INIT and self._mc_check:
            attribute._mc_frozen = True

        default_group = env_factory._mc_default_group
        if isinstance(value, McInvalidValue):
            attribute.set_invalid_value(value, default_group, where, mc_caller_file_name, mc_caller_line_num)
            if self._mc_check:
                messages = self._mc_check_attr_fully_defined_messages(name, attribute)
                if messages:                
                    _mc_print_messages(messages, file_name=mc_caller_file_name, line_num=mc_caller_line_num)
            return

        attribute.set_env_provided(default_group)
        attribute.set_current_env_value(value, default_group, where, mc_caller_file_name, mc_caller_line_num)

    def override(self, name, value, mc_caller_file_name=None, mc_caller_line_num=None):
        """Unconditionally set attributes even if frozen"""
        if not mc_caller_file_name or not mc_caller_line_num or not '.py' in mc_caller_file_name:  # TODO remove when switching to Python3
            mc_caller_file_name, mc_caller_line_num = caller_file_line()

        where = object.__getattribute__(self, '_mc_where')
        attributes = object.__getattribute__(self, '_mc_attributes')
        try:
            self._mc_override_common(name, attributes, where, mc_caller_file_name, mc_caller_line_num, value)
        except ConfigException as ex:
            self._mc_error_msg(str(ex), file_name=mc_caller_file_name, line_num=mc_caller_line_num)

    def _mc_check_attr_fully_defined_messages(self, name, attribute):
        # In case of override_method, the attribute need not be fully defined, the property method will handle remaining values
        if attribute.all_set(self._mc_included_envs_mask) or attribute.override_method:
            return []

        root_conf = object.__getattribute__(self, '_mc_root_conf')
        env_factory = object.__getattribute__(root_conf, '_mc_env_factory')
        selected_env = object.__getattribute__(root_conf, '_mc_selected_env')

        # Check for which envs the attribute is not defined
        messages= []
        missing_envs_mask = self._mc_included_envs_mask & ~attribute.envs_set_mask
        for env in env_factory.envs_from_mask(missing_envs_mask):
            # Check for which envs the attribute is McInvalidValue.MC_TODO
            value = McInvalidValue.MC_NO_VALUE
            for inv_value, inv_eg, inv_where_from, inv_file_name, inv_line_num in attribute.invalid_values:
                # debug("Checking MC_TODO, env, inv_value, inv_eg:", env, inv_value, inv_eg)
                if env.bit & inv_eg.mask:
                    if selected_env == env:
                        attribute._value = inv_value
                    value = inv_value
                    break

            # debug("attribute._value, value:", attribute._value, value)
            value_msg = (' ' + repr(value)) if isinstance(value, McInvalidValue) and value != McInvalidValue.MC_NO_VALUE else ''
            current_env_msg = " current" if env == self.env else ''
            msg = "Attribute: " + repr(name) + value_msg + " did not receive a value for" + current_env_msg + " env " + repr(env)

            if value == McInvalidValue.MC_TODO:
                if env != self.env and root_conf._mc_allow_todo:
                    messages.append(self._mc_warning_type_msg(msg))
                    continue
                if root_conf._mc_allow_current_env_todo:
                    messages.append(self._mc_warning_type_msg(msg + ". Continuing with invalid configuration!"))
                    continue

            messages.append(self._mc_error_type_msg(msg))

        return messages

    def __getattribute__(self, name):
        if name[0] == '_':
            return object.__getattribute__(self, name)

        try:
            attributes = object.__getattribute__(self, '_mc_attributes')
            attr = attributes[name]
        except KeyError:
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                raise ConfigAttributeError(mc_object=self, attr_name=name)
        except AttributeError:
            __class__ = object.__getattribute__(self, '__class__')
            ex_msg = "An error was detected trying to get attribute " + repr(name) + " on class " + repr(__class__.__name__)
            msg = "\n    - You did not initailize the parent class (parent __init__ method has not been called)."
            _api_error_msg(ex_msg + msg)
            raise ConfigApiException(ex_msg)

        mc_value = attr._mc_value()
        if mc_value != McInvalidValue.MC_NO_VALUE:
            return mc_value

        if self._mc_is_excluded:
            return Excluded(self)

        try:
            return object.__getattribute__(self, name)
        except Exception:
            root_conf = object.__getattribute__(self, '_mc_root_conf')
            selected_env = object.__getattribute__(root_conf, '_mc_selected_env')

            if attr.override_method:
                # We have both an mc_attribute and a property method on the object
                raise AttributeError("Attribute " + repr(name) +
                                     " is defined as muticonf attribute and as property method, but value is undefined for env " +
                                     repr(selected_env) + " and method call failed")

            # This can only happen for unchecked classes
            raise AttributeError("Attribute " + repr(name) + " is undefined for env " + repr(selected_env))

    def items(self):
        attributes = object.__getattribute__(self, '_mc_attributes')
        for key, item in attributes.items():
            value = item._mc_value()
            if value != McInvalidValue.MC_NO_VALUE:  # MC_NO_VALUE should only happen in case of  a conditional attribute
                yield key, value

    # For backwards compatibility
    iteritems = items

    def _iterattributes(self):
        attributes = object.__getattribute__(self, '_mc_attributes')
        for key, item in attributes.items():
            yield key, item

    @property
    def contained_in(self):
        contained_in = object.__getattribute__(self, '_mc_contained_in')
        if not isinstance(contained_in, _ConfigBuilder):
            return contained_in

        root_conf = object.__getattribute__(contained_in, '_mc_root_conf')
        if root_conf._mc_under_proxy_build:
            return contained_in.contained_in

        raise ConfigApiException("Use of 'contained_in' in not allowed in object while under a ConfigBuilder")

    @property
    def root_conf(self):
        return object.__getattribute__(self, '_mc_root_conf')

    @property
    def env(self):
        root_conf = object.__getattribute__(self, '_mc_root_conf')
        return object.__getattribute__(root_conf, '_mc_selected_env')

    @property
    def env_factory(self):
        root_conf = object.__getattribute__(self, '_mc_root_conf')
        return object.__getattribute__(root_conf, 'env_factory')

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
            attributes = object.__getattribute__(contained_in, '_mc_attributes')
            attr = attributes.get(attribute_name)
            if attr:
                return getattr(contained_in, attribute_name)
            contained_in = contained_in.contained_in
        return None

    def find_attribute(self, attribute_name):
        """Find first occurence of attribute 'attribute_name', by searching backwards towards root_conf, starting with self."""
        contained_in = self
        while contained_in:
            attributes = object.__getattribute__(contained_in, '_mc_attributes')
            attr = attributes.get(attribute_name)
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

        attributes = object.__getattribute__(self, '_mc_attributes')
        for child_value in attributes.values():
            child_value._user_validate_recursively()

    def validate(self):
        """Can be overridden to provide post-frozen validation"""
        pass

    def mc_init(self):
        """Can be overridden in derived classes to instantiate default child objects"""
        pass

    def _mc_value(self):
        return self


class ConfigRoot(_ConfigBase):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None, mc_allow_todo=False, mc_allow_current_env_todo=False):
        __class__ = object.__getattribute__(self, '__class__')
        if not isinstance(env_factory, EnvFactory):
            raise ConfigException(__class__.__name__ + ': env_factory arg must be instance of ' + repr(EnvFactory.__name__) + '; found type '
                                  + repr(env_factory.__class__.__name__) + ': ' + repr(env_factory))

        if not isinstance(selected_env, Env):
            raise ConfigException(__class__.__name__ + ': env must be instance of ' + repr(Env.__name__) + '; found type '
                                  + repr(selected_env.__class__.__name__) + ': ' + repr(selected_env))

        if selected_env.factory != env_factory:
            raise ConfigException("The selected env " + repr(selected_env) + " must be from the specified 'env_factory'")

        del __class__._mc_nested[:]

        self._mc_selected_env = selected_env
        self._mc_env_factory = env_factory
        self._mc_allow_todo = mc_allow_todo or mc_allow_current_env_todo
        self._mc_allow_current_env_todo = mc_allow_current_env_todo
        env_factory = object.__getattribute__(self, '_mc_env_factory')
        env_factory._mc_create_default_group()
        super(ConfigRoot, self).__init__(root_conf=self, env_factory=env_factory)
        self._mc_json_filter = mc_json_filter
        self._mc_json_fallback = mc_json_fallback
        self._mc_contained_in = None
        self._mc_under_proxy_build = False
        self._mc_num_warnings = 0
        self._mc_config_loaded = False

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            super(ConfigRoot, self).__exit__(exc_type, exc_value, traceback)
            if not exc_type:
                self._user_validate_recursively()
                self._mc_config_loaded = True
        except Exception as ex:
            if hasattr(ex, '_mc_in_user_code') or _debug_exc:
                raise
            raise ex

    @property
    def env_factory(self):
        return self._mc_env_factory

    def _mc_raise_if_errors_in_init(self):
        """Errors in __init__won't be handled, so we must raise at the end of each method"""
        where = object.__getattribute__(self, '_mc_where')
        if where == Where.IN_INIT:
            self._mc_raise_if_errors()

    def setattr(self, name, mc_caller_file_name=None, mc_caller_line_num=None, **kwargs):
        if not mc_caller_file_name or not mc_caller_line_num or not '.py' in mc_caller_file_name:  # TODO remove when switching to Python3
            mc_caller_file_name, mc_caller_line_num = caller_file_line()
        super(ConfigRoot, self).setattr(name, mc_caller_file_name, mc_caller_line_num, **kwargs)
        self._mc_raise_if_errors_in_init()

    def override(self, name, value, mc_caller_file_name=None, mc_caller_line_num=None):
        if not mc_caller_file_name or not mc_caller_line_num or not '.py' in mc_caller_file_name:  # TODO remove when switching to Python3
            mc_caller_file_name, mc_caller_line_num = caller_file_line()
        super(ConfigRoot, self).override(name, value, mc_caller_file_name, mc_caller_line_num)
        self._mc_raise_if_errors_in_init()


class _ConfigItem(_ConfigBase):
    def __init__(self, mc_include=None, mc_exclude=None):
        # Set back reference to containing Item and root item
        __class__ = object.__getattribute__(self, '__class__')
        if not __class__._mc_nested:
            raise ConfigException(__class__.__name__ + " object must be nested (indirectly) in a " + repr(ConfigRoot.__name__))

        contained_in = __class__._mc_nested[-1]

        # Freeze attributes on previously defined child
        previous_item = contained_in._mc_previous_child
        if previous_item and not previous_item.frozen:
            try:
                previous_item._mc_freeze(previous_child=True)
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

        self._mc_contained_in = contained_in
        root_conf = object.__getattribute__(contained_in, '_mc_root_conf')
        env_factory = object.__getattribute__(root_conf, '_mc_env_factory')
        super(_ConfigItem, self).__init__(root_conf=root_conf, env_factory=env_factory)
        self._mc_select_envs(mc_include, mc_exclude, self._mc_file_name, self._mc_line_num)

        if not self._mc_is_excluded:
            contained_in._mc_previous_child = self

    def _mc_freeze(self, previous_child):
        if self._mc_is_excluded:
            self._mc_frozen = True
            self._mc_raise_if_errors()
            return True

        return super(_ConfigItem, self)._mc_freeze(previous_child)

    def _mc_select_envs(self, include, exclude, file_name, line_num):
        """Determine if item (and children) is included in specified env"""
        # Resolve most specif include/exclude eg
        contained_in = object.__getattribute__(self, '_mc_contained_in')
        contained_in_included_envs_mask = object.__getattribute__(contained_in, '_mc_included_envs_mask')
        _mc_included_envs_mask = object.__getattribute__(self, '_mc_included_envs_mask')

        all_ambiguous = {}
        if exclude:
            for eg_excl in exclude:
                if include is None:
                    _mc_included_envs_mask &= ~eg_excl.mask
                    continue

                include_masks = 0b0
                for eg_incl in include:
                    # Check if this is more specific than a previous eg or not overlapping, and collect bitmask of all seen and ambiguous envs
                    must_excl = eg_excl in eg_incl
                    must_incl = eg_incl in eg_excl

                    ambiguous = 0x0
                    if not (must_incl or must_excl):
                        ambiguous = eg_excl.mask & eg_incl.mask
                        if ambiguous:
                            all_ambiguous[(eg_incl, eg_excl)] = ambiguous

                    if not ambiguous:
                        include_masks |= eg_incl.mask
                        include_masks &= ~eg_excl.mask

                _mc_included_envs_mask &= include_masks
        else:
            if include is not None:
                include_masks = 0b0
                for eg in include:
                    include_masks |= eg.mask
                _mc_included_envs_mask &= include_masks

        # Clear resolved conflicts
        cleared = []

        for conflicting_egs, ambiguous in all_ambiguous.items():
            for eg in include or ():
                if eg.mask & ambiguous == eg.mask:  # mask in or equal to ambiguous
                    ambiguous ^= eg.mask & ambiguous
                    if ambiguous:
                        all_ambiguous[conflicting_egs] = ambiguous
                    elif eg in conflicting_egs[1]:
                        cleared.append(conflicting_egs)
                    _mc_included_envs_mask |= eg.mask

            for eg in exclude or ():
                if eg.mask & ambiguous == eg.mask:  # mask in or equal to ambiguous
                    ambiguous ^= eg.mask & ambiguous
                    if ambiguous:
                        all_ambiguous[conflicting_egs] = ambiguous
                    elif eg in conflicting_egs[0]:
                        cleared.append(conflicting_egs)
                    _mc_included_envs_mask &= ~eg.mask

        for conflicting_egs in cleared:
            del all_ambiguous[conflicting_egs]

        # If we still have unresolved conflicts, it is an error
        if all_ambiguous:
            # Reorder to generate one error per ambiguous env
            all_ambiguous_by_envs = {}
            root_conf = object.__getattribute__(contained_in, '_mc_root_conf')
            env_factory = object.__getattribute__(root_conf, '_mc_env_factory')
            for conflicting_egs, ambiguous in all_ambiguous.items():
                for env in env_factory.envs_from_mask(ambiguous):
                    all_ambiguous_by_envs.setdefault(env, set()).update(conflicting_egs)

            for env, conflicting_egs in sorted(all_ambiguous_by_envs.items()):
                msg = "Env " + repr(env.name) + " is specified in both include and exclude, with no single most specific group or direct env:"
                for eg in sorted(conflicting_egs):
                    msg += "\n    from: " + repr(eg)
                self._mc_error_msg(msg, file_name=file_name, line_num=line_num)

        if include is not None and _mc_included_envs_mask & contained_in_included_envs_mask != _mc_included_envs_mask:
            re_included = _mc_included_envs_mask & contained_in_included_envs_mask ^ _mc_included_envs_mask
            root_conf = object.__getattribute__(contained_in, '_mc_root_conf')
            env_factory = object.__getattribute__(root_conf, '_mc_env_factory')
            for env in env_factory.envs_from_mask(re_included):
                msg = "Env " + repr(env.name) + " is excluded at an outer level"
                self._mc_error_msg(msg, file_name=file_name, line_num=line_num)

        self._mc_raise_if_errors(already="")

        if not (self.env.mask & _mc_included_envs_mask) or contained_in._mc_is_excluded:
            self._mc_is_excluded = True
            attributes = object.__getattribute__(self, '_mc_attributes')
            for _key, item in attributes.items():
                item._mc_is_excluded = True
        self._mc_included_envs_mask = _mc_included_envs_mask & contained_in_included_envs_mask

    def mc_select_envs(self, include=None, exclude=None, mc_caller_file_name=None, mc_caller_line_num=None):
        """Skip with block if item is excluded"""

        self._mc_select_envs(include=include, exclude=exclude, file_name=mc_caller_file_name, line_num=mc_caller_line_num)
        if self._mc_is_excluded:
            contained_in = object.__getattribute__(self, '_mc_contained_in')
            contained_in_attributes, _ = contained_in._mc_get_attributes_where()
            if isinstance(self, RepeatableConfigItem):
                # Remove repeatable item
                del contained_in_attributes[self.named_as()][self._mc_repeatable_item_key]
            else:
                contained_in_attributes[self.named_as()] = Excluded(self)

        if self._mc_is_excluded:
            raise _McExcludedException()

    def _error_msg_not_repeatable_in_container(self, key, containing_class):
        return repr(key) + ': ' + repr(self) + ' is defined as repeatable, but this is not defined as a repeatable item in the containing class: ' + \
            repr(containing_class.named_as())

    def __bool__(self):
        return not object.__getattribute__(self, '_mc_is_excluded')

    # Python2 compatibility
    __nonzero__ = __bool__


class ConfigItem(_ConfigItem):
    def __init__(self, mc_include=None, mc_exclude=None):
        super(ConfigItem, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        contained_in = self._mc_contained_in

        # Insert self in parent attributes
        my_key = self.named_as()
        attributes, where = contained_in._mc_get_attributes_where()

        if my_key in attributes:
            if where == Where.IN_MC_INIT:
                # TODO? override value from __init__
                return

            if isinstance(attributes[my_key], _ConfigItem):
                raise ConfigException("Repeated non repeatable conf item: " + repr(my_key))
            if isinstance(attributes[my_key], Repeatable):
                msg = repr(my_key) + ': ' + repr(self) + \
                    ' is defined as non-repeatable, but the containing object has repeatable items with the same name: ' + repr(contained_in)
                raise ConfigException(msg)
            raise ConfigException(repr(my_key) + ' is defined both as simple value and a contained item: ' + repr(self))

        if not self._mc_is_excluded:
            attributes[my_key] = self
            return

        # In case of a Non-Repeatable excluded item we insert an Excluded object which is always False
        # This makes it possible to do 'if x.item: ...' instead of hasattr(x, 'item') and allows for a nicer json dump
        attributes[my_key] = Excluded(self)


class RepeatableConfigItem(_ConfigItem):
    def __init__(self, mc_key, mc_include=None, mc_exclude=None):
        super(RepeatableConfigItem, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        contained_in = self._mc_contained_in

        # Insert self in parent attributes
        my_key = self.named_as()
        attributes, where = contained_in._mc_get_attributes_where()

        # Validate that this class specifies item as repeatable
        if isinstance(contained_in, _ConfigBuilder):
            ur = UserRepeatable()
            ur.contained_in = contained_in
            attributes.setdefault(my_key, UserRepeatable())
        elif my_key not in contained_in.__class__._mc_deco_nested_repeatables:
            raise ConfigException(self._error_msg_not_repeatable_in_container(my_key, contained_in))

        repeatable = attributes[my_key]

        # Repeatable excluded items are simply excluded, but in order to lookup excluded keys during config setup
        # we mark the repeatable as _mc_is_excluded
        if self._mc_is_excluded:
            repeatable._mc_is_excluded = True
            return

        # Calculate key to use when inserting repeatable item in Repeatable dict
        obj_key = mc_key if mc_key is not None else id(self)
        item = repeatable.setdefault(obj_key, self)

        if item is not self and where != Where.IN_MC_INIT:
            # We are trying to replace an object with the same id/name
            raise ConfigException("Re-used key " + repr(obj_key) + " in nested objects")
        self._mc_repeatable_item_key = obj_key

    @classmethod
    def named_as(cls):
        """Return the named_as property set by the @named_as decorator"""
        return cls._mc_deco_named_as or (cls.__name__ + 's')


class _ConfigBuilder(ConfigItem):
    _num = 0

    def __init__(self, mc_include=None, mc_exclude=None):
        super(_ConfigBuilder, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self._mc_build_attributes = Repeatable()
        _ConfigBuilder._num += 1

    def setattr(self, name, mc_caller_file_name=None, mc_caller_line_num=None, **kwargs):
        if not mc_caller_file_name or not mc_caller_line_num or not '.py' in mc_caller_file_name:  # TODO remove when switching to Python3
            mc_caller_file_name, mc_caller_line_num = caller_file_line()

        attribute, name = new_attribute(name)
        attributes, where = self._mc_get_attributes_where()
        try:
            self._mc_setattr_common(name, attributes, attribute, where, mc_caller_file_name, mc_caller_line_num, False, **kwargs)
        except ConfigException as ex:
            self._mc_error_msg(str(ex), file_name=mc_caller_file_name, line_num=mc_caller_line_num)

    def override(self, name, value, mc_caller_file_name=None, mc_caller_line_num=None):
        """Unconditionally set attributes even if frozen"""
        if not mc_caller_file_name or not mc_caller_line_num or not '.py' in mc_caller_file_name:  # TODO remove when switching to Python3
            mc_caller_file_name, mc_caller_line_num = caller_file_line()

        attributes, where = self._mc_get_attributes_where()
        try:
            self._mc_override_common(name, attributes, where, mc_caller_file_name, mc_caller_line_num, value)
        except ConfigException as ex:
            self._mc_error_msg(str(ex), file_name=mc_caller_file_name, line_num=mc_caller_line_num)

    def _mc_post_build_update(self):
        root_conf = object.__getattribute__(self, '_mc_root_conf')
        selected_env = object.__getattribute__(root_conf, '_mc_selected_env')
        attributes = object.__getattribute__(self, '_mc_attributes')

        override_attribute_errors = OrderedDict()

        def set_my_attributes_on_item_from_build(item_from_build, clone):
            for override_key, override_value in attributes.items():
                if override_value._mc_value() == None:
                    continue

                if isinstance(override_value, Repeatable):
                    for rep_override_key, rep_override_value in override_value.items():
                        if override_key not in item_from_build.__class__._mc_deco_nested_repeatables:
                            raise ConfigException(rep_override_value._error_msg_not_repeatable_in_container(override_key, item_from_build))
                        ov = copy.copy(rep_override_value) if clone else rep_override_value
                        ov._mc_contained_in = item_from_build

                        item_from_build._mc_attributes[override_key][rep_override_key] = ov
                    continue

                if isinstance(override_value, _ConfigItem):
                    ov = copy.copy(override_value) if clone else override_value
                    ov._mc_contained_in = item_from_build
                    item_from_build._mc_attributes[override_key] = ov
                    continue

                # override_value is an Attribute
                name = override_key
                try:
                    self._mc_check_override_common(item_from_build, name, override_value)
                    override_attribute_errors[name] = False
                except ConfigException as ex:
                    if name not in override_attribute_errors:
                        override_attribute_errors[name] = str(ex)

                existing_attr = item_from_build._mc_attributes.get(override_key)
                if existing_attr:
                    item_from_build._mc_attributes[override_key] = existing_attr.override(override_value, selected_env)
                    continue

                item_from_build._mc_attributes[override_key] = override_value

        def from_build_to_parent(build_key, build_value, clone):
            """Copy/Merge all items/attributes defined in 'build' into parent object"""
            parent = self._mc_contained_in
            parent_attributes, _ = parent._mc_get_attributes_where()

            # Merge repeatable items into parent
            if isinstance(build_value, Repeatable):
                for rep_key, rep_value in build_value.items():
                    rep_value._mc_contained_in = parent
                    set_my_attributes_on_item_from_build(rep_value, clone=clone)

                    if isinstance(parent, _ConfigBuilder):
                        ur = UserRepeatable()
                        ur.contained_in = self
                        parent_attributes.setdefault(build_key, ur)
                    elif build_key not in parent.__class__._mc_deco_nested_repeatables:
                        raise ConfigException(rep_value._error_msg_not_repeatable_in_container(build_key, parent))

                    if rep_key in parent_attributes[build_key]:
                        # TODO: Silently skip insert instead (optional warning)?
                        raise ConfigException("Nested repeatable from 'build', key: " + repr(rep_key) + ", value: " + repr(rep_value) +
                                              " overwrites existing entry in parent: " + repr(parent))

                    parent_attributes[build_key][rep_key] = rep_value

                parent_attributes[build_key]._mc_is_excluded |= self._mc_is_excluded
                return

            if isinstance(build_value, _ConfigItem):
                build_value._mc_contained_in = parent
                set_my_attributes_on_item_from_build(build_value, clone=clone)

            # Set non-repeatable items on parent
            # TODO validation
            parent_attributes[build_key] = build_value if not self._mc_is_excluded else Excluded(build_value)

        def move_items_around():
            # Loop over attributes created in build
            # Items and attributes created in 'build' goes into parent
            # Attributes/Items on builder are copied to items created in build
            clone = False
            for build_key, build_value in self._mc_build_attributes.items():
                from_build_to_parent(build_key, build_value, clone)
                clone = True

        move_items_around()

        errors = [err_value for err_value in override_attribute_errors.values() if err_value]
        if errors:
            num_errors = len(errors)
            sing_plu = "errors were" if num_errors > 1 else "error was"
            raise ConfigException('The following ' + sing_plu + ' found when setting values on items from build()\n  ' + '\n  '.join(errors))

    def what_built(self):
        return OrderedDict([(key, attr._mc_value()) for key, attr in self._mc_build_attributes.items()])

    @classmethod
    def named_as(cls):
        return super(_ConfigBuilder, cls).named_as() + '.builder.' + repr(_ConfigBuilder._num)

# Copyright (c) 2012-2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, traceback
from collections import OrderedDict
import json

from .envs import EnvFactory, MissingValueEnvException, AmbiguousEnvException, EnvException, NO_ENV
from .values import MC_NO_VALUE, MC_TODO, MC_REQUIRED, McTodoHandling
from .attribute import _McAttribute, Where

major_version = sys.version_info[0]
if major_version < 3:
    from .property_wrapper_py2 import _McPropertyWrapper  # pylint: disable=import-error
else:
    from .property_wrapper_py3 import _McPropertyWrapper

from .repeatable import RepeatableDict
from .config_errors import ConfigAttributeError, ConfigExcludedAttributeError, ConfigException, ConfigApiException, InvalidUsageException
from .config_errors import caller_file_line, find_user_file_line, _line_msg, _error_msg, _warning_msg, not_repeatable_in_parent_msg, repeatable_in_parent_msg
from .json_output import ConfigItemEncoder, _mc_filter_out_keys, _mc_identification_msg_str
from .bases import get_bases
from . import typecheck


class _McExcludedException(Exception):
    pass


_mc_debug_enabled = False
def _mc_debug(*args):
    if _mc_debug_enabled:
        print(*args)


class _ConfigBase(object):
    _mc_last_item = None
    _mc_hierarchy = []
    _mc_deco_named_as = None
    _mc_deco_required = ()
    _mc_deco_nested_repeatables = ()

    @classmethod
    def _mc_debug_hierarchy(cls, msg):
        _mc_debug(msg, cls, '_mc_hierarchy: {}'.format([id(item) for item in cls._mc_hierarchy]))

    def _mc_error_msg(self, message):
        self._mc_num_errors += 1
        return _error_msg(message)

    def _mc_warning_msg(self, msg):
        self._mc_root._mc_num_warnings += 1
        return _warning_msg(msg)

    def _mc_raise_errors(self, already="\nCheck already printed error messages"):
        nerr = self._mc_num_errors
        ww, err = ('were', 'errors') if nerr > 1 else ('was', 'error')
        msg = "There {ww} {nerr} {err} when defining item: {self}{already}.".format(ww=ww, nerr=nerr, err=err, self=self, already=already)
        raise ConfigException(msg, is_summary = True)

    def _mc_print_error(self, message, file_name, line_num):
        """Print a single message preceeded by file:line"""
        print(_line_msg(file_name=file_name, line_num=line_num) + '\n' + self._mc_error_msg(message), file=sys.stderr)

    def _mc_print_error_caller(self, message, mc_error_info_up_level):
        """Print a single message preceeded by file:line"""
        file_name, line_num = caller_file_line(up_level=mc_error_info_up_level + 1)
        print(_line_msg(file_name=file_name, line_num=line_num) + '\n' + self._mc_error_msg(message), file=sys.stderr)
        if self._mc_where == Where.FROZEN:
            # We need to raise now, self is already frozen so error count will not be checked later
            self._mc_raise_errors()

    def _mc_print_warning(self, message, file_name, line_num):
        """Print a single message preceeded by file:line"""
        print(_line_msg(file_name=file_name, line_num=line_num) + '\n' + self._mc_warning_msg(message), file=sys.stderr)

    def _mc_print_value_error_msg(self, attr_name, value, mc_caller_file_name, mc_caller_line_num):
        """Print message about invalid or missing value"""
        cr = self._mc_root
        current_env = cr._mc_env

        value_msg = ' ' + repr(value) if value != MC_NO_VALUE else ''
        msg = "Attribute: '{attr}'{value_msg} did not receive a value for env {env}".format(attr=attr_name, value_msg=value_msg, env=current_env)
        if value == MC_TODO:
            cr._mc_todo_msgs[current_env].append((msg, mc_caller_file_name, mc_caller_line_num))
            todo_handling =  cr._mc_todo_handling_allowed if current_env.allow_todo else cr._mc_todo_handling_other
            if todo_handling is McTodoHandling.SILENT:
                return
            if todo_handling is McTodoHandling.WARNING:
                self._mc_print_warning(msg, file_name=mc_caller_file_name, line_num=mc_caller_line_num)
                return

        self._mc_print_error(msg, file_name=mc_caller_file_name, line_num=mc_caller_line_num)

    def _mc_print_no_proper_value_error_msg(self, mc_error_info_up_level):
        msg = "The following attribues defined earlier never received a proper value for {env}:".format(env=self.env)
        if mc_error_info_up_level is not None:
            mc_caller_file_name, mc_caller_line_num = find_user_file_line(up_level_start=mc_error_info_up_level + 1)
            print(_line_msg(file_name=mc_caller_file_name, line_num=mc_caller_line_num), file=sys.stderr)
        print(_error_msg(msg), file=sys.stderr)

        for attr_name, info in self._mc_attributes_to_check.items():
            where_from, value_file_name, value_line_num = info  # TODO, 'use where'_from in error message
            value = getattr(self, attr_name)
            self._mc_print_value_error_msg(attr_name, value, value_file_name, value_line_num)

    @classmethod
    def named_as(cls):
        """Return the named_as property set by the @named_as decorator"""
        return cls._mc_deco_named_as or cls.__name__

    def json(self, compact=False, sort_attributes=False, property_methods=True, builders=False, skipkeys=True, warn_nesting=None, show_all_envs=False, depth=None):
        """Create json representation of configuration.

        The mc_json_filter and mc_json_fallback arguments to `mc_config` also influence the output.

        Arguments:
            compact (bool): Set compact to true if dumping for easier human readable output, false for machine readable output.
            sort_attributes (bool): Sort sttributes by name. Sort dir() entries by name.
            property_methods (bool): call @property methods and insert values in output, including a comment that the value is calculated.
            builders (bool): Include ConfigBuilder items in json.
            skipkeys (bool: Passed to json.dumps.
            show_all_envs (bool): Display attribute values for all envs in a single dump. Without this only the values for the current env is displayed.
            depth (int): The number of levels of child objects to dump. None means all.
        """

        cr = self._mc_root

        filter_callable = cr._mc_json_filter
        fallback_callable = cr._mc_json_fallback
        encoder = ConfigItemEncoder(
            filter_callable=filter_callable, fallback_callable=fallback_callable,
            compact=compact, sort_attributes=sort_attributes, property_methods=property_methods,
            builders=builders, warn_nesting=warn_nesting,
            multiconf_base_type=_ConfigBase, multiconf_builder_type=_ConfigBuilder,
            multiconf_property_wrapper_type=_McPropertyWrapper,
            show_all_envs=show_all_envs,
            depth=depth)
        try:
            # TODO: Thread safety
            orig_env = cr._mc_env
            if show_all_envs:
                cr._mc_env = NO_ENV

            # python3 doesn't need  separators=(',', ': ')
            json_str = json.dumps(self, skipkeys=skipkeys, default=encoder, check_circular=False, sort_keys=False, indent=4, separators=(',', ': '))
            cr._mc_json_errors = encoder.num_errors
            return json_str
        finally:
            cr._mc_env = orig_env

    def _mc_excl_repr(self):
        return "Excluded: " + repr(type(self))

    def __repr__(self):
        if self:
            # Don't call property methods in repr?, it is too dangerous, leading to double errors in case of incorrect user implemented property methods
            return self.json(compact=True, property_methods=True, builders=True, depth=None)
        return self._mc_excl_repr()

    def num_json_errors(self):
        """
        Returns number of errors encountered when generating json
        Return 0 if json() has not been called
        """

        return self._mc_root._mc_json_errors

    def mc_init(self):
        """This is a user defined callback method.

        This is called at the exit from a with statement.
        May be used for e.g. setting default values based on other properties or cross validation of different properties
        """

    def mc_validate(self):
        """This is a user defined callback method.

        This method is called once for each item for each env after other initialization has been and all items are created.
        May be used for e.g. setting default values based on other properties or cross validation of different properties.
        It is preferable to use mc_init when possible as mc_init generally results in more precise error messages, and ensures that an
        item is fully defined when the 'with' statement is exited.
        """

    def mc_post_validate(self):
        """This is a user defined callback method.

        This method is called once for each item after other initialization has been done for all envs, so cross env checking and cross
        object/attribute checking is possible. Since it is called once, and not per env, there is no current env and regular attribute
        access is not possible, instead the item.getattr(name, env) method must be used to get attribute values for different envs.

        This makes it possible to checks like the following:

        assert item.getattr('mem_size', pprd) == item.getattr('mem_size', prod) <= item.getattr('mem_size', tst1)

        Note that careful consideration should be taken when using env names explicitly (as above) when implementing a configuration
        object model, since this will force all configurations to define those envs.

        Note that no modifications can be done in this method!
        """

    def __bool__(self):
        return not (self._mc_root._mc_env.mask & self._mc_excluded)

    # Python2 compatibility
    __nonzero__ = __bool__

    if major_version < 3:
        def _mc_dir_entries(self):
            return dir(self)

    if major_version >= 3:  # This should have been an else, but that makes it difficult to do the coverage
        def _mc_dir_entries(self):
            dir_set = set(dir(self))
            mc_attr_keys_set = set(self._mc_attributes.keys())
            return dir_set.difference(mc_attr_keys_set.difference(object.__dir__(self)))
            # return [key for key in dir(self) if key not in self._mc_attributes.keys() or key in object.__dir__(self)]

        def __dir__(self):
            return object.__dir__(self) + list(self._mc_attributes.keys())

    def _mc_exists_in_given_env(self, env):
        env_mask = env.mask
        if env_mask & self._mc_excluded:
            return False
        return self._mc_handled_env_bits & env_mask

    def _mc_exists_in_env(self):
        """Note: This always returns True when the onfig is not fully loaded"""
        cr = self._mc_root
        if not cr._mc_config_loaded:
            return True
        env_mask = cr._mc_env.mask
        if env_mask & self._mc_excluded:
            return False
        return self._mc_handled_env_bits & env_mask or env_mask == 0

    def _mc_freeze(self, mc_error_info_up_level):
        if not self:
            self._mc_where = Where.FROZEN
            return

        if self._mc_num_errors:
            self._mc_raise_errors()

        self._mc_where = Where.IN_MC_INIT
        must_pop = False
        if self.__class__._mc_hierarchy[-1] != self:
            must_pop = True
            self.__class__._mc_hierarchy.append(self)

        # Call user 'mc_init' callback
        self.mc_init()

        if self._mc_attributes_to_check and self.mc_validate.__code__ is _ConfigBase.mc_validate.__code__:
            self._mc_print_no_proper_value_error_msg(mc_error_info_up_level)

        if isinstance(self, _ConfigBuilder):
            self._mc_builder_freeze()

        if must_pop:
            self.__class__._mc_hierarchy.pop()

        missing_req = []
        for req in self._mc_deco_required:
            if not req in self._mc_items:
                missing_req.append(req)
        if missing_req:
            if mc_error_info_up_level is not None:
                mc_caller_file_name, mc_caller_line_num = find_user_file_line(up_level_start=mc_error_info_up_level)
                print(_line_msg(file_name=mc_caller_file_name, line_num=mc_caller_line_num), file=sys.stderr)
            print(self._mc_error_msg("Missing '@required' items: {}".format(missing_req)), file=sys.stderr)

        if self._mc_num_errors:
            self._mc_raise_errors()
        self._mc_where = Where.FROZEN

    def _mc_call_mc_validate_recursively(self, env):
        """Call the user defined 'mc_validate' methods on all items"""
        if not self._mc_exists_in_given_env(env):
            return

        self._mc_where = Where.NOWHERE
        self.mc_validate()
        if self._mc_attributes_to_check:
            self._mc_print_no_proper_value_error_msg(None)
        if self._mc_num_errors:
            self._mc_raise_errors()
        self._mc_where = Where.FROZEN

        for child_item in self._mc_items.values():
            child_item._mc_call_mc_validate_recursively(env)

    def _mc_validate_properties_recursively(self, env):
        """Validate that @property methods can be called without error"""
        if not self._mc_exists_in_given_env(env):
            return

        cr = self._mc_root

        try:
            dir_entries = dir(self)
        except Exception as ex:
            dir_entries = ()
            cr._mc_num_property_errors += 1
            print(_error_msg("Calling dir() failed while validating @properties for {env}.".format(env=env)), file=sys.stderr)
            traceback.print_exception(*sys.exc_info())

        for key in dir_entries:
            if key.startswith('_') or key in _mc_filter_out_keys or key in self._mc_items:
                continue

            try:
                val = getattr(self, key)
            except InvalidUsageException:
                cr._mc_num_invalid_property_usage += 1
                # print(_error_msg("InvalidUsageException trying to validate @property '{prop_name}' in {env}.".format(prop_name=key, env=env)), file=sys.stderr)
                # traceback.print_exception(*sys.exc_info())
            except Exception as ex:
                cr._mc_num_property_errors += 1
                print(_error_msg("Exception validating @property '{prop_name}' on item {item} in {env}.".format(
                    prop_name=key, item=_mc_identification_msg_str(self), env=env)), file=sys.stderr)
                traceback.print_exception(*sys.exc_info())

        for child_item in self._mc_items.values():
            child_item._mc_validate_properties_recursively(env)

    @property
    def num_invalid_property_usage(self):
        """Returns number of 'InvalidUsageException' s encountered when validating @property methods
        Returns 0 if 'mc_config' was called with validate_properties=False.
        """

        return self._mc_root._mc_num_invalid_property_usage

    def _mc_call_mc_post_validate_recursively(self):
        """Call the user defined 'mc_post_validate' methods on all items"""

        self._mc_where = Where.NOWHERE
        self.mc_post_validate()
        self._mc_where = Where.FROZEN

        for child_item in self._mc_items.values():
            child_item._mc_call_mc_post_validate_recursively()

    def __enter__(self):
        self._mc_where = Where.IN_WITH if self._mc_where != Where.IN_RE_INIT else Where.IN_RE_WITH
        self.__class__._mc_hierarchy.append(self)
        # self.__class__._mc_debug_hierarchy('_ConfigBase.__enter__')
        return self

    @staticmethod
    def _update_mc_excluded_recursively(parent, mc_excluded_mask):
        for child_item in parent._mc_items.values():
            if isinstance(child_item, RepeatableDict):
                for child_item in child_item.values():
                    child_item._mc_excluded |= mc_excluded_mask
                    _ConfigBase._update_mc_excluded_recursively(child_item, mc_excluded_mask)
                return

            child_item._mc_excluded |= mc_excluded_mask
            _ConfigBase._update_mc_excluded_recursively(child_item, mc_excluded_mask)

    def __exit__(self, exc_type, value, traceback):
        if not exc_type:
            previous_item = _ConfigBase._mc_last_item
            if previous_item != self and previous_item != self._mc_contained_in and previous_item and previous_item._mc_where != Where.FROZEN:
                previous_item._mc_freeze(mc_error_info_up_level=1)

            self._mc_freeze(mc_error_info_up_level=1)
            self.__class__._mc_hierarchy.pop()
            return None

        # self.__class__._mc_debug_hierarchy('_ConfigBase.__exit__')
        if exc_type is _McExcludedException:
            # We need to update _mc_excluded mask on all children which may have been skipped
            _ConfigBase._update_mc_excluded_recursively(self, self._mc_excluded)
            self.__class__._mc_hierarchy.pop()
            return True

    def _mc_setattr(self, current_env, attr_name, value, from_eg, mc_overwrite_property, mc_set_unknown, mc_force, mc_error_info_up_level, is_assign=False):
        """Common code for assignment and item.setattr"""

        try:
            real_attr = None
            try:
                real_attr = object.__getattribute__(self, attr_name)
            except AttributeError:
                raise
            except Exception as ex:
                pass

            if attr_name in self._mc_items:
                if isinstance(real_attr, RepeatableDict):
                    msg = "'{name}' is already defined as a nested-repeatable and may not be replaced with an attribute.".format(name=attr_name)
                else:
                    msg = "'{name}' {typ} is already defined and may not be replaced with an attribute.".format(name=attr_name, typ=type(real_attr))
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

            for cls in get_bases(object.__getattribute__(self, '__class__')):
                try:
                    prop = object.__getattribute__(cls, attr_name)
                except AttributeError:
                    prop = None
                    continue

                if isinstance(prop, _McPropertyWrapper):
                    break

                if not mc_overwrite_property:
                    base_msg = "The attribute '{name}' clashes with a @property or method".format(name=attr_name)
                    msg = base_msg + " and 'mc_overwrite_property' is False."
                    if is_assign:
                        msg = base_msg + ". Use item.setattr with mc_overwrite_property=True if overwrite intended."
                    self._mc_print_error_caller(msg, mc_error_info_up_level)
                    return

                if isinstance(prop, property):
                    setattr(cls, attr_name, _McPropertyWrapper(attr_name, prop))
                    break

                msg = "'mc_overwrite_property' specified but existing attribute '{name}' with value '{value}' is not a @property.".format(
                    name=attr_name, value=prop)
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

        except AttributeError:
            if mc_overwrite_property:
                msg = "'mc_overwrite_property' is True but no property named '{name}' exists.".format(name=attr_name)
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

            prop = None

        env_attr = self._mc_attributes.get(attr_name)
        if env_attr is None:
            if self._mc_where not in (Where.IN_INIT, Where.IN_RE_INIT) and not mc_set_unknown and not prop:
                msg = "All attributes must be defined in __init__ or set with 'mc_set_unknown'. " + \
                      "Attempting to set attribute '{attr_name}' which does not exist.".format(attr_name=attr_name)
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

            env_attr = _McAttribute()
            self._mc_attributes[attr_name] = env_attr
            old_value = MC_NO_VALUE
        else:
            try:
                old_value = env_attr.env_values[current_env]

                if mc_set_unknown:
                    msg = "Attempting to use 'mc_set_unknown' to set attribute '{attr_name}' which already exists.".format(attr_name=attr_name)
                    self._mc_print_error_caller(msg, mc_error_info_up_level)
                    return

                if not mc_force:
                    if self._mc_where == Where.IN_MC_INIT and env_attr.where_from != Where.IN_MC_INIT and old_value not in (MC_NO_VALUE, MC_REQUIRED):
                        # In mc_init we will not overwrite a proper value set previously unless the eg is more specific than the previous one or mc_force is used
                        if from_eg not in env_attr.from_eg or from_eg == env_attr.from_eg:
                            return

                    if self._mc_where == Where.IN_RE_INIT and env_attr.where_from != Where.IN_RE_INIT and old_value not in (MC_NO_VALUE, MC_REQUIRED):
                        # In mc_re_init we will not overwrite a proper value set previously unless the eg is more specific than the previous one or mc_force is used
                        if from_eg not in env_attr.from_eg or from_eg == env_attr.from_eg:
                            return

                    if self._mc_where == Where.IN_RE_WITH and env_attr.where_from == Where.IN_RE_WITH:
                        # Trying to set the same attribute again in with block
                        msg = "The attribute '{attr_name}' is already fully defined.".format(attr_name=attr_name)
                        self._mc_print_error_caller(msg, mc_error_info_up_level)
                        return

                    if self._mc_where == Where.IN_WITH and env_attr.where_from == Where.IN_WITH:
                        # Trying to set the same attribute again in with block
                        msg = "The attribute '{attr_name}' is already fully defined.".format(attr_name=attr_name)
                        self._mc_print_error_caller(msg, mc_error_info_up_level)
                        return

                    if env_attr.where_from == Where.FROZEN:
                        msg = "Trying to set attribute '{attr_name}'. ".format(attr_name=attr_name)
                        msg += "Setting attributes is not allowed after value has been used (in order to enforce derived value validity)."
                        self._mc_print_error_caller(msg, mc_error_info_up_level)
                        return

                    if self._mc_where == Where.FROZEN:
                        msg = "Trying to set attribute '{attr_name}'. ".format(attr_name=attr_name)
                        msg += "Setting attributes is not allowed after item is 'frozen' (with 'scope' is exited)."
                        self._mc_print_error_caller(msg, mc_error_info_up_level)  # Note: This always raises en exception

            except KeyError:
                old_value = MC_NO_VALUE

        if value == MC_NO_VALUE:
            if old_value not in (MC_NO_VALUE, MC_TODO, MC_REQUIRED) or prop:
                return
            value = old_value

        if value != MC_NO_VALUE:
            # We have a value for the env which is more specific than any previous value
            env_attr.set(current_env, value, self._mc_where, from_eg)

        if value not in (MC_NO_VALUE, MC_TODO, MC_REQUIRED):
            if self._mc_root._mc_do_type_check:
                type_msg = typecheck.type_check(self, attr_name, value)
                if type_msg:
                    self._mc_print_error_caller(type_msg, mc_error_info_up_level)
                    return

            if self._mc_attributes_to_check:
                self._mc_attributes_to_check.pop(attr_name, None)
            return

        if self._mc_where == Where.IN_INIT or not self:
            if value == MC_NO_VALUE:
                env_attr.set(current_env, value, self._mc_where, from_eg)

            # This is not an error now, as we allow partial set in __init__ and setting value to MC_REQUIRED in 'with' block
            # to postpone check until after 'mc_init', but we must remember to test later if the attribute has been set.
            mc_caller_file_name, mc_caller_line_num = caller_file_line(up_level=mc_error_info_up_level)
            if self._mc_attributes_to_check is None:
                self._mc_attributes_to_check = OrderedDict()
            self._mc_attributes_to_check[attr_name] = (self._mc_where, mc_caller_file_name, mc_caller_line_num)
            return

        # We will report the error now, so pop from check list
        if self._mc_attributes_to_check:
            self._mc_attributes_to_check.pop(attr_name, None)

        mc_caller_file_name, mc_caller_line_num = caller_file_line(up_level=mc_error_info_up_level)
        self._mc_print_value_error_msg(attr_name, value, mc_caller_file_name, mc_caller_line_num)

    def _mc_setattr_disabled(self, current_env, attr_name, value, from_eg, mc_overwrite_property, mc_set_unknown, mc_force, mc_error_info_up_level, is_assign=False):
        """Common code for assignment and item.setattr to disable attribute modification after config is loaded"""
        msg = "Trying to set attribute '{}'. Setting attributes is not allowed after configuration is loaded (in order to enforce derived value validity)."
        raise ConfigApiException(msg.format(attr_name))

    _mc_setattr_real = _mc_setattr  # Keep a reference to the real _mc_setattr

    def __setattr__(self, attr_name, value):
        if attr_name[0] == '_':
            object.__setattr__(self, attr_name, value)
            return

        cr = self._mc_root
        self._mc_setattr(cr._mc_env, attr_name, value, cr._mc_env_factory.default, False, False, False, mc_error_info_up_level=3, is_assign=True)

    def setattr(self, attr_name, mc_overwrite_property=False, mc_set_unknown=False, mc_force=False, mc_error_info_up_level=2, **env_values):
        """Set env specific values for an attribute.

        Arguments:
            attr_name (str): The name of the attribute to set.
            mc_overwrite_property (bool=False): Setting this to True allows overwriting a @property method with env specific values.
                Any env for which the @property is not overridden will still get the value of the @property method.
            mc_set_unknown (bool=False): This allows setting a property which was not defined in the __init__ method.
            mc_force (bool=False): Force the value of the property regardless of the normal multiconf rules for assigning values.
                This should be used with care, as normal validation is disabled. Using this could be a sign of bad configuration/modelling.
            mc_error_info_up_level (int): Only for use if a class overrides setattr. You must add 1 each time it is overridden.
                This is used for calculating the file:line info in case of errors.
            **env_values (dict[env-name]->value): The env specific values to assign. Arg names must be valid env names from the EnvFactory used to
                create the configuration.
        """

        if attr_name[0] == '_':
            msg = "Trying to set attribute '{}' on a config item. ".format(attr_name)
            msg += ("Atributes starting with '_mc' are reserved for multiconf internal usage." if attr_name.startswith('_mc') else
                    "Atributes starting with '_' cannot be set using item.setattr. Use assignment instead.")
            self._mc_print_error_caller(msg, mc_error_info_up_level)
            return

        if not env_values:
            msg = "No Env or EnvGroup names specified."
            self._mc_print_error_caller(msg, mc_error_info_up_level)
            return

        cr = self._mc_root
        env_factory = cr._mc_env_factory

        if cr._mc_check_unknown:
            # Check that there are no undefined eg names specified
            undefined = []
            for eg_name in env_values:
                try:
                    env_factory.env_or_group_from_name(eg_name)
                except EnvException:
                    undefined.append(eg_name)
            if undefined:
                msg = "No such Env or EnvGroup: " + repr(undefined[0])  # TODO list
                self._mc_print_error_caller(msg, mc_error_info_up_level)

        current_env = cr._mc_env
        try:
            value, eg = env_factory._mc_resolve_env_group_value(current_env, env_values)
            self._mc_setattr(current_env, attr_name, value, eg, mc_overwrite_property, mc_set_unknown, mc_force, mc_error_info_up_level + 1)
            return
        except MissingValueEnvException:
            self._mc_setattr(current_env, attr_name, MC_NO_VALUE, env_factory.eg_none, mc_overwrite_property, mc_set_unknown, False, mc_error_info_up_level + 1)
            return
        except AmbiguousEnvException as ex:
            msg = "Value for {env} is specified more than once, with no single most specific group or direct env:".format(env=current_env)
            for eg in ex.ambiguous:
                value = env_values[eg.name]
                msg += "\nvalue: " + repr(value) + ", from: " + repr(eg)
            self._mc_print_error_caller(msg, mc_error_info_up_level)

    def __getattr__(self, attr_name):
        # Only called if self.<attr_name> is not found
        if not self and self._mc_root._mc_config_loaded:
            raise ConfigExcludedAttributeError(self, attr_name, self._mc_root._mc_env)

        try:
            attr = self._mc_attributes[attr_name]
            attr.where_from = Where.FROZEN
            return attr.env_values[self._mc_root._mc_env]
        except KeyError:
            if self._mc_root._mc_env is not NO_ENV or attr_name not in self._mc_attributes:
                if not self:
                    raise ConfigExcludedAttributeError(self, attr_name, self._mc_root._mc_env)
                raise ConfigAttributeError(self, attr_name)

            msg = "Trying to access attribute '{}'. "
            msg += "Item.attribute access is not allowed in 'mc_post_validate' as there is no current env, use: item.getattr(attr_name, env)"
            raise ConfigApiException(msg.format(attr_name))

    def getattr(self, attr_name, env):
        """Get an attribute value for any env."""
        if env.mask & self._mc_excluded and self._mc_root._mc_config_loaded:
            raise ConfigExcludedAttributeError(self, attr_name, env)

        try:
            attr = self._mc_attributes[attr_name]
            attr.where_from = Where.FROZEN
            return attr.env_values[env]
        except KeyError:
            prop = object.__getattribute__(self.__class__, attr_name)
            try:
                # TODO: Thread safety
                orig_env = self._mc_root._mc_env
                self._mc_root._mc_env = env
                if isinstance(prop, _McPropertyWrapper):
                    return prop.prop.__get__(self, type(self))
                return getattr(self, attr_name)
            finally:
                self._mc_root._mc_env = orig_env

    def items(self):
        for key, item in self._mc_items.items():
            if not item or isinstance(item, _ConfigBuilder):
                continue
            yield key, item

    @property
    def env(self):
        return self._mc_root._mc_env

    @property
    def env_factory(self):
        return self._mc_root._mc_env_factory

    @property
    def root_conf(self):
        return self._mc_root

    @property
    def contained_in(self):
        mc_contained_in = self._mc_contained_in
        child = self
        while isinstance(mc_contained_in, _ConfigBuilder):
            if mc_contained_in._mc_where == Where.IN_WITH and not child._mc_where == Where.IN_MC_BUILD:
                msg = "Use of 'contained_in' in not allowed in object while under the 'with statement of a ConfigBuilder. The final containment is still unknown."
                self._mc_print_error_caller(msg, mc_error_info_up_level=2)
                raise ConfigApiException(msg)
            mc_contained_in = mc_contained_in._mc_contained_in
            child = child._mc_contained_in
        return mc_contained_in

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

    def find_attribute_or_none(self, name):
        """Find first occurence of attribute or child item 'name', by searching backwards towards root_conf, starting with self."""
        contained_in = self
        while contained_in:
            attr = contained_in._mc_attributes.get(name)
            if attr:
                return getattr(contained_in, name)
            item = contained_in._mc_items.get(name)
            if item:
                return item
            contained_in = contained_in.contained_in
        return None

    def find_attribute(self, name):
        """Find first occurence of attribute or child item 'name', by searching backwards towards root_conf, starting with self."""
        contained_in = self
        while contained_in:
            attr = contained_in._mc_attributes.get(name)
            if attr:
                return getattr(contained_in, name)
            item = contained_in._mc_items.get(name)
            if item:
                return item
            contained_in = contained_in.contained_in

        # Error, create error message
        contained_in = self
        contained_in_names = []
        while contained_in:
            contained_in_names.append(contained_in.named_as())
            contained_in = contained_in.contained_in

        msg = ': Could not find an attribute named: ' + repr(name) + ' in hieracy with names: ' + repr(contained_in_names)
        raise ConfigException("Searching from: " + repr(type(self)) + msg)


class _ConfigItemBase(_ConfigBase):
    def __init__(self, mc_include=None, mc_exclude=None):
        previous_item = self.__class__._mc_last_item
        if previous_item != self._mc_contained_in and previous_item and previous_item._mc_where != Where.FROZEN and previous_item is not self:
            try:
                previous_item._mc_freeze(mc_error_info_up_level=None)
            except Exception as ex:
                print("Exception validating previously defined object -", file=sys.stderr)
                print("  type:", type(previous_item), file=sys.stderr)
                print("Stack trace will be misleading!", file=sys.stderr)
                print("This happens if there is an error (e.g. attributes with value MC_REQUIRED or missing '@required' ConfigItems) in", file=sys.stderr)
                print("an object that was not directly enclosed in a with statement. Objects that are not arguments to a with", file=sys.stderr)
                print("statement will not be validated until the next ConfigItem is declared or an outer with statement is exited.", file=sys.stderr)
                raise

        _ConfigBase._mc_last_item = self

        if not self._mc_contained_in:
            self._mc_excluded |= self._mc_root._mc_env.mask
            raise _McExcludedException()

        if mc_include or mc_exclude:
            self._mc_select_envs(mc_include, mc_exclude)

    def _mc_select_envs(self, include, exclude):
        """Calculate whether to include or exclude item in env."""
        try:
            selected = self._mc_root._mc_env_factory._mc_select_env_list(self.env, exclude or [], include or [])
        except AmbiguousEnvException as ex:
            msg = "{env} is specified in both include and exclude, with no single most specific group or direct env:"
            msg += "\n - from exclude: {egx}"
            msg += "\n - from include: {egi}"
            ex = ConfigException(msg.format(env=self.env, egx=ex.ambiguous[0], egi=ex.ambiguous[1]))
            ex.__suppress_context__ = True
            raise ex

        if selected == 1 or (selected is None and include):
            self._mc_excluded |= self._mc_root._mc_env.mask
            return True

        return False

    def mc_select_envs(self, include=None, exclude=None, mc_error_info_up_level=2):
        """Calculate whether item should be included or excluded.

        This should be the first statement in the 'with' block
        If item is excluded, then the 'with' block, is skipped and no multiconf validations are done for item or contained items.

        Arguments:
            include (list[env]): List of Envs/EngGroups for which to include this item (and contained items)
            exclude (list[env]): List of Envs/EngGroups for which to exclude this item (and contained items)
            mc_error_info_up_level (int): Only for use if a class overrides mc_select_envs. You must add 1 each time it is overridden.
                This is used for calculating the file:line in case of ambiguous include/exclude lists.

        The inclusion/exclusion is done on a 'most specific' basis -
         - If an item is excluded by an EnvGroup specification but included by a more specific EnvGroup (or Env), then it will be included.
         - If an item is included by an EnvGroup specification but excluded by a more specific EnvGroup (or Env), then it will be excluded.
        """

        try:
            if self._mc_select_envs(include, exclude):
                raise _McExcludedException()
        except ConfigException as ex:
            self._mc_print_error_caller(str(ex), mc_error_info_up_level)

    def _mc_get_repeatable(self, repeatable_class_key, repeatable_cls_or_dict):
        """Return repeatable if item has repeatable with 'repeatable_class_key', if not raise an exception."""
        if repeatable_class_key in self.__class__._mc_deco_nested_repeatables:
            return object.__getattribute__(self, repeatable_class_key)

        if isinstance(repeatable_cls_or_dict, RepeatableDict):
            # Get class of first item for error message
            for item in repeatable_cls_or_dict.values():  # pragma: no branch
                repeatable_cls_or_dict = type(item)
                break

        msg = not_repeatable_in_parent_msg.format(
            repeatable_cls_key=repeatable_class_key, repeatable_cls=repeatable_cls_or_dict, ci_named_as=self.named_as(), ci_cls=type(self))
        raise ConfigException(msg)


class ConfigItem(_ConfigItemBase):
    """Base class for config items."""

    def __new__(cls, *init_args, **init_kwargs):
        # cls._mc_debug_hierarchy('ConfigItem.__new__')
        _mc_contained_in = cls._mc_hierarchy[-1]

        # Find the first parent which is not a builder if we are in the mc_build method of a builder
        contained_in = _mc_contained_in
        while contained_in._mc_where == Where.IN_MC_BUILD:
            contained_in = contained_in._mc_contained_in

        name = cls.named_as()

        try:
            self = object.__getattribute__(contained_in, name)
            if self._mc_handled_env_bits & self._mc_root._mc_env.mask:
                # We are trying to replace a non-repeatable object. In mc_init we ignore this.
                if contained_in._mc_where == Where.IN_MC_INIT:
                    self._mc_where = Where.IN_RE_INIT
                    return self
                raise ConfigException("Repeated non repeatable conf item: '{name}': {cls}".format(name=name, cls=cls))
            self._mc_handled_env_bits |= self._mc_root._mc_env.mask

            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0
            return self
        except AttributeError:
            self = super(ConfigItem, cls).__new__(cls)
            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0

            self._mc_attributes = OrderedDict()
            self._mc_attributes_to_check = None
            self._mc_items = OrderedDict()
            self._mc_contained_in = _mc_contained_in
            self._mc_root = contained_in._mc_root
            self._mc_excluded = 0

            for key in cls._mc_deco_nested_repeatables:
                od = RepeatableDict()
                self._mc_items[key] = od  # Needed to implement reliable 'items' method
                object.__setattr__(self, key, od)

            # Insert self in parent
            if name in contained_in.__class__._mc_deco_nested_repeatables:
                msg = repeatable_in_parent_msg.format(named_as=name, cls=cls, ci_item=contained_in)
                raise ConfigException(msg, is_fatal=True)

            if name in contained_in._mc_attributes:
                msg = "'{name}' is defined both as simple value and a contained item: {self}".format(name=name, self=self)
                raise ConfigException(msg, is_fatal=True)
            object.__setattr__(contained_in, name, self)
            contained_in._mc_items[name] = self  # Needed to implement reliable 'items' method

            self._mc_handled_env_bits = self._mc_root._mc_env.mask
            return self


class RepeatableConfigItem(_ConfigItemBase):
    """Base class for config items which may be repeated.

    RepeatableConfigItems will be stored in an OrderedDict using the key 'mc_key'.

    Args:
        mc_key (hashable): The key used to lookup the config item.
    """

    def __new__(cls, mc_key, *init_args, **init_kwargs):
        # cls._mc_debug_hierarchy('RepeatableConfigItem.__new__')
        _mc_contained_in = cls._mc_hierarchy[-1]

        # Find the first parent which is not a builder if we are in the mc_build method of a builder
        contained_in = _mc_contained_in
        while contained_in._mc_where == Where.IN_MC_BUILD:
            contained_in = contained_in._mc_contained_in

        repeatable = contained_in._mc_get_repeatable(cls.named_as(), cls)

        try:
            self = repeatable[mc_key]
            if self._mc_handled_env_bits & self._mc_root._mc_env.mask:
                # We are trying to replace an object with the same mc_key. In mc_init we ignore this.
                if contained_in._mc_where == Where.IN_MC_INIT:
                    self._mc_where = Where.IN_RE_INIT
                    return self
                build_msg = " from 'mc_build'" if _mc_contained_in._mc_where == Where.IN_MC_BUILD else ""
                raise ConfigException("Re-used key '{key}' in repeated item {cls}{build_msg} overwrites existing entry in parent:\n{ci}".format(
                    key=mc_key, cls=cls, build_msg=build_msg, ci=contained_in))
            self._mc_handled_env_bits |= self._mc_root._mc_env.mask

            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0
            return self
        except KeyError:
            self = super(RepeatableConfigItem, cls).__new__(cls)
            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0

            self._mc_attributes = OrderedDict()
            self._mc_attributes_to_check = None
            self._mc_items = OrderedDict()
            self._mc_contained_in = _mc_contained_in
            self._mc_root = contained_in._mc_root
            self._mc_excluded = 0

            for key in cls._mc_deco_nested_repeatables:
                od = RepeatableDict()
                self._mc_items[key] = od  # Needed to implement reliable 'items' method
                object.__setattr__(self, key, od)

            self._mc_handled_env_bits = self._mc_root._mc_env.mask

            # Insert self in repeatable
            repeatable[mc_key] = self
            return self

    def __init__(self, mc_key, mc_include=None, mc_exclude=None):
        # Overridden to accept 'mc_key'
        super(RepeatableConfigItem, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)

    @classmethod
    def named_as(cls):
        """Return the named_as property set by the @named_as decorator"""
        return cls._mc_deco_named_as or (cls.__name__ + 's')


class _ConfigBuilder(_ConfigItemBase):
    """Base class for 'builder' items which can create (a collection of) other items."""

    def __new__(cls, mc_key='default-builder', *init_args, **init_kwargs):
        # cls._mc_debug_hierarchy('_ConfigBuilder.__new__')
        _mc_contained_in = cls._mc_hierarchy[-1]

        # Find the first parent which is not a builder if we are in the mc_build method of a builder
        contained_in = _mc_contained_in
        while contained_in._mc_where == Where.IN_MC_BUILD:
            contained_in = contained_in._mc_contained_in

        private_key = cls.named_as() + ' ' + str(mc_key)

        try:
            self = contained_in._mc_items[private_key]
            if self._mc_handled_env_bits & self._mc_root._mc_env.mask:
                # We are trying to replace an object with the same mc_key. In mc_init we ignore this.
                if contained_in._mc_where == Where.IN_MC_INIT:
                    self._mc_where = Where.IN_RE_INIT
                    return self
                build_msg = " from 'mc_build'" if _mc_contained_in._mc_where == Where.IN_MC_BUILD else ""
                raise ConfigException("Re-used key '{key}' in repeated item {cls}{build_msg} overwrites existing entry in parent:\n{ci}".format(
                    key=mc_key, cls=cls, build_msg=build_msg, ci=contained_in))
            self._mc_handled_env_bits |= self._mc_root._mc_env.mask

            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0
            return self
        except KeyError:
            self = super(_ConfigBuilder, cls).__new__(cls)
            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0

            self._mc_attributes = OrderedDict()
            self._mc_attributes_to_check = None
            self._mc_items = OrderedDict()
            self._mc_contained_in = _mc_contained_in
            self._mc_root = contained_in._mc_root
            self._mc_excluded = 0

            self._mc_handled_env_bits = self._mc_root._mc_env.mask
            contained_in._mc_items[private_key] = self

            return self

    def __init__(self, mc_key='default-builder', mc_include=None, mc_exclude=None):
        # Overridden to accept 'mc_key'
        super(_ConfigBuilder, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)

    @classmethod
    def named_as(cls):
        """Try to generate a unique name"""
        return '_mc_ConfigBuilder_' + cls.__name__

    def _mc_get_repeatable(self, repeatable_class_key, repeatable_cls_or_dict):
        repeatable = getattr(self, repeatable_class_key, None)
        if repeatable:
            return repeatable

        repeatable = RepeatableDict()
        self._mc_items[repeatable_class_key] = repeatable
        object.__setattr__(self, repeatable_class_key, repeatable)
        return repeatable

    def _mc_builder_freeze(self):
        self._mc_where = Where.IN_MC_BUILD
        try:
            self.mc_build()
        except _McExcludedException:
            pass

        def insert(from_build, from_with_key, from_with):
            """Insert items from with statement (single or repeatable) in a single (non repeatable) item from mc_build."""
            if from_build._mc_contained_in is not self:
                return

            if isinstance(from_with, RepeatableDict):
                repeatable = from_build._mc_get_repeatable(from_with_key, from_with)
                for wi_key, wi in from_with.items():
                    pp = _ItemParentProxy(from_build, wi)
                    repeatable[wi_key] = pp
                return

            pp = _ItemParentProxy(from_build, from_with)
            from_build._mc_items[from_with_key] = pp
            object.__setattr__(from_build, from_with_key, pp)

        # Now set all items created in the 'with' block of the builder on the items created in the 'mc_build' method
        # Find the first parent which is not a builder if we are in the mc_build method of a builder
        contained_in = self._mc_contained_in
        while contained_in._mc_where == Where.IN_MC_BUILD:
            contained_in = contained_in._mc_contained_in

        for item_from_with_key, item_from_with in self.items():
            for item_from_build_key, item_from_build in contained_in.items():

                if isinstance(item_from_build, RepeatableDict):
                    for bi_key, bi in item_from_build.items():
                        insert(bi, item_from_with_key, item_from_with)
                        continue
                    continue

                insert(item_from_build, item_from_with_key, item_from_with)

        previous_item = _ConfigBase._mc_last_item
        if previous_item != self and previous_item != self._mc_contained_in and previous_item and previous_item._mc_where != Where.FROZEN:
            previous_item._mc_freeze(mc_error_info_up_level=1)

        self._mc_where = Where.NOWHERE


class _ItemParentProxy(object):
    """The purpose of this is to set the current '_mc_contained_in' when accessing an item created by a builder and assigned under mutiple parent items"""
    __slots__ = ('_mc_contained_in', '_mc_item')

    def __init__(self, ci, item):
        object.__setattr__(self, '_mc_contained_in', ci)
        object.__setattr__(self, '_mc_item', item)

        item._mc_excluded |= ci._mc_excluded

    def __getattribute__(self, name):
        if name in object.__getattribute__(self, '__slots__'):
            return object.__getattribute__(self, name)

        item = object.__getattribute__(self, '_mc_item')
        orig_ci = item._mc_contained_in
        item._mc_contained_in = object.__getattribute__(self, '_mc_contained_in')
        try:
            return getattr(item, name)
        finally:
            item._mc_contained_in = orig_ci

    def __setattr__(self, attr_name, value):
        if attr_name[0] == '_':
            object.__setattr__(self._mc_item, attr_name, value)
            return

        cr = self._mc_item._mc_root
        self._mc_item._mc_setattr(cr._mc_env, attr_name, value, cr._mc_env_factory.default, False, False, False, mc_error_info_up_level=3, is_assign=True)


class _ConfigRoot(_ConfigBase):
    def __init__(self, env_factory, mc_todo_handling_other, mc_todo_handling_allowed, mc_json_filter, mc_json_fallback, mc_do_type_check):
        self._mc_env_factory = env_factory
        self._mc_todo_handling_other = mc_todo_handling_other
        self._mc_todo_handling_allowed = mc_todo_handling_allowed
        self._mc_json_filter = mc_json_filter
        self._mc_json_fallback = mc_json_fallback
        self._mc_do_type_check = mc_do_type_check

        self._mc_where = Where.IN_INIT
        self._mc_num_errors = 0

        self._mc_todo_msgs = OrderedDict([(env, []) for env in env_factory.envs.values()])
        self._mc_attributes = OrderedDict()
        self._mc_attributes_to_check = None
        self._mc_items = OrderedDict()
        self._mc_contained_in = None
        self._mc_root = self
        self._mc_excluded = 0
        self._mc_handled_env_bits = 0
        self._mc_num_warnings = 0
        self._mc_config_result = {}
        self._mc_config_loaded = False
        self._mc_num_property_errors = 0
        self._mc_num_invalid_property_usage = 0

    @property
    def mc_config_result(self):
        return self._mc_config_result[self.env]

    def __bool__(self):
        return True

    __nonzero__ = __bool__


class _RootEnvProxy(object):
    """The purpose of this is to set the current env when accessing a configuration"""
    __slots__ = ('_mc_root', '_mc_env')

    def __init__(self, env, root_item):
        object.__setattr__(self, '_mc_env', env)
        object.__setattr__(self, '_mc_root', root_item)

    def __getattr__(self, name):
        cr = self._mc_root
        cr._mc_env = self._mc_env
        return getattr(cr, name)

    @property
    def env(self):
        return self._mc_env

    def __repr__(self):
        return repr(self._mc_root)


def mc_config(
        env_factory, error_next_env=False, validate_properties=True,
        mc_todo_handling_other=McTodoHandling.ERROR, mc_todo_handling_allowed=McTodoHandling.WARNING,
        mc_json_filter=None, mc_json_fallback=None, do_type_check=None):
    """Instantiate ConfigItem hierarchy for all Envs defined in 'env_factory'.

    Arguments:
        env_factory (EnvFactory): The EnvFactory defining the envs for which we instantiate the configuration.
        error_next_env (bool): If this is False, then no more envs will be instantiated after errors are found in an env.
            If True, then instantiation is attempted for all envs, but an exception is raised at the end in any envs could not
            be instantiated.

        mc_todo_handling_other (McTodoHandling): This specifies how to handl attributes set to MC_TODO for envs with 'allow_todo' False.
            The default is McTodoHandling.ERROR, causing an error message to be printed and the configuration to be considered invalid.
        mc_todo_handling_allowed (McTodoHandling): This specifies how to handle attributes set to MC_TODO for envs with 'allow_todo' True.
            The default is McTodoHandling.WARNING, causing a warning message to be printed but the configuration to be considered valid.

        mc_json_filter (func(obj, key, value)): User defined function for filtering objects in json output.
            - filter_callable is called for each key/value pair of attributes on each ConfigItem obj.
            - It must return a tuple of (key, value). If key is False, the key/value pair is removed from the json output

        mc_json_fallback (func(obj)): User defined function for handling objects not otherwise encoded in json output.
            - fallback_callable is called for objects that are not handled by the builtin encoder.
            - It must return a tupple (object, handled). If handled is True, the object must be encodable by the standard json encoder.

        do_type_check (bool): Do type checking of attributes based on typing annotations. Default is True for Pythonn 3.6.1+. Attempting
            to enable this for earlier Python versions will raise an exception.

            Type checking of attributes is done based on typing information from the __init__ signature. If an attribute exists with the same
            name as an __init__ argument with typing information, then the attribute must conform to that type. E.g.::

                class X(ConfigItem):
                    def __init__(self, a:int = MC_REQUIRED):
                        super(X).__init__()
                        self.a = a

            It will be checked that x.a is instance of int.
    """

    if not isinstance(env_factory, EnvFactory):
        msg = "'env_factory' arg must be instance of {ef_typ!r}; found type {got_typ!r}: {val!r}"
        raise ConfigException(msg.format(ef_typ=EnvFactory.__name__, got_typ=env_factory.__class__.__name__, val=env_factory))

    for _ in env_factory.envs:
        # There is at least one env
        break
    else:
        raise ConfigException("The specified 'env_factory' is empty. It must have at least one Env.")

    if not isinstance(mc_todo_handling_other, McTodoHandling):
        msg = "'mc_todo_handling_other' arg must be instance of {th_typ!r}; found type {got_typ!r}: {val!r}"
        raise ConfigException(msg.format(th_typ=McTodoHandling.__name__, got_typ=mc_todo_handling_other.__class__.__name__, val=mc_todo_handling_other))

    if not isinstance(mc_todo_handling_allowed, McTodoHandling):
        msg = "'mc_todo_handling_allowed' arg must be instance of {th_typ!r}; found type {got_typ!r}: {val!r}"
        raise ConfigException(msg.format(th_typ=McTodoHandling.__name__, got_typ=mc_todo_handling_allowed.__class__.__name__, val=mc_todo_handling_allowed))

    allow_type_check = major_version >= 3 and typecheck.typing_vcheck()
    if do_type_check:
        if not allow_type_check:
            raise ConfigException(typecheck.unsup_version_msg)
    else:
        do_type_check = do_type_check is None and allow_type_check

    def deco(conf_func):
        env_factory._mc_calc_env_group_order()
        # Create root object
        cr = _ConfigRoot(env_factory, mc_todo_handling_other, mc_todo_handling_allowed, mc_json_filter, mc_json_fallback, do_type_check)
        cr._mc_check_unknown = True

        # Make sure _mc_setattr is the real one if decorator is used multiple times
        _ConfigBase._mc_setattr = _ConfigBase._mc_setattr_real

        # Load envs
        error_envs = []
        for env in env_factory.envs.values():
            _mc_debug("\n==== Loading", env, "====")
            rp = _RootEnvProxy(env, cr)
            cr._mc_env = env
            del cr.__class__._mc_hierarchy[:]
            _ConfigBase._mc_last_item = None

            try:
                with cr:
                    res = conf_func(cr)
                cr._mc_handled_env_bits |= env.mask
                cr._mc_call_mc_validate_recursively(env)
                if validate_properties:
                    cr._mc_validate_properties_recursively(env)
                    if cr._mc_num_property_errors:
                        raise ConfigException("Error validating @property methods for {}".format(env))
            except ConfigException as ex:
                if not error_next_env or ex.is_fatal:
                    raise

                if not ex.is_summary:
                    traceback.print_exc(file=sys.stderr)
                else:
                    print(ex.__class__.__name__ + ':', ex, file=sys.stderr)
                print("Error in config for {} above.\n".format(env), file=sys.stderr)

                error_envs.append(env)
                continue

            cr._mc_check_unknown = False
            cr._mc_config_result[env] = res
            env_factory.root_proxies[env] = rp

        if error_envs:
            raise ConfigException("The following envs had errors {}".format(error_envs))

        # No modifications are allowed after this
        cr._mc_config_loaded = True
        _ConfigBase._mc_setattr = _ConfigBase._mc_setattr_disabled

        # Call mc_post_validate
        cr._mc_env = NO_ENV
        cr._mc_call_mc_post_validate_recursively()

    return deco

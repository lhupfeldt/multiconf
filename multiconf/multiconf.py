# Copyright (c) 2012-2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, abc, traceback
import json
import threading

from .thread_state import thread_local
from .envs import EnvFactory, Env, AmbiguousEnvException, EnvException, MC_NO_ENV
from .values import MC_NO_VALUE, MC_TODO, MC_REQUIRED, McTodoHandling
from .attribute import _McAttribute, _McAttributeAccessor, Where
from .property_wrapper import _McPropertyWrapper
from .repeatable import RepeatableDict
from .config_errors import ConfigException, ConfigApiException, InvalidUsageException, ConfigExcludedAttributeError, ConfigExcludedKeyError
from .config_errors import caller_file_line, find_user_file_line, _line_msg, _error_msg, _warning_msg, not_repeatable_in_parent_msg, repeatable_in_parent_msg
from .json_output import ConfigItemEncoder, _mc_filter_out_keys, _mc_identification_msg_str
from . import typecheck


class _McExcludedException(Exception):
    pass


_mc_debug_enabled = str(os.environ.get('MULTICONF_DEBUG')).lower() == 'true'
def _mc_debug(*args):
    if _mc_debug_enabled:
        print(*args)


class _ConfigBase():
    _mc_last_item = None
    _mc_in_build = None
    _mc_built_by = None
    _mc_hierarchy = []
    _mc_deco_named_as = None
    _mc_deco_required = ()
    _mc_deco_nested_repeatables = ()

    @classmethod
    def _mc_debug_hierarchy(cls, msg):
        _mc_debug(
            msg,
            cls if not isinstance(cls, _ConfigBase) else (type(cls), id(cls)),
            '_mc_hierarchy: {}'.format([id(item) for item in cls._mc_hierarchy]))

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
        raise ConfigException(msg, is_summary=True)

    def _mc_print_error(self, message, file_name, line_num):
        """Print a single message preceded by file:line"""
        print(_line_msg(file_name=file_name, line_num=line_num) + '\n' + self._mc_error_msg(message), file=sys.stderr)

    def _mc_print_error_caller_unchecked(self, message, mc_error_info_up_level):
        """Print a single message preceded by file:line. The caller is responsible for checking if self is frozen."""
        file_name, line_num = caller_file_line(up_level=mc_error_info_up_level + 1)
        print(_line_msg(file_name=file_name, line_num=line_num) + '\n' + self._mc_error_msg(message), file=sys.stderr)

    def _mc_print_error_caller(self, message, mc_error_info_up_level):
        """Print a single message preceded by file:line. If self is frozen then raise error immediately."""
        self._mc_print_error_caller_unchecked(message, mc_error_info_up_level + 1)
        if self._mc_where == Where.FROZEN:
            # We need to raise now, self is already frozen so error count will not be checked later
            self._mc_raise_errors()

    def _mc_print_warning(self, message, file_name, line_num):
        """Print a single message preceded by file:line"""
        print(_line_msg(file_name=file_name, line_num=line_num) + '\n' + self._mc_warning_msg(message), file=sys.stderr)

    def _mc_print_value_error_msg(self, attr_name, value, mc_caller_file_name, mc_caller_line_num):
        """Print message about invalid or missing value"""
        cr = self._mc_root
        current_env = thread_local.env

        value_msg = ' ' + repr(value) if value != MC_NO_VALUE else ''
        msg = "Attribute: '{attr}'{value_msg} did not receive a value for env {env}".format(attr=attr_name, value_msg=value_msg, env=current_env)
        if value == MC_TODO:
            cr._mc_todo_msgs[current_env].append((msg, mc_caller_file_name, mc_caller_line_num))
            todo_handling = cr._mc_todo_handling_allowed if current_env.allow_todo else cr._mc_todo_handling_other
            if todo_handling is McTodoHandling.SILENT:
                return
            if todo_handling is McTodoHandling.WARNING:
                self._mc_print_warning(msg, file_name=mc_caller_file_name, line_num=mc_caller_line_num)
                return

        self._mc_print_error(msg, file_name=mc_caller_file_name, line_num=mc_caller_line_num)

    def _mc_validate_attributes(self, mc_error_info_up_level):
        """Verify that all attributes got a value"""
        if not self._mc_attributes_to_check:
            return

        if thread_local.is_under_default_item:
            return

        msg = "The following attribues defined earlier never received a proper value for {env}:".format(env=self.env)
        if mc_error_info_up_level is not None:
            mc_caller_file_name, mc_caller_line_num = find_user_file_line(up_level_start=mc_error_info_up_level + 1)
            print(_line_msg(file_name=mc_caller_file_name, line_num=mc_caller_line_num), file=sys.stderr)
        print(_error_msg(msg), file=sys.stderr)

        for attr_name, info in self._mc_attributes_to_check.items():
            where_from, value_file_name, value_line_num = info  # TODO, 'use where'_from in error message
            value = getattr(self, attr_name)
            self._mc_print_value_error_msg(attr_name, value, value_file_name, value_line_num)

    def _mc_validate_required(self, mc_error_info_up_level):
        """Verify that all @required child items are present"""
        if not self._mc_deco_required:
            return

        missing_req = {}
        for req in self._mc_deco_required:
            if req not in self.__dict__:
                missing_req[req] = None

            # Any required item not present on self, but found on a default value item with same name will be assigned to self
            contained_in = self
            while contained_in and missing_req:
                contained_in, shared_req = contained_in._mc_find_closest_default_item(req)
                if not shared_req:
                    break

                if isinstance(shared_req, (_ConfigBase, RepeatableDict)):
                    proxy_insert(self, req, shared_req)
                    del missing_req[req]
                    continue

        if missing_req:
            if mc_error_info_up_level is not None:
                mc_caller_file_name, mc_caller_line_num = find_user_file_line(up_level_start=mc_error_info_up_level)
                print(_line_msg(file_name=mc_caller_file_name, line_num=mc_caller_line_num), file=sys.stderr)
            print(self._mc_error_msg(f"Missing '@required' items: {list(missing_req)}"), file=sys.stderr)

    @classmethod
    def named_as(cls):
        """Return the named_as property set by the @named_as decorator"""
        return cls._mc_deco_named_as or cls.__name__

    def ref_id_for_json(self):
        return id(self)

    def json(self, compact=False, sort_attributes=False, property_methods=True, builders=False, default_items=False, skipkeys=True, warn_nesting=None, show_all_envs=False,
             depth=None, persistent_ids=False):
        """Create json representation of configuration.

        The mc_json_filter and mc_json_fallback arguments to :func:`mc_config` also influence the output.

        Arguments:
            compact (bool): Set compact to true if dumping for easier human readable output, false for machine readable output.
            sort_attributes (bool): Sort attributes by name. Sort dir() entries by name.
            property_methods (bool or None): Call @property methods and insert values in output, including a comment that the value is calculated.
                If `property_methods` is None the @property method is not called but the name is still output, with the value replace by a fixed
                message. False completely disables information about @property methods.
            builders (bool): Include ConfigBuilder items in json.
            default_items (bool): Include DefaultItems in json.
            skipkeys (bool): Passed to json.dumps.
            show_all_envs (bool): Display attribute values for all envs in a single dump. Without this only the values for the current env is displayed.
            depth (int): The number of levels of child objects to dump. None means all.
            persistent_ids (bool): Use a persistent value instead of using id(obj) as reference keys.
                NOTE: This will mostly make it impossible to identify the referenced obj, but it makes it possible to compare json across runs.
        """

        cr = self._mc_root

        filter_callable = cr._mc_json_filter
        fallback_callable = cr._mc_json_fallback

        with_item_types = (
            (_ConfigBase, RepeatableConfigItem, RepeatableDict) if (builders and default_items) else
            (ConfigBuilder, ConfigItem, RepeatableConfigItem, RepeatableDict) if builders else
            (DefaultItems, ConfigItem, RepeatableConfigItem, RepeatableDict) if default_items else
            (ConfigItem, RepeatableConfigItem, RepeatableDict)
        )

        encoder = ConfigItemEncoder(
            filter_callable=filter_callable, fallback_callable=fallback_callable,
            compact=compact, sort_attributes=sort_attributes, property_methods=property_methods,
            with_item_types=with_item_types,
            warn_nesting=warn_nesting,
            multiconf_base_type=_ConfigBase,
            multiconf_property_wrapper_type=_McPropertyWrapper,
            show_all_envs=show_all_envs,
            depth=depth,
            persistent_ids=persistent_ids)

        cr._mc_in_json = True

        # Disable attribute setting to avoid side effects from calling json if @property methods set mc attributes
        _ConfigBase._mc_setattr = _ConfigBase._mc_setattr_disabled

        try:
            orig_env = thread_local.env
            if show_all_envs:
                thread_local.env = MC_NO_ENV

            # python3 doesn't need  separators=(',', ': ')
            json_str = json.dumps(self, skipkeys=skipkeys, default=encoder, check_circular=False, sort_keys=False, indent=4, separators=(',', ': '))
            cr._mc_json_errors = encoder.num_errors
            return json_str
        finally:
            _ConfigBase._mc_setattr = _ConfigBase._mc_setattr_real
            cr._mc_in_json = False

            thread_local.env = orig_env

    def _mc_excl_repr(self):
        return "Excluded: " + repr(type(self))

    def __repr__(self):
        if self:
            # Don't call @property methods in repr, it is too dangerous, leading to double errors (endless loops) in case of incorrect user
            # implemented @property methods. We only insert the method name and a predefined message in the generated json.
            return self.json(compact=True, property_methods=None, builders=False, depth=None)
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

        This makes it possible to implement checks like the following::

            assert item.getattr('mem_size', pprd) == item.getattr('mem_size', prod) <= item.getattr('mem_size', tst1)

        Note that careful consideration should be taken when using env names explicitly (as above) when implementing a configuration
        object model, since this will force all configurations to define those envs.

        Note that no modifications can be done in this method!
        """

    def __bool__(self):
        return bool(self._mc_exists_in_env())

    def __dir__(self):
        return [name for name in object.__dir__(self)
                if not isinstance(getattr(self.__class__, name, None), _McAttributeAccessor) or name in self._mc_attributes]

    def _mc_exists_in_given_env(self, env):
        return self._mc_handled_env_bits & env.mask

    def _mc_exists_in_env(self):
        env_mask = thread_local.env.mask
        return self._mc_handled_env_bits & env_mask or env_mask == 0

    def _mc_attributes_to_check_add(self, attr_name, mc_error_info_up_level):
        mc_caller_file_name, mc_caller_line_num = caller_file_line(up_level=mc_error_info_up_level + 1)
        if self._mc_attributes_to_check is None:
            self._mc_attributes_to_check = {}

        self._mc_attributes_to_check[attr_name] = (self._mc_where, mc_caller_file_name, mc_caller_line_num)

    def _mc_attributes_to_check_del(self, attr_name):
        if self._mc_attributes_to_check:
            self._mc_attributes_to_check.pop(attr_name, None)

    def _mc_find_closest_default_item(self, item_name):
        contained_in = self._mc_contained_in
        while contained_in:
            default_items = contained_in.__dict__.get(DefaultItems.name)
            if default_items:
                default_item = getattr(default_items, item_name, MC_NO_VALUE)
                if default_item != MC_NO_VALUE:
                    if isinstance(default_item, RepeatableDict):
                        # There should be only one, get it
                        for default_item in default_item._all_items.values():  # pragma: no branch
                            break

                    return contained_in, default_item

            contained_in = contained_in._mc_contained_in

        return None, None

    def _mc_resolve_shared_attribute(self, default_item, attr_name, mc_error_info_up_level):
        """Try to resolve attribute values from default_item.

        Return: True if value is found, False otherwise.
        """

        env_attr = self._mc_attributes[attr_name]
        shared_value = getattr(default_item, attr_name, MC_NO_VALUE)
        if shared_value in (MC_NO_VALUE, MC_REQUIRED):
            return False

        # This will pop attributes from self._mc_attributes_to_check
        shared_attr = default_item._mc_attributes[attr_name]
        self._mc_setattr_env_value(
            thread_local.env, attr_name, env_attr, shared_value, old_value=getattr(self, attr_name), from_eg=shared_attr.from_eg,
            mc_force=False, mc_error_info_up_level=mc_error_info_up_level + 1)

        return True

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

        if self.mc_validate.__code__ is _ConfigBase.mc_validate.__code__:
            # mc_validate has not been overridden, so we can validate that all attributes have been set now
            self._mc_validate_attributes(mc_error_info_up_level)

        if isinstance(self, ConfigBuilder):
            self._mc_builder_freeze()

        # New items may have been created in mc_init
        self._mc_freeze_previous(mc_error_info_up_level)

        if must_pop:
            self.__class__._mc_hierarchy.pop()

        if not self._mc_is_default_value_item:
            # Any child item not present on self, but found on a corresponding default value item matching self will be assigned to self
            contained_in = self
            while contained_in:
                contained_in, default_item = contained_in._mc_find_closest_default_item(self.named_as())
                if not default_item:
                    break

                for shared_child_name, shared_child in default_item.items(with_excluded=True):
                    if isinstance(shared_child, RepeatableDict):
                        if shared_child_name not in self._mc_deco_nested_repeatables:
                            # Don't merge repeatables on shared items if they are not declared on self
                            continue

                        repeatable = object.__getattribute__(self, shared_child_name)
                        for rep_key, rep in shared_child._all_items.items():
                            repeatable._all_items.setdefault(rep_key, _mc_item_parent_proxy_factory(self, rep))
                        continue

                    if shared_child_name not in [named_as for named_as, it in  self.items(with_excluded=True)]:
                        proxy_insert(self, shared_child_name, shared_child)

        if not thread_local.is_under_default_item:
            self._mc_validate_required(mc_error_info_up_level + 1 if mc_error_info_up_level is not None else None)

        if self._mc_num_errors:
            self._mc_raise_errors()
        self._mc_where = Where.FROZEN

        if not _ConfigBase._mc_in_build:
            self._mc_built_by = None

    def _mc_freeze_previous(self, mc_error_info_up_level):
        previous_item = _ConfigBase._mc_last_item
        if previous_item is not self and previous_item is not self._mc_contained_in and previous_item and previous_item._mc_where != Where.FROZEN:
            previous_item._mc_freeze(mc_error_info_up_level + 1 if mc_error_info_up_level is not None else None)

    def _mc_call_mc_validate(self, env):
        """Call the user defined 'mc_validate' method and verify attributes"""
        if not self._mc_exists_in_given_env(env):
            return

        self._mc_where = Where.NOWHERE
        self.mc_validate()
        self._mc_validate_attributes(None)
        if self._mc_num_errors:
            self._mc_raise_errors()
        self._mc_where = Where.FROZEN

    def _mc_call_mc_post_validate(self):
        """Call the user defined 'mc_post_validate' method."""

        self._mc_where = Where.NOWHERE
        self.mc_post_validate()
        self._mc_where = Where.FROZEN

    def _mc_validate_properties(self, env):
        """Validate that @property methods can be called without error"""
        if not self._mc_exists_in_given_env(env):
            return

        for key in self.__class__._mc_cls_dir_entries:
            if key.startswith('_') or key in self._mc_attributes or key in self.__dict__ or key in _mc_filter_out_keys:
                continue

            try:
                val = getattr(self, key)
            except InvalidUsageException:
                self._mc_root._mc_num_invalid_property_usage += 1
                # print(_error_msg("InvalidUsageException trying to validate @property '{prop_name}' in {env}.".format(prop_name=key, env=env)), file=sys.stderr)
                # traceback.print_exception(*sys.exc_info())
            except Exception as ex:
                self._mc_root._mc_num_property_errors += 1
                print(_error_msg("Exception validating @property '{prop_name}' on item {item} in {env}.".format(
                    prop_name=key, item=_mc_identification_msg_str(self), env=env)), file=sys.stderr)
                traceback.print_exception(*sys.exc_info())

    @property
    def num_invalid_property_usage(self):
        """Returns number of 'InvalidUsageException' s encountered when validating @property methods
        Returns 0 if 'mc_config' was called with validate_properties=False.
        """

        return self._mc_root._mc_num_invalid_property_usage

    def __enter__(self):
        self._mc_where = Where.IN_WITH if self._mc_where != Where.IN_RE_INIT else Where.IN_RE_WITH
        self.__class__._mc_hierarchy.append(self)
        # self.__class__._mc_debug_hierarchy('_ConfigBase.__enter__')
        return self

    def __exit__(self, exc_type, value, traceback):
        if not exc_type:
            self._mc_freeze_previous(mc_error_info_up_level=1)
            self._mc_freeze(mc_error_info_up_level=1)
            self.__class__._mc_hierarchy.pop()
            return None

        # self.__class__._mc_debug_hierarchy('_ConfigBase.__exit__')
        if exc_type is _McExcludedException:
            self.__class__._mc_hierarchy.pop()
            return True

    def _mc_setattr_env_value(self, current_env, attr_name, env_attr, value, old_value, from_eg, mc_force, mc_error_info_up_level):
        # print("_mc_setattr_env_value:", current_env, attr_name, value, old_value, self._mc_where, env_attr.where_from)
        if old_value not in (MC_NO_VALUE, MC_REQUIRED) and not mc_force:
            if self._mc_where == Where.IN_MC_INIT:
                if env_attr.where_from != Where.IN_MC_INIT:
                    # In mc_init we will not overwrite a proper value set previously unless the eg is more specific than the previous one or mc_force is used
                    if from_eg not in env_attr.from_eg or from_eg == env_attr.from_eg:
                        return

            elif self._mc_where == Where.IN_RE_INIT:
                if env_attr.where_from != Where.IN_RE_INIT:  # pragma: no branch TODO: test
                    # In RE_INIT we will not overwrite a proper value set previously unless the eg is more specific than the previous one or mc_force is used
                    if _ConfigBase._mc_in_build:  # pragma: no cover TODO: test
                        return

                    if from_eg not in env_attr.from_eg or from_eg == env_attr.from_eg:
                        return

            elif self._mc_where == Where.IN_RE_WITH:
                # In RE_WITH we will not overwrite a proper value set previously
                if env_attr.where_from == Where.IN_RE_WITH:
                    # In mc_build we ignore this
                    if not _ConfigBase._mc_in_build:  # pragma: no branch TODO: test
                        # Trying to set the same attribute again in with block
                        msg = "The attribute '{attr_name}' is already fully defined.".format(attr_name=attr_name)
                        self._mc_print_error_caller(msg, mc_error_info_up_level)
                    return

                if env_attr.where_from == Where.IN_WITH:
                    if from_eg not in env_attr.from_eg or from_eg == env_attr.from_eg:
                        return

            elif self._mc_where == Where.IN_WITH:
                if env_attr.where_from == Where.IN_WITH:
                    if not _ConfigBase._mc_in_build:  # pragma: no branch TODO: test
                        # Trying to set the same attribute again in with block
                        msg = "The attribute '{attr_name}' is already fully defined.".format(attr_name=attr_name)
                        self._mc_print_error_caller(msg, mc_error_info_up_level)
                    return

            elif self._mc_where == Where.FROZEN:
                msg = "Trying to set attribute '{attr_name}'. ".format(attr_name=attr_name)
                msg += "Setting attributes is not allowed after item is 'frozen' (with 'scope' is exited)."
                self._mc_print_error_caller(msg, mc_error_info_up_level)  # Note: This always raises en exception

            if env_attr.where_from == Where.FROZEN:
                msg = "Trying to set attribute '{attr_name}'. ".format(attr_name=attr_name)
                msg += "Setting attributes is not allowed after value has been used (in order to enforce derived value validity)."
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

        if value != MC_NO_VALUE:
            # We have a value for the env which is more specific than any previous value
            env_attr.set(current_env, value, self._mc_where, from_eg)

            if value not in (MC_TODO, MC_REQUIRED):
                if self._mc_root._mc_do_type_check:
                    type_msg = typecheck.type_check(self, attr_name, value)
                    if type_msg:
                        self._mc_print_error_caller(type_msg, mc_error_info_up_level)
                        return

                self._mc_attributes_to_check_del(attr_name)
                return

        elif old_value not in (MC_NO_VALUE, MC_TODO, MC_REQUIRED):
            return

        # Try to resolve value from shared items
        # Find first occurrence of DefaultItems.name, by searching backwards towards root_conf
        if not self._mc_is_default_value_item:
            contained_in = self
            while contained_in:
                contained_in, default_item = contained_in._mc_find_closest_default_item(self.named_as())
                if default_item:
                    if self._mc_resolve_shared_attribute(default_item, attr_name, mc_error_info_up_level):
                        return

        if self._mc_where == Where.IN_INIT:
            if value == MC_NO_VALUE:
                env_attr.set(current_env, value, self._mc_where, from_eg)

            # This is not an error now, as we allow partial set in __init__
            # Postpone check until after 'mc_init'
            self._mc_attributes_to_check_add(attr_name, mc_error_info_up_level)
            return

        if self._mc_where == Where.IN_WITH and env_attr.where_from == Where.IN_WITH and value == MC_REQUIRED:
            # This is not an error now, as we allow setting value to MC_REQUIRED in 'with' block
            self._mc_attributes_to_check_add(attr_name, mc_error_info_up_level)
            return

        if thread_local.is_under_default_item:
            return

        # We will report the error now, so remove from check list
        self._mc_attributes_to_check_del(attr_name)

        mc_caller_file_name, mc_caller_line_num = caller_file_line(up_level=mc_error_info_up_level)
        value = value if value != MC_NO_VALUE else old_value
        self._mc_print_value_error_msg(attr_name, value, mc_caller_file_name, mc_caller_line_num)

    def _mc_check_no_existing_attr(self, attr_name, mc_overwrite_property, mc_set_unknown, mc_error_info_up_level):
        if attr_name in self.__dict__:
            # Non-Repeatable ConfigItems are not defined at the class level, only at instance level
            item = self.__dict__[attr_name]
            msg = "'{name}' {typ} is already defined and may not be replaced with an attribute.".format(name=attr_name, typ=type(item))
            self._mc_print_error_caller(msg, mc_error_info_up_level)
            return True

        if mc_overwrite_property:
            msg = "'mc_overwrite_property' is True but no property named '{name}' exists.".format(name=attr_name)
            self._mc_print_error_caller(msg, mc_error_info_up_level)
            return True

        if self._mc_where not in (Where.IN_INIT, Where.IN_RE_INIT) and not mc_set_unknown:
            msg = "All attributes must be defined in __init__ or set with 'mc_set_unknown'. " + \
                  "Attempting to set attribute '{attr_name}' which does not exist.".format(attr_name=attr_name)
            self._mc_print_error_caller(msg, mc_error_info_up_level)
            return True

        return False

    def _mc_setattr(
            self, current_env, attr_name, value, from_eg, mc_overwrite_property, mc_set_unknown, mc_force, mc_error_info_up_level, is_assign=False):
        """Common code for assignment and item.setattr"""

        #_mc_debug("_mc_setattr:", current_env, attr_name, value)
        try:
            cls_attr = getattr(self.__class__, attr_name)
            # print("_mc_setattr, cls_attr:", type(cls_attr))
        except AttributeError as ex:
            #_mc_debug("_mc_setattr, AttributeError:", ex)
            if self._mc_check_no_existing_attr(attr_name, mc_overwrite_property, mc_set_unknown, mc_error_info_up_level+1):
                return

            # print("_mc_setattr creating new _McAttributeAccessor")
            setattr(self.__class__, attr_name, _McAttributeAccessor(attr_name))
            env_attr = _McAttribute()
            self._mc_attributes[attr_name] = env_attr
            self._mc_setattr_env_value(current_env, attr_name, env_attr, value, MC_NO_VALUE, from_eg, mc_force, mc_error_info_up_level + 1)
        else:
            if isinstance(cls_attr, _McAttributeAccessor):
                # print("_mc_setattr found _McAttributeAccessor:", current_env, attr_name, value, from_eg)
                env_attr = self._mc_attributes.get(attr_name)
                if env_attr is None:
                    if self._mc_check_no_existing_attr(attr_name, mc_overwrite_property, mc_set_unknown, mc_error_info_up_level+1):
                        return

                    env_attr = _McAttribute()
                    self._mc_attributes[attr_name] = env_attr
                    old_value = MC_NO_VALUE
                else:
                    old_value = env_attr.env_values.get(current_env, MC_NO_VALUE)
                    if mc_set_unknown and old_value != MC_NO_VALUE:
                        msg = "Attempting to use 'mc_set_unknown' to set attribute '{attr_name}' which already exists.".format(attr_name=attr_name)
                        self._mc_print_error_caller(msg, mc_error_info_up_level)
                        return
                self._mc_setattr_env_value(current_env, attr_name, env_attr, value, old_value, from_eg, mc_force, mc_error_info_up_level + 1)
                return

            if isinstance(cls_attr, _McPropertyWrapper):
                #_mc_debug("_mc_setattr found _McPropertyWrapper")
                if value == MC_NO_VALUE:
                    return

                env_attr = self._mc_attributes.get(attr_name)
                if env_attr is None:
                    env_attr = _McAttribute()
                    self._mc_attributes[attr_name] = env_attr
                    old_value = MC_NO_VALUE
                else:
                    old_value = env_attr.env_values.get(current_env, MC_NO_VALUE)
                    if mc_set_unknown and old_value != MC_NO_VALUE:
                        msg = "Attempting to use 'mc_set_unknown' to overwrite a an existing @property '{attr_name}'.".format(attr_name=attr_name)
                        self._mc_print_error_caller(msg, mc_error_info_up_level)
                        return
                self._mc_setattr_env_value(current_env, attr_name, env_attr, value, old_value, from_eg, mc_force, mc_error_info_up_level + 1)
                return

            if isinstance(cls_attr, RepeatableDict):
                msg = "'{name}' is already defined as a nested-repeatable and may not be replaced with an attribute.".format(name=attr_name)
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

            if not mc_overwrite_property:
                base_msg = "The attribute '{name}' clashes with a @property or method".format(name=attr_name)
                msg = base_msg + " and 'mc_overwrite_property' is False."
                if is_assign:
                    msg = base_msg + ". Use item.setattr with mc_overwrite_property=True if overwrite intended."
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

            if not isinstance(cls_attr, property):
                msg = "'mc_overwrite_property' specified but existing attribute '{name}' with value '{value}' is not a @property.".format(
                    name=attr_name, value=cls_attr)
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

            # Now we know we had a @property at class level
            if value == MC_NO_VALUE:
                # No value was give for current env, so no need to do anything, we will fall back to the @property
                return

            # Replace property with a wrapper
            setattr(self.__class__, attr_name, _McPropertyWrapper(attr_name, cls_attr))
            env_attr = _McAttribute()
            self._mc_attributes[attr_name] = env_attr
            self._mc_setattr_env_value(current_env, attr_name, env_attr, value, MC_NO_VALUE, from_eg, mc_force, mc_error_info_up_level + 1)
            return

    def _mc_setattr_disabled(
            self, current_env, attr_name, value, from_eg, mc_overwrite_property, mc_set_unknown, mc_force, mc_error_info_up_level, is_assign=False):
        """Common code for assignment and item.setattr to disable attribute modification after config is loaded"""
        msg = "Trying to set attribute '{}'. Setting attributes is not allowed after configuration is loaded or while doing json dump (print) (in order to enforce derived value validity)."
        raise ConfigApiException(msg.format(attr_name))

    _mc_setattr_real = _mc_setattr  # Keep a reference to the real _mc_setattr

    def __setattr__(self, attr_name, value):
        if attr_name[0] == '_':
            object.__setattr__(self, attr_name, value)
            return

        cr = self._mc_root
        self._mc_setattr(
            thread_local.env, attr_name, value, cr.env_factory.default, False, False, False, mc_error_info_up_level=3, is_assign=True)

    def setattr(self, attr_name, *, mc_overwrite_property=False, mc_set_unknown=False, mc_force=False, mc_error_info_up_level=2, **env_values):
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

        cr = self._mc_root
        env_factory = cr.env_factory

        if cr._mc_check_unknown:
            # Check that there are no undefined eg names specified
            try:
                env_factory.validate_env_group_names(env_values)
            except EnvException as ex:
                self._mc_print_error_caller(str(ex), mc_error_info_up_level)

        current_env = thread_local.env
        try:
            value, eg = env_factory._mc_resolve_env_group_value(current_env, env_values)
            if eg is not None:
                self._mc_setattr(
                    current_env, attr_name, value, eg, mc_overwrite_property, mc_set_unknown, mc_force, mc_error_info_up_level + 1)
                return

            if not env_values:
                msg = "No Env or EnvGroup names specified."
                self._mc_print_error_caller(msg, mc_error_info_up_level)
                return

            self._mc_setattr(
                current_env, attr_name, MC_NO_VALUE, env_factory.eg_none, mc_overwrite_property, mc_set_unknown, False, mc_error_info_up_level + 1)
            return
        except AmbiguousEnvException as ex:
            msg = "Value for {env} is specified more than once, with no single most specific group or direct env:".format(env=current_env)
            for eg in ex.ambiguous:
                value = env_values[eg.name]
                msg += "\nvalue: " + repr(value) + ", from: " + repr(eg)
            self._mc_print_error_caller(msg, mc_error_info_up_level)

    def getattr(self, attr_name, env):
        """Get the attribute value for the specified env.

        Arguments:
            attr_name (str): The attribute name.
            env (Env): The env to get the value for.
        """

        try:
            orig_env = thread_local.env
            thread_local.env = env
            return getattr(self, attr_name)
        finally:
            thread_local.env = orig_env

    def attr_env_items(self, attr_name, ignored_exceptions=()):
        """Iterate through the attribute (env, value) for the all defined envs.

        If ConfigExcludedAttributeError, ConfigExcludedKeyError or any exception specified in `ignored_exceptions` is raised then
        `McInvalidValue.MC_NO_VALUE` is returned.

        Arguments:
            attr_name (str): The attribute name.
            ignored_exceptions (type or sequence(type)): Additional exception classes to ignore. This can be necessary when
                `attr_name` references a @property method which may raise an arbitrary error when called for an env where some of
                it's dependencies may not be setup correctly.

        Yields:
            env (Env), value (any): The (env, attribute value) for each env or `MC_NO_VALUE` if there is no value for a specific
               env (e.g. the item is excluded). If an exception was raised for all envs the last exception will propagate.
        """

        try:
            exception = True
            orig_env = thread_local.env
            # print("attr_env_items 1:", attr_name, 'current env:', orig_env, bool(self))
            for env in self._mc_root._mc_env_factory.envs.values():
                thread_local.env = env
                # print("attr_env_items 2:", env, type(self), bool(self),
                #       '\n self._mc_handled_env_bits', int_to_bin_str(self._mc_handled_env_bits),
                #       '\n env.mask                 ', int_to_bin_str(env.mask))
                try:
                    yield env, getattr(self, attr_name)
                    exception = False
                except (ConfigExcludedAttributeError, ConfigExcludedKeyError) as ex:
                    # print("attr_env_items 3:", ex)
                    if exception:
                        exception = ex
                    yield env, MC_NO_VALUE
                except ignored_exceptions as ex:
                    # print("attr_env_items 4:", repr(ex), 'hello')
                    if exception:
                        exception = ex
                    yield env, MC_NO_VALUE
        finally:
            thread_local.env = orig_env
            if exception and exception is not True:
                raise exception

    def attr_env_values(self, attr_name, ignored_exceptions=()):
        """Iterate through the attribute value for the all defined envs.

        See :meth:`attr_env_items` for common behaviour.

        Yields:
            value (any): The attribute value for each env.
        """

        for _, value in self.attr_env_items(attr_name, ignored_exceptions):
            yield value

    def env_loop(self):
        """Iterator over all defined envs.

        Sets current env and yields it.
        This is most useful for cross env applications where the config has been instantiated with `MC_NO_ENV`.

        E.g.::

            class item(ConfigItem):
                def __init__(self, aa):
                    super().__init__()
                    self.aa = aa
                    self.aa_alternate = MC_REQUIRED

                @property
                def aa_special(self):
                    return self.aa_alternate + self.aa

            @mc_config(ef)
            def config(root):
                with item(aa=1) as it:
                    it.setattr('aa_alternate', default=1, prod=7)

            cr = config(MC_NO_ENV)

            exp_envs = [pp, prod]
            exp_values = [2, 8]
            for index, env in enumerate(cr.item.env_loop()):
                print(cr.item.aa)
                print(cr.item.aa_special)

          prints: 1 2 1 8

        Yields:
            env (Env): The env which was set as the current env.
        """

        try:
            orig_env = thread_local.env
            for env in self._mc_root._mc_env_factory.envs.values():
                thread_local.env = env
                yield env
        finally:
            thread_local.env = orig_env

    def items(self, with_types=None, with_excluded=False):
        """Iterate all nested items of types specified and possibly excluded items.

        Arguments:
            with_types: Types to include in iteration. The default value is what should be used in configuration code. Other types should only be included for debugging.
            with_excluded: Include excluded objects. The default is what should be used in configuration code. True should only be used for debugging.

        Yields:
            item (any type specified in 'with_types'): The nested items.
        """

        with_types = with_types or (ConfigItem, RepeatableDict)
        for key, item in self.__dict__.items():
            if not key.startswith('_') and isinstance(item, with_types) and (item or with_excluded) and not key in self._mc_attributes:
                yield key, item

    def items_with_builders_and_excluded(self, with_builders=True, with_excluded=True):
        """Iterate all nested items, incl. builders and excluded.

        Yields:
            item (ConfigItem or RepeatableDict): Nested items.
        """
        yield from self.items(with_types=(RepeatableDict, _ConfigBase if with_builders else ConfigItem), with_excluded=with_excluded)

    @property
    def env(self):
        return thread_local.env

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
        while isinstance(mc_contained_in, ConfigBuilder):
            if mc_contained_in._mc_where == Where.IN_WITH and not child._mc_where == Where.IN_MC_BUILD:
                msg = "Use of 'contained_in' in not allowed in object while under the 'with' statement of a ConfigBuilder. The final containment is still unknown."
                self._mc_print_error_caller(msg, mc_error_info_up_level=2)
                raise ConfigApiException(msg)
            if self._mc_root._mc_config_post_validated and not isinstance(child, _ItemParentProxy):
                msg = "Use of 'contained_in' in not allowed through direct reference to an item from 'with' statement of a ConfigBuilder. Containment is unknown."
                self._mc_print_error_caller_unchecked(msg, mc_error_info_up_level=2)
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
        """Find first occurrence of attribute or child item 'name', by searching backwards towards root_conf, starting with self."""

        contained_in = self
        while contained_in:
            attr = contained_in._mc_attributes.get(name)
            if attr:
                return getattr(contained_in, name)
            item = contained_in.__dict__.get(name)
            if item and isinstance(item, (ConfigItem, RepeatableDict)):
                return item
            contained_in = contained_in.contained_in
        return None

    def find_attribute(self, name):
        """Find first occurrence of attribute or child item 'name', by searching backwards towards root_conf, starting with self."""

        contained_in = self
        while contained_in:
            attr = contained_in._mc_attributes.get(name)
            if attr:
                return getattr(contained_in, name)
            item = contained_in.__dict__.get(name)
            if item and isinstance(item, (ConfigItem, RepeatableDict)):
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

    def _mc_get_repeatable(self, repeatable_class_key, repeatable_cls_or_dict):
        """Return repeatable if item has repeatable with 'repeatable_class_key', if not raise an exception."""
        if repeatable_class_key in self.__class__._mc_deco_nested_repeatables:
            return object.__getattribute__(self, repeatable_class_key)

        if isinstance(repeatable_cls_or_dict, RepeatableDict):
            # Get class of first item for error message. TODO: muliple types can be in the same repeatable
            for item in repeatable_cls_or_dict._all_items.values():  # pragma: no branch
                repeatable_cls_or_dict = type(item)
                break

        msg = not_repeatable_in_parent_msg.format(
            repeatable_cls_key=repeatable_class_key, repeatable_cls=repeatable_cls_or_dict, ci_named_as=self.named_as(), ci_cls=type(self))
        raise ConfigException(msg)

    @property
    def mc_is_default_value_item(self):
        return self._mc_is_default_value_item


class AbstractConfigItem(_ConfigBase):  # TODO metaclass=abc.ABCMeta
    """This may be used as the base of classes which will be basis for both Repeatable and non-repeatable ConfigItem.

    Inheriting from this class makes it possible to use the decorators on a your base class and then later in the hierarchy split into Repeatable and
    non repeatable.
    """

    def __new__(cls, mc_key=None, *init_args, **init_kwargs):
        try:
            object.__getattribute__(cls, '_mc_cls_dir_entries')
        except AttributeError:
            # Get dir list before attributes are added, but attributes may have been added to a base class, so filter those out
            # Assume that dir(cls) will never fail
            cls._mc_cls_dir_entries = [dd for dd in dir(cls) if not isinstance(getattr(cls, dd), _McAttributeAccessor)]
        return super().__new__(cls)

    def __init__(self, mc_key=None, mc_include=None, mc_exclude=None):
        previous_item = _ConfigBase._mc_last_item
        try:
            self._mc_freeze_previous(mc_error_info_up_level=None)
        except Exception as ex:
            print("Exception validating previously defined object -", file=sys.stderr)
            print("  type:", type(_ConfigBase._mc_last_item or previous_item), file=sys.stderr)
            print("Stack trace will be misleading!", file=sys.stderr)
            print("This happens if there is an error (e.g. attributes with value MC_REQUIRED or missing '@required' ConfigItems) in", file=sys.stderr)
            print("an object that was not directly enclosed in a with statement. Objects that are not arguments to a with", file=sys.stderr)
            print("statement will not be validated until the next ConfigItem is declared or an outer with statement is exited.", file=sys.stderr)
            raise

        _ConfigBase._mc_last_item = self

        if not self._mc_contained_in:
            self._mc_handled_env_bits &= ~thread_local.env.mask
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
            self._mc_handled_env_bits &= ~thread_local.env.mask
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

        if self._mc_where == Where.FROZEN:
            self._mc_print_error_caller("Calling 'mc_select_envs' on a frozen item.", mc_error_info_up_level)

        try:
            if self._mc_select_envs(include, exclude):
                raise _McExcludedException()
        except ConfigException as ex:
            self._mc_print_error_caller(str(ex), mc_error_info_up_level)


class _RealConfigItemMixin():
    """Method definitions for non-ConfigBuilder classes"""

    def _mc_call_mc_validate_recursively(self, env):
        """Call the user defined 'mc_validate' methods on item and child items"""
        self._mc_call_mc_validate(env)

        for _, child_item in self.items_with_builders_and_excluded():
            child_item._mc_call_mc_validate_recursively(env)

    def _mc_call_mc_post_validate_recursively(self):
        """Call the user defined 'mc_post_validate' methods on all items"""
        self._mc_call_mc_post_validate()

        for _, child_item in self.items_with_builders_and_excluded():
            child_item._mc_call_mc_post_validate_recursively()

    def _mc_validate_properties_recursively(self, env):
        """Call _mc_validate_properties recursively"""
        self._mc_validate_properties(env)

        for _, child_item in self.items_with_builders_and_excluded():
            child_item._mc_validate_properties_recursively(env)

    def ref_type_info_for_json(self):
        return ''


class _ConfigBuilderMixin():
    """Method definitions for ConfigBuilder classes

    This must have the same methods as the _RealConfigItemMixin class.
    We never recurse from the builder item, recursion is done from the real item where the built items are placed.
    """

    def _mc_call_mc_validate_recursively(self, env):
        """Call the user defined 'mc_validate' methods on item but don't actually recurse"""
        self._mc_call_mc_validate(env)

    def _mc_call_mc_post_validate_recursively(self):
        """Call the user defined 'mc_post_validate' methods on item but don't actually recurse"""
        self._mc_call_mc_post_validate()

    def _mc_validate_properties_recursively(self, env):
        """Call _mc_validate_properties but don't actually recurse"""
        self._mc_validate_properties(env)

    def ref_type_info_for_json(self):
        return ' builder'


class _DefaultItemsMixin():
    """Method definitions for DefaultItems class

    This must have the same methods as the _RealConfigItemMixin class.
    We never recurse or do any validation of DefaultItems.
    """

    def _mc_call_mc_validate_recursively(self, env):
        pass

    def _mc_call_mc_post_validate_recursively(self):
        pass

    def _mc_validate_properties_recursively(self, env):
        pass

    def ref_type_info_for_json(self):
        return ' default'


class ConfigItem(AbstractConfigItem, _RealConfigItemMixin):
    """Base class for config items."""

    def __new__(cls, *init_args, **init_kwargs):
        # cls._mc_debug_hierarchy('ConfigItem.__new__')
        contained_in = cls._mc_hierarchy[-1]
        built_by = _ConfigBase._mc_in_build

        # Find the first parent which is not a builder if we are in the mc_build method of a builder
        if contained_in._mc_where == Where.IN_MC_BUILD:
            built_by = contained_in
            while contained_in._mc_where == Where.IN_MC_BUILD:
                contained_in = contained_in._mc_contained_in

        name = cls.named_as()

        try:
            self = contained_in.__dict__[name]
            if self._mc_handled_env_bits & thread_local.env.mask:
                if name in contained_in.__class__._mc_deco_nested_repeatables:
                    msg = repeatable_in_parent_msg.format(named_as=name, cls=cls, ci_item=contained_in)
                    raise ConfigException(msg, is_fatal=True)

                # We are trying to replace a non-repeatable object. In mc_init we ignore this.
                if contained_in._mc_where == Where.IN_MC_INIT:
                    self._mc_where = Where.IN_RE_INIT
                    return self

                if _ConfigBase._mc_in_build and self._mc_built_by != _ConfigBase._mc_in_build:
                    # We are trying to replace a non-repeatable in mc_build. In mc_build we ignore this.
                    self._mc_where = Where.IN_RE_INIT
                    return self

                raise ConfigException("Repeated non repeatable conf item: '{name}': {cls}".format(name=name, cls=cls))
            self._mc_handled_env_bits |= thread_local.env.mask

            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0
            return self
        except KeyError:
            self = super().__new__(cls)
            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0

            self._mc_attributes = {}
            self._mc_attributes_to_check = None
            self._mc_contained_in = contained_in
            self._mc_root = contained_in._mc_root
            self._mc_built_by = built_by
            self._mc_handled_env_bits = thread_local.env.mask
            self._mc_is_default_value_item = contained_in._mc_is_default_value_item

            for key in cls._mc_deco_nested_repeatables:
                od = RepeatableDict()
                object.__setattr__(self, key, od)

            # Insert self in parent
            if name in contained_in._mc_attributes:
                msg = "'{name}' is defined both as simple value and a contained item: {self}".format(name=name, self=self)
                raise ConfigException(msg, is_fatal=True)

            object.__setattr__(contained_in, name, self)

            return self


class RepeatableConfigItem(AbstractConfigItem, _RealConfigItemMixin):
    """Base class for config items which may be repeated.

    RepeatableConfigItems will be stored in a dict using the key 'mc_key'.

    Args:
        mc_key (hashable): The key used to lookup the config item.
    """

    _mc_key_name = None
    _mc_key_value = None

    def __new__(cls, mc_key=None, *init_args, **init_kwargs):
        # cls._mc_debug_hierarchy('RepeatableConfigItem.__new__')
        contained_in = cls._mc_hierarchy[-1]
        built_by = None

        # Find the first parent which is not a builder if we are in the mc_build method of a builder
        if contained_in._mc_where == Where.IN_MC_BUILD:
            built_by = contained_in
            while contained_in._mc_where == Where.IN_MC_BUILD:
                contained_in = contained_in._mc_contained_in

        repeatable = contained_in._mc_get_repeatable(cls.named_as(), cls)

        if repeatable and isinstance(contained_in, DefaultItems):
            raise ConfigException(f"'{cls.__name__}' cannot be repeated under '{DefaultItems.__name__}'. The first (and only) occurance of a '{RepeatableConfigItem.__name__}' instance is used to provide the default attribute values.")

        mc_key = init_kwargs.get(cls._mc_key_name) or cls._mc_key_value or mc_key

        try:
            self = repeatable._all_items[mc_key]
            if self._mc_handled_env_bits & thread_local.env.mask:
                # We are trying to replace an object with the same mc_key. In mc_init we ignore this.
                if contained_in._mc_where == Where.IN_MC_INIT:
                    self._mc_where = Where.IN_RE_INIT
                    return self
                if built_by:
                    build_msg = " from 'mc_build'"
                    ci_msg = contained_in.json(compact=True, property_methods=None, builders=True, depth=None)
                else:
                    build_msg = ""
                    ci_msg = contained_in
                raise ConfigException("Re-used key '{key}' in repeated item {cls}{build_msg} overwrites existing entry in parent:\n{ci}".format(
                    key=mc_key, cls=cls, build_msg=build_msg, ci=ci_msg))
            self._mc_handled_env_bits |= thread_local.env.mask

            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0
            return self
        except KeyError:
            self = super().__new__(cls)
            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0

            self._mc_attributes = {}
            self._mc_attributes_to_check = None
            self._mc_contained_in = contained_in
            self._mc_root = contained_in._mc_root
            self._mc_built_by = built_by
            self._mc_handled_env_bits = thread_local.env.mask
            self._mc_is_default_value_item = contained_in._mc_is_default_value_item

            for key in cls._mc_deco_nested_repeatables:
                od = RepeatableDict()
                object.__setattr__(self, key, od)

            # Insert self in repeatable
            repeatable._all_items[mc_key] = self
            return self

    @classmethod
    def named_as(cls):
        """Return the named_as property set by the @named_as decorator"""
        return cls._mc_deco_named_as or (cls.__name__ + 's')


class _UndeclaredRepeatableMixin():
    def _mc_get_repeatable(self, repeatable_class_key, repeatable_cls_or_dict):
        """Create any nested repeatable without previous declaration."""
        repeatable = getattr(self, repeatable_class_key, None)
        if repeatable is not None:
            return repeatable

        repeatable = RepeatableDict()
        object.__setattr__(self, repeatable_class_key, repeatable)
        return repeatable


class ConfigBuilder(_ConfigBuilderMixin, _UndeclaredRepeatableMixin, AbstractConfigItem, metaclass=abc.ABCMeta):
    """Base class for 'builder' items which can create (a collection of) other items."""

    def __new__(cls, mc_key='default-builder', *init_args, **init_kwargs):
        # cls._mc_debug_hierarchy('ConfigBuilder.__new__')
        contained_in = cls._mc_hierarchy[-1]
        built_by = None

        # Find the first parent which is not a builder if we are in the mc_build method of a builder
        if contained_in._mc_where == Where.IN_MC_BUILD:
            built_by = contained_in
            while contained_in._mc_where == Where.IN_MC_BUILD:
                contained_in = contained_in._mc_contained_in

        private_key = cls.named_as() + ' ' + str(mc_key)

        try:
            self = contained_in.__dict__[private_key]
            if self._mc_handled_env_bits & thread_local.env.mask:
                # We are trying to replace an object with the same mc_key. In mc_init we ignore this.
                if contained_in._mc_where == Where.IN_MC_INIT:
                    self._mc_where = Where.IN_RE_INIT
                    return self
                build_msg = " from 'mc_build'" if built_by else ""
                raise ConfigException("Re-used key '{key}' in repeated item {cls}{build_msg} overwrites existing entry in parent:\n{ci}".format(
                    key=mc_key, cls=cls, build_msg=build_msg, ci=contained_in.json(compact=True, property_methods=None, builders=True, depth=None)))
            self._mc_handled_env_bits |= thread_local.env.mask

            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0
            return self
        except KeyError:
            self = super().__new__(cls)
            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0

            self._mc_attributes = {}
            self._mc_attributes_to_check = None
            self._mc_contained_in = contained_in
            self._mc_root = contained_in._mc_root
            self._mc_built_by = built_by
            self._mc_handled_env_bits = thread_local.env.mask
            self._mc_is_default_value_item = contained_in._mc_is_default_value_item

            object.__setattr__(contained_in, private_key, self)

            return self

    def __init__(self, mc_key='default-builder', mc_include=None, mc_exclude=None):
        # Overridden to accept 'mc_key'
        super().__init__(mc_include=mc_include, mc_exclude=mc_exclude)

    @classmethod
    def named_as(cls):
        """Try to generate a unique name"""
        return 'mc_ConfigBuilder_' + cls.__name__

    def _mc_builder_freeze(self):
        self._mc_where = Where.IN_MC_BUILD
        _ConfigBase._mc_last_item = None
        was_in_build = _ConfigBase._mc_in_build
        try:
            _ConfigBase._mc_in_build = self
            self.mc_build()
        except _McExcludedException:
            _ConfigBase._mc_in_build = was_in_build

        # Now set all items created in the 'with' block of the builder on the items created in the 'mc_build' method
        for item_from_with_key, item_from_with in self.items(with_types=(ConfigItem, DefaultItems, RepeatableDict)):
            for item_from_build_key, item_from_build in self._mc_contained_in.items():

                if isinstance(item_from_build, RepeatableDict):
                    for bi_key, bi in item_from_build._all_items.items():
                        if bi._mc_built_by is self:
                            proxy_insert(bi, item_from_with_key, item_from_with)
                    continue

                if item_from_build._mc_built_by is self:
                    proxy_insert(item_from_build, item_from_with_key, item_from_with)

        self._mc_freeze_previous(mc_error_info_up_level=1)
        self._mc_where = Where.NOWHERE

    @abc.abstractmethod
    def mc_build(self):
        """Override this in derived classes. This is where child ConfigItems are declared"""


class DefaultItems(_UndeclaredRepeatableMixin, _DefaultItemsMixin, AbstractConfigItem):
    """Class for grouping config items to supply default attribute values across different ConfigItem instances.

    Items can be placed under a 'DefaultItems' item to provide default values (contained items and attributes) for other non-shared items of the same name.
    It is not required to provide valid values for all attributes, neither is it required to satisfy the `required` decorator requirements for nested objects.
    Any attribute left as MC_REQUIRED are expected to get a value in each non-shared ConfigItem, and missing `required` child objects must likewise be
    satisfied in each non-shared ConfigItem.
    RepeatableConfigItems will be merged in from default items to matching regular items iff they have a corresponding `_mc_deco_nested_repeatables`.

        E.g. attributes will be resolved::

            class myitem(ConfigItem):
                def __init__(self):
                    super().__init__()
                    self.abcd = MC_REQUIRED
                    self.efgh = MC_REQUIRED
                    self.ijkl = MC_REQUIRED

            @mc_config(ef, load_now=True)
            def config(_):
                with DefaultItems():
                    with myitem() as ii:
                        ii.efgh = 7

                with myitem() as ii:
                    ii.abcd = 6
                    ii.ijkl = 8

            it = config(prod).myitem

            # it.abcd == 6
            # t.efgh == 7
            # t.ijkl == 8


        E.g. nested items found under DefaultItems will be made available as if declared under a regular item::

            class child(ConfigItem):
                def __init__(self, xx):
                    super().__init__()
                    self.xx = xx

            class myitem(ConfigItem):
                pass

            @mc_config(ef, load_now=True)
            def config(_):
                with DefaultItems():
                    with myitem():
                        child(1)

                myitem()

            sout, serr = capsys.readouterr()

            it = config(pp).myitem
            # it.child.xx == 1
            # it.child.contained_in == it


    DefaultItems are not supported in 'mc_build' or under a ConfigBuilder.
    User validate callback methods 'mc_validate' and 'mc_post_validate' will not be called for any default item.
    The 'mc_init' method will be called.
    The items under the DefaultItems cannot be accessed, they are used solely for resolving values for regular items.
    """

    name = 'mc_DefaultItems'

    def __new__(cls):
        # cls._mc_debug_hierarchy('ConfigItem.__new__')
        contained_in = cls._mc_hierarchy[-1]

        try:
            self = contained_in.__dict__[DefaultItems.name]
            if self._mc_handled_env_bits & thread_local.env.mask:
                raise ConfigException(f"Repeated: {cls}.")
            self._mc_handled_env_bits |= thread_local.env.mask

            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0
            return self
        except KeyError:
            if contained_in._mc_where == Where.IN_MC_BUILD:
                raise ConfigException(f"'{cls.__name__}' are not allowed in 'mc_build'.")

            if contained_in._mc_where == Where.IN_MC_INIT:
                raise ConfigException(f"'{cls.__name__}' are not allowed in 'mc_init'.")

            if contained_in._mc_is_default_value_item:
                raise ConfigException(f"'{cls.__name__}' cannot be nested.")

            self = super().__new__(cls)
            self._mc_where = Where.IN_INIT
            self._mc_num_errors = 0

            self._mc_attributes = {}
            self._mc_attributes_to_check = None
            self._mc_contained_in = contained_in
            self._mc_root = contained_in._mc_root
            self._mc_built_by = None
            self._mc_handled_env_bits = thread_local.env.mask
            self._mc_is_default_value_item = True

            # Insert self in parent
            object.__setattr__(contained_in, DefaultItems.name, self)

            return self

    def __enter__(self):
        thread_local.is_under_default_item = True
        return super().__enter__()

    def __exit__(self, exc_type, value, traceback):
        res = super().__exit__(exc_type, value, traceback)
        thread_local.is_under_default_item = False
        return res

class _ItemParentProxy():
    """The purpose of this is to set the current '_mc_contained_in' when accessing an item created by a builder and assigned under multiple parent items"""
    __slots__ = ('_mc_contained_in', '_mc_proxied_item')
    _mc_lock = threading.RLock()

    def __init__(self, ci, item):
        object.__setattr__(self, '_mc_contained_in', ci)
        object.__setattr__(self, '_mc_proxied_item', item)

    def __getattribute__(self, name):
        if name in object.__getattribute__(self, '__slots__'):
            return object.__getattribute__(self, name)

        item = object.__getattribute__(self, '_mc_proxied_item')
        _ItemParentProxy._mc_lock.acquire()
        orig_ci = item._mc_contained_in
        item._mc_contained_in = object.__getattribute__(self, '_mc_contained_in')
        try:
            attr = getattr(item, name)
            if isinstance(attr, AbstractConfigItem) and not isinstance(attr, _ItemParentProxy):
                return _mc_item_parent_proxy_factory(self, attr)
            return attr
        finally:
            item._mc_contained_in = orig_ci
            _ItemParentProxy._mc_lock.release()

    def __setattr__(self, attr_name, value):
        if attr_name[0] == '_':
            object.__setattr__(self._mc_proxied_item, attr_name, value)
            return

        cr = self._mc_proxied_item._mc_root
        self._mc_proxied_item._mc_setattr(
            thread_local.env, attr_name, value, cr.env_factory.default, False, False, False, mc_error_info_up_level=3, is_assign=True)

    def __enter__(self):
        return self._mc_proxied_item.__enter__()

    def __exit__(self, exc_type, value, traceback):
        return self._mc_proxied_item.__exit__(exc_type, value, traceback)

    def __bool__(self):
        return self._mc_contained_in.__bool__() and self._mc_proxied_item.__bool__()

    def __eq__(self, other):
        return self is other or self._mc_proxied_item is other


def _mc_item_parent_proxy_factory(ci, item):
    cls_name = 'ItemParentProxy:<' + type(item).__module__ + '.' + type(item).__name__ + '>'
    ItemParentProxy = type(cls_name, (_ItemParentProxy,), {})
    return ItemParentProxy(ci, item)


def proxy_insert(parent, item_key, item):
    """Insert proxied item(s) (single or repeatable) into parent.

    This must be used to insert a proxied item under different parents.
    """

    if isinstance(item, RepeatableDict):
        repeatable = parent._mc_get_repeatable(item_key, item)
        for wi_key, wi in item._all_items.items():
            repeatable._all_items[wi_key] = _mc_item_parent_proxy_factory(parent, wi)
        return

    object.__setattr__(parent, item_key, _mc_item_parent_proxy_factory(parent, item))


class McConfigRoot(_ConfigBase, _RealConfigItemMixin):
    """Class of root object allocated by the 'mc_config' decorator.

    May also be used directly for a single env configuration.
    """

    _mc_cls_dir_entries = ()

    def __init__(self, mc_json_filter=None, mc_json_fallback=None, env_factory=None, conf_func=None):
        self._mc_json_filter = mc_json_filter
        self._mc_json_fallback = mc_json_fallback

        self._mc_num_errors = 0
        self._mc_num_warnings = 0
        self._mc_num_property_errors = 0
        self._mc_num_invalid_property_usage = 0

        self._mc_where = Where.IN_INIT
        self._mc_attributes = {}
        self._mc_attributes_to_check = None
        self._mc_contained_in = None
        self._mc_root = self
        self._mc_handled_env_bits = 0
        self._mc_is_default_value_item = False
        self._mc_config_result = {}
        self._mc_config_loaded = False
        self._mc_in_post_validate = False
        self._mc_config_post_validated = False
        self._mc_in_json = False
        self._mc_json_errors = 0
        self._mc_check_unknown = True
        self._mc_lazy_load = False
        self._mc_root_proxies = {}
        self._mc_error_envs = []

        # Make sure _mc_setattr is the real one if decorator is used multiple times
        _ConfigBase._mc_setattr = _ConfigBase._mc_setattr_real

        self._mc_do_type_check = True
        self._mc_do_validate_properties = True

        if env_factory is None:
            # Single environment config, create a dummy env named 'single'
            self._mc_env_factory = EnvFactory()
            single = self._mc_env_factory.Env('single')
            self._mc_is_single_env = single
        else:
            self._mc_env_factory = env_factory
            self._mc_is_single_env = False

        self._mc_env_factory._mc_calc_env_group_order()
        self._mc_todo_msgs = dict([(env, []) for env in self._mc_env_factory.envs.values()])

        if env_factory is None:
            self._mc_pre_load_one_env(single)

        self._mc_conf_func = conf_func

    def __exit__(self, exc_type, value, traceback):
        super().__exit__(exc_type, value, traceback)
        if self._mc_is_single_env:
            self._mc_post_successful_load_one_env(self._mc_is_single_env, None, self)

    @property
    def mc_config_result(self):
        return self._mc_config_result[self.env]

    def __bool__(self):
        return True

    def _mc_pre_load_one_env(self, env):
        _mc_debug("\n==== Loading", env, "====")
        rp = _RootEnvProxy(env, self)
        thread_local.env = env
        del self.__class__._mc_hierarchy[:]
        _ConfigBase._mc_last_item = None
        _ConfigBase._mc_in_build = None

        return rp

    def _mc_post_successful_load_one_env(self, env, result, root_proxy):
        self._mc_handled_env_bits |= env.mask
        self._mc_call_mc_validate_recursively(env)
        if self._mc_do_validate_properties:
            _mc_debug("\n==== Validating @properties", env, "====")
            self._mc_validate_properties_recursively(env)
            if self._mc_num_property_errors:
                raise ConfigException("Error validating @property methods for {}".format(env))

        self._mc_check_unknown = False
        self._mc_config_result[env] = result
        self._mc_root_proxies[env] = root_proxy

    def _mc_load_one_env(self, env):
        rp = self._mc_pre_load_one_env(env)
        try:
            with self:
                res = self._mc_conf_func(self)
            self._mc_post_successful_load_one_env(env, res, rp)
        except ConfigException as ex:
            if not self._mc_error_next_env or ex.is_fatal:
                raise

            if not ex.is_summary:
                traceback.print_exc(file=sys.stderr)
            else:
                print(ex.__class__.__name__ + ':', ex, file=sys.stderr)
            print("Error in config for {} above.\n".format(env), file=sys.stderr)

            self._mc_error_envs.append(env)

    def load(
            self,
            error_next_env=False, validate_properties=True,
            todo_handling_other=McTodoHandling.ERROR, todo_handling_allowed=McTodoHandling.WARNING,
            do_type_check=True, do_post_validate=True, lazy_load=False):

        """Load configuration (execute the function which was decorated using `mc_config` for each env defined in the env_factory).

        Arguments:
            error_next_env (bool): If this is False, then no more envs will be instantiated after errors are found in an env.
                If True, then instantiation is attempted for all envs, but an exception is raised at the end in any envs could not
                be instantiated.

            todo_handling_other (McTodoHandling): This specifies how to handle attributes set to MC_TODO for envs with 'allow_todo' False.
                The default is McTodoHandling.ERROR, causing an error message to be printed and the configuration to be considered invalid.
            todo_handling_allowed (McTodoHandling): This specifies how to handle attributes set to MC_TODO for envs with 'allow_todo' True.
                The default is McTodoHandling.WARNING, causing a warning message to be printed but the configuration to be considered valid.

            do_type_check (bool): Do type checking of attributes based on typing annotations.

                Type checking of attributes is done based on typing information from the __init__ signature. If an attribute exists with the same
                name as an __init__ argument with typing information, then the attribute must conform to that type. E.g.::

                    class X(ConfigItem):
                        def __init__(self, a:int = MC_REQUIRED):
                            super().__init__()
                            self.a = a

                It will be checked that x.a is instance of int.

            do_post_validate (bool): Allow skipping the mc_post_validate call. I.e. if set to False the user defined call backs are not called.

            lazy_load (bool): Allow loading config only for envs for which it is instantiated by calling the wrapped config method. If False the config is
                pre-instantiated for all envs in order to validate correctness of the configuration for all envs. Enabling lazy_load also disables
                `mc_post_validate` calls and other checking which cannot be done with lazy loading.

        Returns self: This makes it possible to load and get an instantion in a one liner, e.g.::

            config.load()(prod)
        """

        if self._mc_config_loaded:
            raise ConfigApiException("Configuration can only be loaded once.")

        self._mc_error_next_env = error_next_env
        self._mc_do_validate_properties = validate_properties

        if not isinstance(todo_handling_other, McTodoHandling):
            msg = "'todo_handling_other' arg must be instance of {th_typ!r}; found type {got_typ!r}: {val!r}"
            raise ConfigException(msg.format(th_typ=McTodoHandling.__name__, got_typ=todo_handling_other.__class__.__name__, val=todo_handling_other))

        self._mc_todo_handling_other = todo_handling_other

        if not isinstance(todo_handling_allowed, McTodoHandling):
            msg = "'todo_handling_allowed' arg must be instance of {th_typ!r}; found type {got_typ!r}: {val!r}"
            raise ConfigException(msg.format(th_typ=McTodoHandling.__name__, got_typ=todo_handling_allowed.__class__.__name__, val=todo_handling_allowed))
        self._mc_todo_handling_allowed = todo_handling_allowed

        self._mc_do_type_check = do_type_check

        self._mc_lazy_load |= lazy_load
        # Load envs
        if not self._mc_lazy_load:
            self._mc_root_proxies[MC_NO_ENV] = self
            for env in self._mc_env_factory.envs.values():
                self._mc_load_one_env(env)

            if self._mc_error_envs:
                raise ConfigException("The following envs had errors {}".format(self._mc_error_envs))

            # No modifications are allowed after this
            self._mc_config_loaded = True
            _ConfigBase._mc_setattr = _ConfigBase._mc_setattr_disabled

            if do_post_validate:
                self._mc_in_post_validate = True
                # Call mc_post_validate
                thread_local.env = MC_NO_ENV
                _mc_debug("\n==== Calling 'mc_post_validate' ====")
                self._mc_call_mc_post_validate_recursively()
                self._mc_in_post_validate = False

            self._mc_config_post_validated = True

        self._mc_config_loaded = True
        return self

    def __call__(self, env, allow_todo=False):
        """Get the configuration instantiated for the specified env.

        Arguments:
            env (Env): The environment for which to retrieve the config.
            allow_todo (bool): If true, then retrieving a configuration for an env which contains `MC_TODO` values will not raise an error.

        Return (Root ConfigItem proxy): Reference to the config with the current env set to env.
        """

        try:
            rp = self._mc_root_proxies[env]
        except KeyError:
            if not isinstance(env, Env):
                msg = "{ef_cls}: env must be instance of {env_cls!r}; found type '{got_typ}': {val!r}"
                raise ConfigException(msg.format(ef_cls=self._mc_env_factory.__class__.__name__, env_cls=Env.__name__, got_typ=type(env).__name__, val=env))

            if self._mc_lazy_load and env is MC_NO_ENV:
                raise ConfigException("{} cannot be used with 'lazy_load'.".format(env))

            if env.factory != self._mc_env_factory:
                raise ConfigException("The selected env {} must be from the 'env_factory' specified for 'mc_config'.".format(env))

            if self._mc_lazy_load:
                self._mc_check_unknown = True

                # Make sure _mc_setattr is the real one if decorator is used multiple times
                _ConfigBase._mc_setattr = _ConfigBase._mc_setattr_real

                self._mc_load_one_env(env)
                rp = _RootEnvProxy(env, self)
            else:
                raise  # Should not happen

        if env is not MC_NO_ENV and not allow_todo and rp._mc_todo_msgs[env]:
            for msg, fname, line in rp._mc_todo_msgs[env]:
                print(_line_msg(file_name=fname, line_num=line), file=sys.stderr)
                print(msg, file=sys.stderr)
            raise ConfigException("Trying to get invalid configuration containing MC_TODO")

        return rp


class _RootEnvProxy():
    """The purpose of this is to set the current env when accessing a configuration"""
    __slots__ = ('_mc_root', '_mc_env')

    def __init__(self, env, root_item):
        thread_local.env = env
        object.__setattr__(self, '_mc_env', env)
        object.__setattr__(self, '_mc_root', root_item)

    def __getattr__(self, name):
        cr = self._mc_root
        thread_local.env = self._mc_env
        return getattr(cr, name)

    @property
    def env(self):
        return self._mc_env

    def __repr__(self):
        return repr(self._mc_root)

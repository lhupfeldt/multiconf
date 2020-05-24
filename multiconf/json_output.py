# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os, threading, traceback
import types
from collections.abc import Mapping

from . import envs
from .thread_state import thread_local
from .values import McInvalidValue
from .config_errors import InvalidUsageException, ConfigExcludedAttributeError, ConfigApiException
from .bases import get_bases
from .attribute import Where, _McAttributeAccessor
from .repeatable import RepeatableDict


_calculated_value = ' #calculated'
_static_value = ' #static'
_dynamic_value = ' #dynamic'
_property_method_value_hidden = '@property method value - call disabled'

_mc_filter_out_keys = ('env', 'env_factory', 'contained_in', 'root_conf', 'attributes', 'mc_config_result', 'num_invalid_property_usage', 'named_as')


def _class_tuple(obj, obj_info=""):
    return {'__class__': obj.__class__.__name__ + obj_info}


def _attr_ref_msg(obj, attr_name):
    try:
        return attr_name + ": " + repr(getattr(obj, attr_name))
    except ConfigExcludedAttributeError as ex:
        return attr_name + ": " + ex.value if ex.value else ''
    except AttributeError:
        return ''
    except ConfigApiException:
        return attr_name + ": 'NO-CURRENT-VALUE"


def ref_id(obj):
    try:
        return obj.ref_id_for_json()
    except (AttributeError, TypeError):
        return id(obj)


def _mc_identification_msg_str(objval):
    """Generate a string which may help to identify an item which is not itself being dumped"""
    name_msg = _attr_ref_msg(objval, 'name')
    id_msg = _attr_ref_msg(objval, 'id')
    additionl_ref_info_msg = ''.join([', ' + msg for msg in (id_msg, name_msg) if msg])
    cls_msg = repr(type(objval)) if objval else repr(objval)
    return cls_msg + additionl_ref_info_msg


class ConfigItemEncoder():
    recursion_check = threading.local()
    recursion_check.in_default = None

    def __init__(self, filter_callable, fallback_callable, compact, sort_attributes, property_methods, with_item_types, warn_nesting,
                 multiconf_base_type, multiconf_property_wrapper_type, show_all_envs, depth, persistent_ids):
        """Encoder for json.

        Check the :meth:`~multiconf.ConfigItem.json` and :meth:`~multiconf.ConfigItem.mc_build` methods for public arguments passed on to this.

        Arguments:
            multiconf_base_type, multiconf_property_wrapper_type (type): Passed as arguments as a workaround for cyclic imports.
        """

        self.user_filter_callable = filter_callable
        self.user_fallback_callable = fallback_callable
        self.compact = compact
        self.sort_attributes = sort_attributes
        self.property_methods = property_methods
        self.with_item_types = with_item_types
        self.multiconf_base_type = multiconf_base_type
        self.multiconf_property_wrapper_type = multiconf_property_wrapper_type

        self.seen = {}
        self.start_obj = None
        self.num_errors = 0
        self.num_invalid_usages = 0
        self.show_all_envs = show_all_envs

        self.depth = depth
        self.start_depth = None
        self.current_depth = None

        self.persistent_ids = persistent_ids

        if warn_nesting != None:
            ConfigItemEncoder.recursion_check.warn_nesting = warn_nesting
        else:
            ConfigItemEncoder.recursion_check.warn_nesting = str(os.environ.get('MULTICONF_WARN_JSON_NESTING')).lower() == 'true'

    def ref_repr(self, obj):
        if self.persistent_ids:
            # This will not identify the object, but it gives an indication
            return _mc_identification_msg_str(obj)

        return ref_id(obj)

    def safe_repr(self, obj):
        """This catches exceptions from calling repr(obj) and embeds the message in the returned str."""

        try:
            return repr(obj)
        except Exception as ex:
            traceback.print_exception(*sys.exc_info())
            self.num_errors += 1
            msg = "Error gettting repr of obj, type: {ot}, exception: {extyp}: {exmsg}".format(ot=type(obj), extyp=type(ex).__name__, exmsg=str(ex))
            print(msg, file=sys.stderr)
            return msg

    def _mc_class_dict(self, obj):
        not_frozen_msg = "" if obj._mc_where == Where.FROZEN else ", not-frozen"
        if self.compact:
            msg = " #as: '" + obj.named_as() + "', id: " + str(self.ref_repr(obj)) + not_frozen_msg
            return _class_tuple(obj, msg)
        return {**_class_tuple(obj, not_frozen_msg), '__id__': self.ref_repr(obj)}

    def _ref_item_str(self, objval):
        excl = ' excluded' if not objval else ''

        if isinstance(objval, self.with_item_types):
            return excl + objval.ref_type_info_for_json() + ", id: " + str(self.ref_repr(objval))

        return excl + objval.ref_type_info_for_json() + " " + _mc_identification_msg_str(objval)

    def _ref_earlier_str(self, objval):
        return "#ref" + self._ref_item_str(objval)

    def _ref_later_str(self, objval):
        return "#ref later" + self._ref_item_str(objval)

    def _ref_self_str(self, objval):
        return "#ref self" + self._ref_item_str(objval)

    def _ref_outside_str(self, objval):
        # A reference to an item which is outside of the currently dumped hierarchy.
        # Showing self.ref_repr(obj) does not help here as the object is not dumped, instead try to show some attributes which may identify the object
        return "#outside-ref: " + _mc_identification_msg_str(objval)

    def _ref_mc_item_str(self, objval):
        if ref_id(objval) in self.seen:
            return self._ref_earlier_str(objval)
        return self._ref_later_str(objval)

    def _check_nesting(self, obj, child_obj):
        # Returns child_obj or reference info string
        # Check that object being dumped is actually contained in self
        # We dont want to display an outer/sibling object as nested under an inner object
        # Check for reference to parent or sibling object (in case we dump from a lower level than root)
        if child_obj is obj:
            return self._ref_self_str(child_obj)

        if self.seen.get(ref_id(child_obj)):
            return self._ref_earlier_str(child_obj)

        if isinstance(child_obj, self.multiconf_base_type):
            contained_in = child_obj._mc_contained_in
            while contained_in is not None:
                if contained_in is self.start_obj:
                    # We know we are referencing a later object, because it was not in 'seen'
                    return self._ref_later_str(child_obj)
                contained_in = contained_in._mc_contained_in

            # We found a reference to an item which is outside of the currently dumped hierarchy
            return self._ref_outside_str(child_obj)

        return child_obj

    def _handle_one_attr_one_env(self, obj, key, mc_attr, env, attributes_overriding_property, dir_entries, names_only):
        attr_inf = []
        try:
            val = mc_attr.env_values[env]
            if key in dir_entries:
                attributes_overriding_property.add(key)
                attr_inf = [(' #overrides @property', True)]
        except KeyError as ex:
            # mc_attribute overriding @property OR the value for env has not yet been set
            try:
                val = obj.getattr(key, env)
                attr_inf = [(' #value for {env} provided by @property'.format(env=env), True)]
            except AttributeError:
                val = McInvalidValue.MC_NO_VALUE

        if self.user_filter_callable:
            try:
                key, val = self.user_filter_callable(obj, key, val)
                if key is False:
                    return key, []
            except Exception as ex:
                self.num_errors += 1
                traceback.print_exception(*sys.exc_info())
                attr_inf.append((' #json_error calling filter', self.safe_repr(ex)),)

        val = self._check_nesting(obj, val)
        if val == McInvalidValue.MC_NO_VALUE:
            return key, [(' #no value for {env}'.format(env=env), True)]

        if isinstance(val, Mapping):
            new_val = {}
            for inner_key, maybeitem in val.items():
                if not isinstance(maybeitem, self.multiconf_base_type):
                    new_val[str(inner_key)] = maybeitem
                    continue
                new_val[inner_key] = self._ref_mc_item_str(maybeitem)
            return key, [('', new_val)] + attr_inf

        try:
            iterable = iter(val)
            # TODO?: Include type of iterable in json meta info
        except TypeError:
            return key, [('', val)] + attr_inf

        if isinstance(val, str):
            return key, [('', val)] + attr_inf

        new_val = []
        for maybeitem in val:
            if not isinstance(maybeitem, self.multiconf_base_type):
                new_val.append(maybeitem)
                continue
            new_val.append(self._ref_mc_item_str(maybeitem))
        return key, [('', new_val)] + attr_inf

    def _handle_one_dir_entry_one_env(self, obj, key, _val, env, attributes_overriding_property, _dir_entries, names_only):
        if key.startswith('_') or isinstance(obj.__dict__.get(key, None), (self.multiconf_base_type, RepeatableDict)) or key in _mc_filter_out_keys:
            return key, ()

        overridden_property = ''
        if key in attributes_overriding_property:
            overridden_property = ' #overridden @property'

        # Figure out if the attribute is a @property or a static value
        try:
            # If proxy object then get proxied object, the access to __class__ does not work through the proxy
            real_obj = object.__getattribute__(obj, '_mc_proxied_item')
        except AttributeError:
            real_obj = obj

        for cls in get_bases(object.__getattribute__(real_obj, '__class__')):
            try:
                real_attr = object.__getattribute__(cls, key)
            except AttributeError:
                continue

            if isinstance(real_attr, (property, self.multiconf_property_wrapper_type)):
                calc_or_static = _calculated_value

                if names_only:
                    val = _property_method_value_hidden
                    break

                orig_env = thread_local.env
                try:
                    thread_local.env = env
                    if isinstance(real_attr, self.multiconf_property_wrapper_type):
                        val = real_attr.prop.__get__(obj, type(obj))
                        break

                    val = getattr(obj, key)
                except InvalidUsageException as ex:
                    self.num_invalid_usages += 1
                    return key, [(overridden_property + ' #invalid usage context', self.safe_repr(ex))]
                except Exception as ex:
                    self.num_errors += 1
                    traceback.print_exception(*sys.exc_info())
                    return key, [(overridden_property + ' #json_error trying to handle property method', self.safe_repr(ex))]
                finally:
                    thread_local.env = orig_env
                break
            elif not (hasattr(real_attr, '__call__') or hasattr(real_attr, '__func__')):
                calc_or_static = _static_value
                val = real_attr
                break
            elif isinstance(real_attr, type):
                calc_or_static = ''
                val = real_attr
                break
            else:
                # Ignore methods
                return key, ()

        property_inf = []
        if self.user_filter_callable:
            try:
                key, val = self.user_filter_callable(obj, key, val)
                if key is False:
                    return key, []
            except Exception as ex:
                self.num_errors += 1
                traceback.print_exception(*sys.exc_info())
                property_inf = [(' #json_error calling filter', self.safe_repr(ex))]

        if type(val) == type:
            return key, [(overridden_property, self.safe_repr(val))] + property_inf

        val = self._check_nesting(obj, val)

        if isinstance(val, (str, int, float)):
            if overridden_property:
                return key, [(overridden_property + calc_or_static + ' value was', val)] + property_inf
            if self.compact:
                return key, [('', str(val) + calc_or_static)] + property_inf
            return key, [('', val), (calc_or_static, True)] + property_inf

        if isinstance(val, (list, tuple)):
            new_list = []
            for item in val:
                new_list.append(self._check_nesting(obj, item))
            return key, [(overridden_property, new_list), (calc_or_static, True)] + property_inf

        if isinstance(val, Mapping):
            new_dict = {}
            for item_key, item in val.items():
                new_dict[item_key] = self._check_nesting(obj, item)
            return key, [(overridden_property, new_dict), (calc_or_static, True)] + property_inf

        return key, [(overridden_property, val), (calc_or_static, True)] + property_inf

    def _handle_one_value_multiple_envs(
            self, dd, obj, attr_key, attr_val, env, attributes_overriding_property, dir_entries, one_env_func, multi_value_meta_inf, names_only):
        if not self.show_all_envs:
            attr_key, property_inf = one_env_func(obj, attr_key, attr_val, env, attributes_overriding_property, dir_entries, names_only)
            for meta_key, val in property_inf:
                dd[attr_key + meta_key] = val
            return

        env_values = {}
        prev_key_property_inf = None
        multiple_values = False
        for env in obj.env_factory.envs.values():
            key_property_inf = one_env_func(obj, attr_key, attr_val, env, attributes_overriding_property, dir_entries, names_only)
            if key_property_inf != prev_key_property_inf:
                if prev_key_property_inf is not None:
                    multiple_values = True
                prev_key_property_inf = key_property_inf
            attr_key, property_inf = key_property_inf
            for meta_key, val in property_inf:
                env_values[env.name + meta_key] = val

        if env_values and multiple_values:
            dd[attr_key + multi_value_meta_inf] = True
            dd[attr_key] = env_values
            return

        for meta_key, val in property_inf:
            dd[attr_key + meta_key] = val

    def __call__(self, obj):
        property_methods_orig = self.property_methods
        if ConfigItemEncoder.recursion_check.in_default:
            in_default = ConfigItemEncoder.recursion_check.in_default
            ConfigItemEncoder.recursion_check.in_default = None
            self.property_methods = False

            if self.recursion_check.warn_nesting:
                print("Warning: Nested json calls, disabling @property method value dump:", file=sys.stderr)
                print("outer object type:", type(in_default), file=sys.stderr)
                print("inner object type:", self.safe_repr(type(obj)) + ", inner obj:", obj.json(compact=True, property_methods=False), file=sys.stderr)

        try:
            ConfigItemEncoder.recursion_check.in_default = obj

            if self.seen.get(ref_id(obj)) and obj is not self.start_obj.env:
                return self._ref_earlier_str(obj)
            self.seen[ref_id(obj)] = obj

            if isinstance(obj, self.multiconf_base_type):
                if self.depth is not None:
                    if self.start_depth is None:
                        self.start_depth = 0
                        contained_in = obj
                        while contained_in is not None:
                            self.start_depth += 1
                            contained_in = contained_in.contained_in

                    self.current_depth = 0
                    contained_in = obj
                    while contained_in is not None:
                        self.current_depth += 1
                        contained_in = contained_in.contained_in
                    self.current_depth = self.current_depth - self.start_depth + 1

                # Handle ConfigItems", type(obj)
                dd = self._mc_class_dict(obj)
                if not self.start_obj:
                    self.start_obj = obj

                    # Put 'env' once on the first object
                    dd['env'] = obj.env

                if self.show_all_envs:
                    not_in_envs = [str(env) for env in obj.env_factory.envs.values() if not obj._mc_exists_in_given_env(env)]
                    if not_in_envs:
                        dd["#item does not exist in"] = ', '.join(not_in_envs)

                # --- Handle attributes ---
                attributes_overriding_property = set()
                if self.sort_attributes:
                    attr_dict = {}
                else:
                    attr_dict = dd

                dir_entries = obj._mc_cls_dir_entries

                for attr_key, mc_attr in obj._mc_attributes.items():
                    self._handle_one_value_multiple_envs(
                        attr_dict, obj, attr_key, mc_attr, obj.env, attributes_overriding_property, dir_entries, self._handle_one_attr_one_env,
                        ' #multiconf attribute', names_only=False)

                if self.sort_attributes:
                    for key in sorted(attr_dict):
                        dd[key] = attr_dict[key]

                # --- Handle child items ---
                for key, item in obj.items(with_types=self.with_item_types, with_excluded=True):
                    if self.current_depth is not None:
                        if self.current_depth >= self.depth:
                            dd[key] = _mc_identification_msg_str(item)
                            continue

                        if self.current_depth == self.depth -1 and isinstance(item, RepeatableDict):
                            shallow_item = {}
                            for child_key, child_item in item.items():
                                shallow_item[child_key] = _mc_identification_msg_str(child_item)
                            dd[key] = shallow_item
                            continue

                    if not item and isinstance(item, self.multiconf_base_type):
                        if self.compact:
                            dd[key] = 'false #' + repr(item)
                            continue

                        dd[key] = False
                        dd[key + ' #' + repr(item)] = True
                        continue

                    dd[key] = item

                if self.property_methods is False:
                    # Note: also excludes class/static members
                    return dd

                # --- Handle results from dir() call ---
                if self.sort_attributes:
                    property_dict = {}
                else:
                    property_dict = dd

                for attr_key in dir_entries:
                    self._handle_one_value_multiple_envs(
                        property_dict, obj, attr_key, None, obj.env, attributes_overriding_property, None, self._handle_one_dir_entry_one_env,
                        ' #multiconf env specific @property', names_only=self.property_methods is None)

                if self.sort_attributes:
                    for key in sorted(property_dict):
                        dd[key] = property_dict[key]

                # --- End handle ConfigItem ---
                return dd

            if isinstance(obj, envs.BaseEnv):
                # print "# Handle Env objects", type(obj)
                dd = _class_tuple(obj)
                dd['name'] = obj.name
                return dd

            if type(obj) == type:
                return self.safe_repr(obj)

            # If obj defines json_equivalent, then return the result of that
            if hasattr(obj, "json_equivalent"):
                try:
                    return obj.json_equivalent()
                except Exception as ex:
                    self.num_errors += 1
                    traceback.print_exception(*sys.exc_info())
                    return "__json_error__ calling 'json_equivalent': " + self.safe_repr(ex)

            try:
                iterable = iter(obj)
            except TypeError:
                pass
            else:
                # print("Handle iterable objects", type(obj))
                return list(iterable)

            if self.user_fallback_callable:
                obj, handled = self.user_fallback_callable(obj)
                if handled:
                    return obj

            self.num_errors += 1
            return "__json_error__ # don't know how to handle obj of type: " + self.safe_repr(type(obj))

        finally:
            self.property_methods = property_methods_orig
            ConfigItemEncoder.recursion_check.in_default = None

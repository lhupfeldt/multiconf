# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, os, threading, traceback
from collections import OrderedDict
import types

from . import envs
from .values import McInvalidValue
from .config_errors import InvalidUsageException, ConfigException
from .bases import get_bases

major_version = sys.version_info[0]
if major_version > 2:
    long = int

_warn_json_nesting = str(os.environ.get('MULTICONF_WARN_JSON_NESTING')).lower() == 'true'
_calculated_value = ' #calculated'
_static_value = ' #static'


class NestedJsonCallError(Exception):
    pass


def _class_tuple(obj, obj_info=""):
    return ('__class__', obj.__class__.__name__ + obj_info)


def _attr_ref_msg(obj, attr_name):
    try:
        if hasattr(obj, attr_name):
            return attr_name + ": " + repr(getattr(obj, attr_name))
    except ConfigException as ex:
        if hasattr(ex, 'excluded') and hasattr(ex, 'value'):
            return attr_name + ": " + repr(ex.value)

    return ''


class ConfigItemEncoder(object):
    recursion_check = threading.local()
    recursion_check.in_default = None
    recursion_check.warn_nesting = _warn_json_nesting

    def __init__(self, filter_callable, fallback_callable, compact, sort_attributes, property_methods, builders, warn_nesting,
                 multiconf_base_type, multiconf_builder_type, multiconf_property_wrapper_type):
        """Encoder for json.

        Arguments:
            filter_callable func(obj, key, value): User defined function for filtering
            - filter_callable is called for each key/value pair of attributes on each ConfigItem obj.
            - It must return a tuple of (key, value). If key is False, the key/value pair is removed from the json output

            fallback_callable func(obj): User defined function for handling objects not otherwise encoded.
            - fallback_callable is called for objects that are not handled by the builtin encoder.
            - It must return a tupple (object, handled). If handled is True, the object must be encodable by the standard json encoder.

            compact (bool): Set compact to true if dumping for debug, false for machine readable output.
            sort_attributes (bool): Sort sttributes by name,
            property_methods (bool): call @property methods and insert values in output, including a comment that the value is calculated.
        """

        self.user_filter_callable = filter_callable
        self.user_fallback_callable = fallback_callable
        self.compact = compact
        self.sort_attributes = sort_attributes
        self.property_methods = property_methods
        self.builders = builders
        self.multiconf_base_type = multiconf_base_type
        self.multiconf_builder_type = multiconf_builder_type
        self.multiconf_property_wrapper_type = multiconf_property_wrapper_type

        self.filter_out_keys = ('env', 'env_factory', 'contained_in', 'root_conf', 'attributes', 'mc_config_result')
        self.seen = {}
        self.start_obj = None
        self.num_errors = 0
        self.num_invalid_usages = 0

        if warn_nesting != None:
            self.recursion_check.warn_nesting = warn_nesting

    if major_version < 3:
        def _class_dict(self, obj):
            if self.compact:
                return OrderedDict((_class_tuple(obj, ' #id: ' + repr(id(obj))),))
            return OrderedDict((_class_tuple(obj), ('__id__', id(obj))))

    def _mc_class_dict(self, obj):
        not_frozen_msg = "" if obj._mc_frozen else ", not-frozen"
        if self.compact:
            msg = " #as: '" + obj.named_as() + "', id: " + str(id(obj)) + not_frozen_msg
            return OrderedDict((_class_tuple(obj, msg),))
        return OrderedDict((_class_tuple(obj, not_frozen_msg), ('__id__', id(obj))))

    def _excl_str(self, objval):
        return ' excluded' if  hasattr(objval, '_mc_is_excluded') and objval._mc_is_excluded() else ''

    def _ref_earlier_str(self, objval):
        return "#ref" + self._excl_str(objval) + ", id: " + repr(id(objval))

    def _ref_later_str(self, objval):
        return "#ref later" + self._excl_str(objval) + ", id: " + repr(id(objval))

    def _ref_self_str(self, objval):
        return "#ref self" + self._excl_str(objval) + ", id: " + repr(id(objval))

    def _ref_mc_item_str(self, objval):
        if id(objval) in self.seen:
            return self._ref_earlier_str(objval)
        return self._ref_later_str(objval)

    def _check_nesting(self, obj, child_obj):
        # Returns child_obj or reference info string
        # Check that object being dumped is actually contained in self
        # We dont want to display an outer/sibling object as nested under an inner object
        # Check for reference to parent or sibling object (in case we dump from a lower level than root)
        if child_obj is obj:
            return self._ref_self_str(child_obj)

        if self.seen.get(id(child_obj)):
            return self._ref_earlier_str(child_obj)

        if isinstance(child_obj, self.multiconf_base_type):
            top = child_obj
            contained_in = child_obj._mc_contained_in
            if contained_in is obj:
                # This is the actual object, not a reference
                return child_obj

            while contained_in is not None:
                if contained_in is self.start_obj:
                    # We know we are referencing a later object, because it was not in 'seen'
                    return self._ref_later_str(child_obj)
                top = contained_in
                contained_in = contained_in._mc_contained_in
            else:
                # We found a reference to an item which is outside of the currently dumped hierarchy
                # Showing id(obj) does not help here as the object is not dumped, instead try to show some attributes which may identify the object
                ref_msg = "#outside-ref: "
                mc_key_msg = _attr_ref_msg(child_obj, 'mc_key')
                name_msg = _attr_ref_msg(child_obj, 'name')
                id_msg = _attr_ref_msg(child_obj, 'id')
                additionl_ref_info_msg = ', '.join([msg for msg in ( id_msg, name_msg, mc_key_msg) if msg])
                additionl_ref_info_msg = ': ' + additionl_ref_info_msg if additionl_ref_info_msg else ''
                return ref_msg + child_obj.__class__.__name__ + additionl_ref_info_msg

        return child_obj

    def __call__(self, obj):
        if ConfigItemEncoder.recursion_check.in_default:
            in_default = ConfigItemEncoder.recursion_check.in_default
            ConfigItemEncoder.recursion_check.in_default = None
            if self.recursion_check.warn_nesting:
                print("Warning: Nested json calls:", file=sys.stderr)
                print("outer object type:", type(in_default), file=sys.stderr)
                print("inner object type:", repr(type(obj)) + ", inner obj:", obj.json(compact=True, property_methods=False), file=sys.stderr)
            raise NestedJsonCallError("Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?")

        try:
            ConfigItemEncoder.recursion_check.in_default = obj

            if self.seen.get(id(obj)):
                return self._ref_earlier_str(obj)
            self.seen[id(obj)] = obj

            if isinstance(obj, self.multiconf_base_type):
                # Handle ConfigItems", type(obj)
                dd = self._mc_class_dict(obj)
                if not self.start_obj:
                    self.start_obj = obj

                    # Put 'env' once on the first object
                    dd['env'] = obj.env

                entries = ()
                try:
                    entries = dir(obj)
                except Exception as ex:
                    self.num_errors += 1
                    print("Error in json generation:", file=sys.stderr)
                    traceback.print_exception(*sys.exc_info())
                    dd['__json_error__ # trying to list property methods, failed call to dir(), @properties will not be included'] = repr(ex)

                # Handle attributes
                attributes_overriding_property = set()
                if self.sort_attributes:
                    attr_dict = {}
                else:
                    attr_dict = dd

                for key, mc_attr in obj._mc_attributes.items():
                    overridden_attr = False
                    try:
                        val = orig_val = mc_attr.env_values[obj.env]
                        if key in entries:
                            attributes_overriding_property.add(key)
                            overridden_attr = key + ' #!overrides @property'
                    except KeyError as ex:
                        # mc_attribute overriding @property OR the value for current env has not yet been set
                        try:
                            val = orig_val = getattr(obj, key)
                            overridden_attr = key + ' #value for current env provided by @property'
                        except AttributeError:
                            val = orig_val = McInvalidValue.MC_NO_VALUE

                    if self.user_filter_callable:
                        key, val = self.user_filter_callable(obj, key, val)
                        if key is False:
                            continue

                    if not self.builders and isinstance(val, self.multiconf_builder_type):
                        continue

                    val = self._check_nesting(obj, val)
                    if val != McInvalidValue.MC_NO_VALUE:
                        if isinstance(val, dict):
                            new_val = OrderedDict()
                            for inner_key, maybeitem in val.items():
                                if not isinstance(maybeitem, self.multiconf_base_type):
                                    new_val[inner_key] = maybeitem
                                    continue
                                new_val[inner_key] = self._ref_mc_item_str(maybeitem)
                            attr_dict[key] = new_val
                        else:
                            try:
                                iterable = iter(val)
                            except TypeError:
                                attr_dict[key] = val
                            else:
                                # TODO: Include type of iterable in json meta info
                                if isinstance(orig_val, str):
                                    attr_dict[key] = val
                                else:
                                    new_val = []
                                    found_mc_ref = False
                                    for maybeitem in val:
                                        if not isinstance(maybeitem, self.multiconf_base_type):
                                            new_val.append(maybeitem)
                                            continue
                                        found_mc_ref = True
                                        new_val.append(self._ref_mc_item_str(maybeitem))
                                    if found_mc_ref:
                                        attr_dict[key] = new_val
                                    else:
                                        # We leave this to be handled later
                                        attr_dict[key] = val

                    if overridden_attr:
                        attr_dict[overridden_attr] = True
                    if val == McInvalidValue.MC_NO_VALUE:
                        attr_dict[key + ' #no value for current env'] = True

                if self.sort_attributes:
                    for key in sorted(attr_dict):
                        dd[key] = attr_dict[key]

                for key, item in obj._mc_items.items():
                    if hasattr(item, '_mc_is_excluded') and item._mc_is_excluded():
                        if self.compact:
                            dd[key] = 'false #' + repr(item)
                            continue

                        dd[key] = False
                        dd[key + ' #' + repr(item)] = True
                        continue

                    dd[key] = item

                if not self.property_methods:
                    # Note also excludes class/static members
                    return dd

                for key in entries:
                    if key.startswith('_') or key in self.filter_out_keys or key in obj._mc_items:
                        continue

                    real_key = key
                    if key in attributes_overriding_property:
                        key += ' #!overridden @property'

                    try:
                        val = object.__getattribute__(obj, real_key)
                    except InvalidUsageException as ex:
                        self.num_invalid_usages += 1
                        dd[key + ' #invalid usage context'] = repr(ex)
                        continue
                    except Exception as ex:
                        self.num_errors += 1
                        traceback.print_exception(*sys.exc_info())
                        dd[key + ' # json_error trying to handle property method'] = repr(ex)
                        continue

                    if type(val) == types.MethodType:
                        continue

                    if self.user_filter_callable:
                        real_key, val = self.user_filter_callable(obj, real_key, val)
                        if real_key is False:
                            continue

                    if type(val) == type:
                        dd[key] = repr(val)
                        continue

                    val = self._check_nesting(obj, val)

                    # Figure out if the attribute is a @property or a static value
                    for cls in get_bases(object.__getattribute__(obj, '__class__')):
                        try:
                            real_attr = object.__getattribute__(cls, real_key)
                            if isinstance(real_attr, self.multiconf_property_wrapper_type):
                                val = real_attr.prop.__get__(obj, type(obj))
                                calc_or_static = _calculated_value
                            elif isinstance(real_attr, property):
                                calc_or_static = _calculated_value
                            else:
                                calc_or_static = _static_value
                            break
                        except AttributeError:
                            pass

                    if (self.compact or real_key in attributes_overriding_property) and isinstance(val, (str, int, long, float)):
                        dd[key] = str(val) + calc_or_static
                        continue

                    if isinstance(val, (list, tuple)):
                        new_list = []
                        for item in val:
                            new_list.append(self._check_nesting(obj, item))
                        dd[key] = new_list
                        dd[key + calc_or_static] = True
                        continue

                    if isinstance(val, dict):
                        new_dict = OrderedDict()
                        for item_key, item in val.items():
                            new_dict[item_key] = self._check_nesting(obj, item)
                        dd[key] = new_dict
                        dd[key + calc_or_static] = True
                        continue

                    dd[key] = val
                    dd[key + calc_or_static] = True
                return dd

            if isinstance(obj, envs.BaseEnv):
                # print "# Handle Env objects", type(obj)
                dd = OrderedDict((_class_tuple(obj),))
                if isinstance(obj, envs.EnvGroup):
                    for group in obj.groups:
                        dd['name'] = group.name
                for env in obj.envs:
                    dd['name'] = env.name
                return dd

            if type(obj) == type:
                return repr(obj)

            # If obj defines json_equivalent, then return the result of that
            if hasattr(obj, 'json_equivalent'):
                return obj.json_equivalent()

            try:
                iterable = iter(obj)
            except TypeError:
                pass
            else:
                # print "# Handle iterable objects", type(obj)
                return list(iterable)

            if self.user_fallback_callable:
                obj, handled = self.user_fallback_callable(obj)
                if handled:
                    return obj

            if major_version < 3 and isinstance(obj, types.InstanceType):
                # print "# Handle instances of old style classes", type(obj)
                # Note that new style class instances are practically indistinguishable from other types of objects
                dd = self._class_dict(obj)
                for key, val in obj.__dict__.items():
                    if key[0] != '_':
                        dd[key] = self._ref_earlier_str(val) if self.seen.get(id(val)) else val
                return dd

            self.num_errors += 1
            return "__json_error__ # don't know how to handle obj of type: " + repr(type(obj))

        finally:
            ConfigItemEncoder.recursion_check.in_default = None

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, os, threading, traceback
from collections import OrderedDict
import types

from . import envs
from .values import McInvalidValue
from .excluded import Excluded
from .repeatable import Repeatable
from .config_errors import InvalidUsageException

major_version = sys.version_info[0]
if major_version > 2:
    long = int

_warn_json_nesting = str(os.environ.get('MULTICONF_WARN_JSON_NESTING')).lower() == 'true'


class NestedJsonCallError(Exception):
    pass


def _class_tuple(obj, obj_info=""):
    return ('__class__', obj.__class__.__name__ + obj_info)


class ConfigItemEncoder(object):
    recursion_check = threading.local()
    recursion_check.in_default = None
    recursion_check.warn_nesting = _warn_json_nesting

    def __init__(self, filter_callable, fallback_callable, compact, property_methods, builders, warn_nesting,
                 multiconf_base_type, multiconf_root_type, multiconf_builder_type):
        """
        filter_callable: func(obj, key, value)
        - filter_callable is called for each key/value pair of attributes on each ConfigItem obj.
        - It must return a tuple of (key, value). If key is False, the key/value pair is removed from the json output

        fallback_callable: func(obj)
        - fallback_callable is called for objects that are not handled by the builtin encoder.
        - It must return a tupple (object, handled). If handled is True, the object must be encodable by the standard json encoder.

        compact: Set compact to true if dumping for debug, false for machine readable output.

        property_methods: call @property methods and insert values in output, including a comment that the value is calculated.
        """

        self.user_filter_callable = filter_callable
        self.user_fallback_callable = fallback_callable
        self.compact = compact
        self.property_methods = property_methods
        self.builders = builders
        self.multiconf_base_type = multiconf_base_type
        self.multiconf_root_type = multiconf_root_type
        self.multiconf_builder_type = multiconf_builder_type

        self.filter_out_keys = ('env', 'env_factory', 'contained_in', 'root_conf', 'attributes', 'frozen')
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
        not_frozen_msg = "" if obj.frozen else ", not-frozen"
        if self.compact:
            msg = " #as: '" + obj.named_as() + "', id: " + str(id(obj)) + not_frozen_msg
            return OrderedDict((_class_tuple(obj, msg),))
        return OrderedDict((_class_tuple(obj, not_frozen_msg), ('__id__', id(obj))))

    def _already_dumped_str(self, objval):
        return "#ref, id: " + repr(id(objval))

    def _check_nesting(self, obj, child_obj):
        # Returns child_obj or reference info string
        # Check that object being dumped is actually contained in self
        # We dont want to display an outer/sibling object as nested under an inner object
        # Check for reference to parent or sibling object (in case we dump from a lower level than root)
        if child_obj is obj:
            return "#ref self, id: " + repr(id(child_obj))

        if self.seen.get(id(child_obj)):
            return self._already_dumped_str(child_obj)

        if isinstance(child_obj, self.multiconf_base_type):
            top = child_obj
            contained_in = child_obj._mc_contained_in
            if contained_in is obj:
                return child_obj

            while contained_in:
                if contained_in is self.start_obj:
                    return "#ref later, id: " + repr(id(child_obj))
                top = contained_in
                contained_in = contained_in._mc_contained_in
            else:
                ref_msg = '#original-cloned-item-ref: ' if not isinstance(top, self.multiconf_root_type) else "#outside-ref: "
                id_msg = ": id: " + repr(child_obj.id) if hasattr(child_obj, 'id') else ''
                name_msg = ", name: " + repr(child_obj.name) if hasattr(child_obj, 'name') else ''
                return ref_msg + child_obj.__class__.__name__ + id_msg + name_msg

        return child_obj

    def __call__(self, obj):
        if ConfigItemEncoder.recursion_check.in_default:
            in_default = ConfigItemEncoder.recursion_check.in_default
            ConfigItemEncoder.recursion_check.in_default = None
            if self.recursion_check.warn_nesting:
                print("Warning: Nested json calls:", file=sys.stderr)
                print("outer object type:", type(in_default), file=sys.stderr)
                print("inner object type:", repr(type(obj)) + ", inner obj:", obj, file=sys.stderr)
            raise NestedJsonCallError("Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?")

        try:
            ConfigItemEncoder.recursion_check.in_default = obj
            if not self.start_obj:
                self.start_obj = obj

            if self.seen.get(id(obj)):
                return self._already_dumped_str(obj)
            self.seen[id(obj)] = obj

            if isinstance(obj, self.multiconf_base_type):
                # print("# Handle ConfigItems", type(obj))
                dd = self._mc_class_dict(obj)

                entries = ()
                try:
                    entries = dir(obj)
                except Exception as ex:
                    self.num_errors += 1
                    print("Error in json generation:", file=sys.stderr)
                    traceback.print_exception(*sys.exc_info())
                    dd['__json_error__ # trying to list property methods, failed call to dir(), @properties will not be included'] = repr(ex)

                # Order 'env' first on root object
                if isinstance(obj, self.multiconf_root_type):
                    dd['env'] = obj.env

                # Handle attributes
                attributes_overriding_property = set()
                attr_dict = {}
                item_dict = OrderedDict()
                for key, item in obj._iterattributes():
                    val = orig_val = item._mc_value()

                    if self.user_filter_callable:
                        key, val = self.user_filter_callable(obj, key, val)
                        if key is False:
                            continue

                    if not self.builders and isinstance(val, self.multiconf_builder_type):
                        continue

                    val = self._check_nesting(obj, val)
                    if isinstance(val, Excluded):
                        if self.compact:
                            item_dict[key] = 'false #' + repr(val)
                        else:
                            item_dict[key] = False
                            item_dict[key + ' #' + repr(val)] = True
                    elif val != McInvalidValue.MC_NO_VALUE:
                        if isinstance(orig_val, (self.multiconf_base_type, Repeatable)):
                            item_dict[key] = val
                        elif isinstance(val, dict):
                            for inner_key, maybeitem in val.items():
                                if isinstance(maybeitem, self.multiconf_base_type):
                                    val[inner_key] = "#ref, id: " + repr(id(maybeitem))
                            attr_dict[key] = val
                        else:
                            try:
                                iterable = iter(val)
                            except TypeError:
                                pass
                            else:
                                if isinstance(val, tuple):
                                    val = list(val)
                                for index, maybeitem in enumerate(val):
                                    if isinstance(maybeitem, self.multiconf_base_type):
                                        val[index] = "#ref, id: " + repr(id(maybeitem))
                            attr_dict[key] = val

                    if key in entries:
                        if val != McInvalidValue.MC_NO_VALUE:
                            attributes_overriding_property.add(key)
                            attr_dict[key + ' #!overrides @property'] = True
                        else:
                            attr_dict[key + ' #value for current env provided by @property'] = True
                    elif val == McInvalidValue.MC_NO_VALUE:
                        attr_dict[key + ' #no value for current env'] = True

                for key in sorted(attr_dict):
                    dd[key] = attr_dict[key]
                dd.update(item_dict)
                if not self.property_methods:
                    return dd

                # Handle @property methods (defined in subclasses)
                overridden_property_postfix = ' #!overridden @property'
                for key in entries:
                    if key.startswith('_') or key in self.filter_out_keys:
                        continue

                    real_key = key
                    if key in attributes_overriding_property:
                        key += overridden_property_postfix

                    try:
                        val = object.__getattribute__(obj, real_key)
                    except InvalidUsageException as ex:
                        self.num_invalid_usages += 1
                        dd[key + ' #invalid usage context'] = repr(ex)
                        continue
                    except Exception as ex:
                        self.num_errors += 1
                        print("Error in json generation:", file=sys.stderr)
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
                    if (self.compact or real_key in attributes_overriding_property) and isinstance(val, (str, int, long, float)):
                        dd[key] = str(val) + ' #calculated'
                        continue

                    if isinstance(val, (list, tuple)):
                        new_list = []
                        for item in val:
                            new_list.append(self._check_nesting(obj, item))
                        dd[key] = new_list
                        dd[key + ' #calculated'] = True
                        continue

                    if isinstance(val, dict):
                        new_dict = OrderedDict()
                        for item_key, item in val.items():
                            new_dict[item_key] = self._check_nesting(obj, item)
                        dd[key] = new_dict
                        dd[key + ' #calculated'] = True
                        continue

                    dd[key] = val
                    dd[key + ' #calculated'] = True
                return dd

            if isinstance(obj, envs.BaseEnv):
                # print "# Handle Env objects", type(obj)
                dd = OrderedDict((_class_tuple(obj),))
                for eg in obj.all:
                    dd['name'] = eg.name
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
                        dd[key] = self._already_dumped_str(val) if self.seen.get(id(val)) else val
                return dd

            self.num_errors += 1
            return "__json_error__ # don't know how to handle obj of type: " + repr(type(obj))

        finally:
            ConfigItemEncoder.recursion_check.in_default = None


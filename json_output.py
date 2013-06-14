# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys, threading, traceback
from collections import OrderedDict
import json
import types

import multiconf, envs
from .excluded import Excluded
from .config_errors import InvalidUsageException


class NestedJsonCallError(Exception):
    pass


def _class_tuple(obj, obj_info=""):
    return ('__class__', obj.__class__.__name__ + obj_info)


class ConfigItemEncoder(json.JSONEncoder):
    recursion_check = threading.local()
    recursion_check.in_default = None

    def __init__(self, filter_callable=None, fallback_callable=None, compact=False, property_methods=True, builders=False, warn_nesting=False, **kwargs):
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
        super(ConfigItemEncoder, self).__init__(**kwargs)
        self.filter_out_keys = ('env', 'valid_envs', 'contained_in', 'root_conf', 'attributes', 'frozen')
        self.user_filter_callable = filter_callable
        self.user_fallback_callable = fallback_callable
        self.compact = compact
        self.property_methods = property_methods
        self.seen = {}
        self.start_obj = None
        self.builders = builders
        self.warn_nesting = warn_nesting

    def _class_dict(self, obj):
        if self.compact:
            return OrderedDict((_class_tuple(obj, ' #id: ' + repr(id(obj))),))
        return OrderedDict((_class_tuple(obj), ('__id__', id(obj))))

    def _mc_class_dict(self, obj):
        not_frozen_msg = "" if obj.frozen else ", not-frozen"
        if self.compact:
            msg = " #as: '" + obj.named_as() + "', id: " + str(id(obj)) + not_frozen_msg
            return OrderedDict((_class_tuple(obj, msg),))
        return OrderedDict(( _class_tuple(obj, not_frozen_msg), ('__id__', id(obj))))

    def _check_already_dumped(self, objval):
        # Return (new)objval, done
        # Check for reference to already dumped objects
        return ("#ref id: " + repr(id(objval)), True) if self.seen.get(id(objval)) else (objval, False)

    def _set_already_dumped(self, obj):
        self.seen[id(obj)] = obj

    def _check_nesting(self, obj, child_obj):
        # Returns child_obj or reference info string
        # Check that object being dumped is actually contained in self
        # We dont want to display an outer/sibling object as nested under an inner object
        # Check for reference to parent or sibling object (in case we dump from a lower level than root)
        if child_obj is obj:
            return "#ref self, id: " + repr(id(child_obj))

        child_obj, done = self._check_already_dumped(child_obj)

        if not done and isinstance(child_obj, multiconf._ConfigBase):
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
                ref_msg = '#original-cloned-item-ref: ' if not isinstance(top, multiconf.ConfigRoot) else "#outside-ref: "
                id_msg = ": id: " + repr(child_obj.id) if hasattr(child_obj, 'id') else ''
                name_msg = ", name: " + repr(child_obj.name) if hasattr(child_obj, 'name') else ''
                return ref_msg + child_obj.__class__.__name__ + id_msg + name_msg

        return child_obj

    def encode(self, obj, **kwargs):
        #print(self.__class__.__name__, "encode: type(obj)", type(obj), kwargs)
        return super(ConfigItemEncoder, self).encode(obj, **kwargs)

    def iterencode(self, obj, **kwargs):
        #print(self.__class__.__name__, "iterencode: type(obj)", type(obj), kwargs)
        return super(ConfigItemEncoder, self).iterencode(obj, **kwargs)

    # pylint: disable=E0202
    def default(self, obj):
        if ConfigItemEncoder.recursion_check.in_default:
            in_default = ConfigItemEncoder.recursion_check.in_default
            ConfigItemEncoder.recursion_check.in_default = None
            if self.warn_nesting:
                print("Warning: Nested json calls:", file=sys.stderr)
                print("outer object type:", type(in_default), file=sys.stderr)
                print("inner object type:", repr(type(obj)) + ", inner obj:", obj, file=sys.stderr)
            raise NestedJsonCallError("Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?")

        try:
            ConfigItemEncoder.recursion_check.in_default = obj
            if not self.start_obj:
                self.start_obj = obj

            obj, dumped = self._check_already_dumped(obj)
            if dumped:
                return obj
            self._set_already_dumped(obj)

            if isinstance(obj, multiconf._ConfigBase):
                # print("# Handle ConfigItems", type(obj))
                dd = self._mc_class_dict(obj)

                entries = ()
                try:
                    entries = dir(obj)
                except Exception as ex:
                    print("Error in json generation:", file=sys.stderr)
                    traceback.print_exception(*sys.exc_info())
                    dd['__json_error__ # trying to list property methods, failed call to dir(), @properties will not be included'] = repr(ex)

                # Order 'env' first on root object
                if isinstance(obj, multiconf.ConfigRoot):
                    dd['env'] = obj.env

                # Handle attributes
                for key, val in obj.iteritems():
                    if self.user_filter_callable:
                        key, val = self.user_filter_callable(obj, key, val)
                        if key is False:
                            continue

                    if not self.builders and isinstance(val, multiconf.ConfigBuilder):
                        continue

                    val = self._check_nesting(obj, val)
                    if key in entries:
                        dd[key + ' #shadowed'] = val
                        continue

                    if isinstance(val, Excluded):
                        if self.compact:
                            dd[key] = 'false #' + repr(val)
                            continue

                        dd[key] = False
                        dd[key + ' #' + repr(val)] = True
                        continue

                    dd[key] = val

                if not self.property_methods:
                    return dd

                # Handle @property methods (defined in subclasses)
                for key in entries:
                    if key.startswith('_') or key in self.filter_out_keys:
                        continue

                    try:
                        val = getattr(obj, key)
                    except InvalidUsageException as ex:
                        dd[key + ' #invalid usage context'] = repr(ex)
                        continue
                    except Exception as ex:
                        print("Error in json generation:", file=sys.stderr)
                        traceback.print_exception(*sys.exc_info())
                        dd[repr(key) + ' # json_error trying to handle property method'] = repr(ex)
                        continue

                    if type(val) == types.MethodType:
                        continue

                    if self.user_filter_callable:
                        key, val = self.user_filter_callable(obj, key, val)
                        if key is False:
                            continue

                    val = self._check_nesting(obj, val)

                    if self.compact and isinstance(val, (str, int, long, float)):
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
                        for item_key, item in val.iteritems():
                            new_dict[item_key] = self._check_nesting(obj, item)
                        dd[key] = new_dict
                        dd[key + ' #calculated'] = True
                        continue

                    dd[key] = val
                    dd[key + ' #calculated'] = True
                return dd

            if isinstance(obj, envs.BaseEnv):
                #print "# Handle Env objects", type(obj)
                dd = OrderedDict((_class_tuple(obj),))
                for eg in obj.all():
                    dd['name'] = eg.name
                return dd

            # If obj defines json_equivalent, then return the result of that
            if hasattr(obj, 'json_equivalent'):
                return obj.json_equivalent()

            try:
                iterable = iter(obj)
            except TypeError:
                pass
            else:
                #print "# Handle iterable objects", type(obj)
                return list(iterable)

            if self.user_fallback_callable:
                obj, handled = self.user_fallback_callable(obj)
                if handled:
                    return obj

            if isinstance(obj, types.InstanceType):
                #print "# Handle instances of old style classes", type(obj)
                # Note that new style class instances are practically indistinguishable from other types of objects
                dd = self._class_dict(obj)
                for key, val in obj.__dict__.iteritems():
                    if key[0] != '_':
                        dd[key], _dumped = self._check_already_dumped(val)
                return dd

            return "__json_error__ # don't know how to handle obj of type: " + repr(type(obj))

        finally:
            ConfigItemEncoder.recursion_check.in_default = None

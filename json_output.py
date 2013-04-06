import sys, threading, traceback
from collections import OrderedDict, Sequence
import json
import types

import multiconf, envs
from .config_errors import InvalidUsageException


class NestedJsonCallError(Exception):
    pass


def _class_tuple(obj, obj_info=""):
    return ('__class__', obj.__class__.__name__ + obj_info)


class ConfigItemEncoder(json.JSONEncoder):
    recursion_check = threading.local()
    recursion_check.in_default = False

    def __init__(self, filter_callable=None, compact=False, property_methods=True, **kwargs):
        """
        filter_callable: func(obj, key, value)
        - filter_callable is called for each key/value pair of attributes on each ConfigItem obj.
        - It it must return a tuple of (key, value). If key is False, the key/value pair is removed from the json output
        compact: Set compact to true if dumping for debug, false for machine readable output.
        property_methods: call @property methods and insert values in output, including a comment that the value is calculated.
        """
        super(ConfigItemEncoder, self).__init__(**kwargs)
        self.filter_out_keys = ('env', 'valid_envs', 'contained_in', 'root_conf', 'attributes', 'frozen')
        self.user_filter_callable = filter_callable
        self.compact = compact
        self.property_methods = property_methods
        self.seen = {}
        self.start_obj = None

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
        # Returns (new)val
        # Check that object being dumped is actually contained in self
        # We dont want to display an outer/sibling object as nested under an inner object
        # Check for reference to parent or sibling object (in case we dump from a lower level than root)
        if child_obj is obj:
            return "#ref self, id: " + repr(id(child_obj))

        child_obj, done = self._check_already_dumped(child_obj)

        if not done and isinstance(child_obj, multiconf._ConfigBase):
            contained_in = child_obj.contained_in
            if contained_in is obj:
                return child_obj

            while contained_in:
                if contained_in is self.start_obj:
                    return "#ref later, id: " + repr(id(child_obj))
                contained_in = contained_in.contained_in
            else:
                id_msg = ": id: " + repr(child_obj.id) if hasattr(child_obj, 'id') else ''
                name_msg = ", name: " + repr(child_obj.name) if hasattr(child_obj, 'name') else ''
                child_obj = "#outside-ref: " + child_obj.__class__.__name__ + id_msg + name_msg

        return child_obj

    def encode(self, obj, **kwargs):
        #print self.__class__.__name__, "encode: type(obj)", type(obj)
        return super(ConfigItemEncoder, self).encode(obj, **kwargs)

    def iterencode(self, obj, **kwargs):
        #print self.__class__.__name__, "iterencode: type(obj)", type(obj)
        return super(ConfigItemEncoder, self).iterencode(obj, **kwargs)

    # pylint: disable=E0202
    def default(self, obj):
        if ConfigItemEncoder.recursion_check.in_default:
            # print >> sys.stderr, self.__class__.__name__, "json_output.default: type(obj)", type(obj)
            raise NestedJsonCallError("Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?")

        try:
            ConfigItemEncoder.recursion_check.in_default = True
            if not self.start_obj:
                self.start_obj = obj

            obj, dumped = self._check_already_dumped(obj)
            if dumped:
                return obj
            self._set_already_dumped(obj)

            if isinstance(obj, multiconf._ConfigBase):
                #print "# Handle ConfigItems", type(obj)
                dd = self._mc_class_dict(obj)

                entries = ()
                try:
                    entries = dir(obj)
                except Exception as ex:
                    print >> sys.stderr, "Error in json generation:"
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

                    val = self._check_nesting(obj, val)
                    if key in entries:
                        dd[key + ' #shadowed'] = val
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
                        print >> sys.stderr, "Error in json generation:"
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

            try:
                iterable = iter(obj)
            except TypeError:
                pass
            else:
                #print "# Handle iterable objects", type(obj)
                return list(iterable)

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
            ConfigItemEncoder.recursion_check.in_default = False

import sys, threading
from collections import OrderedDict
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
        compact: Set compact to true if dumping for debug, false for machine readable output
        property_methods: call @property methods and insert values in output, including a comment that the value is calculated
        """
        super(ConfigItemEncoder, self).__init__(**kwargs)
        self.root_special_keys = ('env', 'valid_envs')
        self.filter_out_keys = self.root_special_keys + ('selected_env', 'contained_in', 'root_conf', 'attributes', 'frozen')
        self.user_filter_callable = filter_callable        
        self.compact = compact
        self.property_methods = property_methods
        self.seen = {}

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

    def _check_already_dumped(self, obj):
        # Check for reference to already dumped objects
        original = self.seen.get(id(obj))
        if original:
            return "#ref id: " + repr(id(obj))
        return False

    def _set_already_dumped(self, obj):
        self.seen[id(obj)] = obj

    def _check_nesting_level(self, current_nesting_level, child_obj):
        # Check for reference to parent or sibling object (in case we dump from a lower level than root)
        # We dont want to display an outer/sibling object as nested under an inner object
        dumped = self._check_already_dumped(child_obj)
        if dumped:
            return dumped

        if isinstance(child_obj, multiconf._ConfigBase):
            if child_obj._nesting_level <= current_nesting_level:
                id_msg = ": id: " + child_obj.id if hasattr(child_obj, 'id') else ''
                name_msg = ", name: " + child_obj.name if hasattr(child_obj, 'name') else ''
                return "#outside-ref: " + repr(type(child_obj)) + id_msg + name_msg
        return False

    def encode(self, obj, **kwargs):
        #print self.__class__.__name__, "encode: type(obj)", type(obj)        
        return super(ConfigItemEncoder, self).encode(obj, **kwargs)

    def iterencode(self, obj, **kwargs):
        #print self.__class__.__name__, "iterencode: type(obj)", type(obj)        
        return super(ConfigItemEncoder, self).iterencode(obj, **kwargs)

    # pylint: disable=E0202
    def default(self, obj):
        try:
            if ConfigItemEncoder.recursion_check.in_default:
                # print >> sys.stderr, self.__class__.__name__, "json_output.default: type(obj)", type(obj)
                raise NestedJsonCallError("Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?")
            ConfigItemEncoder.recursion_check.in_default = True

            dumped = self._check_already_dumped(obj)
            if dumped:
                return dumped
            self._set_already_dumped(obj)

            if isinstance(obj, multiconf._ConfigBase):
                #print "# Handle ConfigItems", type(obj)
                dd = self._mc_class_dict(obj)

                # Order 'env' first on root object                
                if isinstance(obj, multiconf.ConfigRoot):
                    key = self.root_special_keys[0]
                    value = getattr(obj, key)
                    dd[key] = value
    
                # Handle attributes
                for key, val in obj.iteritems():
                    if key in self.filter_out_keys:
                        continue

                    dumped = self._check_nesting_level(obj._nesting_level, val)
                    if dumped:
                        dd[key] = dumped
                        continue
                    
                    dd[key] = val
    
                if not self.property_methods:
                    return dd

                # Handle property methods (defined in subclasses)
                try:
                    for key in dir(obj):
                        if key.startswith('_') or key in self.filter_out_keys or key in obj.attributes:
                            continue
                        
                        try:
                            val = getattr(obj, key)
                        except InvalidUsageException as ex:
                            dd[key + ' #invalid usage context'] = repr(ex)
                            continue
                        except RuntimeError:
                            raise
                        except:
                            # TODO
                            #print >> sys.stderr, "Error in json generation:"
                            #print >> sys.stderr, traceback.format_exc()
                            dd[repr(key) + ' # json_error trying to handle property method'] = repr(sys.exc_info()[1])
                            continue
                    
                        if type(val) == types.MethodType:
                            continue

                        dumped = self._check_nesting_level(obj._nesting_level, val)
                        if dumped:
                            dd[key] = dumped
                            continue
                    
                        if self.compact:
                            dd[key] = str(val) + ' #calculated'
                            continue

                        dd[key] = val
                        dd[key + ' #calculated'] = True
                    
                    return dd
                except RuntimeError:
                    raise
                except:
                    #print >> sys.stderr, "Error in json generation:"
                    #print >> sys.stderr, traceback.format_exc()
                    dd['__json_error__ # trying to handle property methods'] = repr(sys.exc_info()[1])
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
                        dumped = self._check_already_dumped(val)
                        if dumped:
                            dd[key] = dumped
                            continue
                        dd[key] = val
                return dd

            return "__json_error__ # don't know how to handle obj of type: " + repr(type(obj))

        finally:
            ConfigItemEncoder.recursion_check.in_default = False


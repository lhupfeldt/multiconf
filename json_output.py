import sys, traceback, threading
from collections import OrderedDict
import json
import types

import multiconf, envs
from config_errors import InvalidUsageException

# For handling references to avoid dumping objects multiple times
class _AlreadySeen(Exception):
    pass


# For handling references to avoid dumping objects multiple times
class NestedJsonCallError(Exception):
    pass


def _class_tuple(obj, obj_info=""):
    return ('__class__', obj.__class__.__name__ + obj_info)


class ConfigItemEncoder(json.JSONEncoder):
    recursion_check = threading.local()
    recursion_check.in_default = False
        
    def __init__(self, filter_callable=None, compact=False, **kwargs):
        """
        filter_callable: func(obj, key, value)
        compact: Set compact to true if dumping for debug, false for machine readable output
        """
        super(ConfigItemEncoder, self).__init__(**kwargs)
        self.filter = filter_callable
        self.compact = compact
        self.seen = {}

    def _class_dict(self, obj):
        if self.compact:
            return OrderedDict((_class_tuple(obj, ' #id: ' + repr(id(obj))),))
        return OrderedDict((_class_tuple(obj), ('__id__', id(obj))))

    def _mc_class_dict(self, obj):
        not_frozen_msg = "" if obj.frozen else ", not-frozen, defaults: " + repr(obj._defaults)
        if self.compact:
            msg = " #as: " + repr(obj.named_as()) + ', id: ' + repr(id(obj)) + not_frozen_msg
            return OrderedDict((_class_tuple(obj, msg),))
        return OrderedDict(( _class_tuple(obj, not_frozen_msg), ('__id__', id(obj))))

    def _check_already_dumped(self, obj):
        # Check for references to already dumped objects
        original = self.seen.get(id(obj))
        if original:
            raise _AlreadySeen("#ref id: " + repr(id(obj)))

        self.seen[id(obj)] = obj

    # pylint: disable=E0202
    def default(self, obj):        
        try:
            if ConfigItemEncoder.recursion_check.in_default:
                raise NestedJsonCallError("Nested json calls detected. Maybe a @property method calls json or repr (implicitly)?")
            ConfigItemEncoder.recursion_check.in_default = True

            self._check_already_dumped(obj)

            if isinstance(obj, multiconf._ConfigBase):
                #print "# Handle ConfigItems", type(obj)
                dd = self._mc_class_dict(obj)
                # Order 'env' first on root object
                root_special_keys = ('env', 'valid_envs')
                is_root = isinstance(obj, multiconf.ConfigRoot)
                if is_root:
                    key = root_special_keys[0]
                    value = getattr(obj, key)
                    dd[key] = value
    
                # Handle attributes
                for key, val in obj.iteritems():
                    if key[0] != '_':
                        dd[key] = val
    
                # Handle property methods (defined in inherited classes)
                try:
                    for key in dir(obj):
                        if key in obj.attributes or key.startswith('_'):
                            continue
                        if key in ('selected_env', 'contained_in', 'root_conf', 'attributes', 'frozen'):
                            continue
                        if key in root_special_keys:
                            continue
                    
                        try:
                            val = getattr(obj, key)
                            self._check_already_dumped(val)
                        except InvalidUsageException as ex:
                            dd[key + ' #invalid usage context'] = repr(ex)
                            continue
                        except _AlreadySeen as seen:
                            dd[key] = seen.message
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
                    
                        if key in ('valid_envs', 'env'):
                            dd[key] = val
                            continue
                    
                        if self.compact:
                            dd[key] = str(val) + ' #calculated'
                        else:
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
    
            if isinstance(obj, envs.Env):
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
    
            try:
                odict = obj.__dict__
            except AttributeError:
                pass
            else:
                #print "# Handle other class objects", type(obj)
                dd = self._class_dict(obj)
                for key, val in obj.__dict__.iteritems():
                    if key[0] != '_':
                        self._check_already_dumped(val)
                        dd[key] = val
                return dd
    
            #print "# Handle builtin types", type(obj)
            return obj

        except _AlreadySeen as seen:
            return seen.message
        finally:
            ConfigItemEncoder.recursion_check.in_default = False


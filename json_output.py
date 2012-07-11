from collections import OrderedDict
import json
import types

import multiconf, envs
from config_errors import InvalidUsageException

# Note: this is used for handling backreferences to avoid dumping objects multiple times
class _AlreadySeen(Exception):
    pass


def _class_tuple(obj, id_str=""):
    return ('__class__', obj.__class__.__name__ + id_str)


class ConfigItemEncoder(json.JSONEncoder):
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

    def _check_already_dumped(self, obj):
        # Check for references to already dumped objects
        original = self.seen.get(id(obj))
        if original:
            raise _AlreadySeen("#ref id: " + repr(id(obj)))

        self.seen[id(obj)] = obj

    def default(self, obj):
        try:
            if isinstance(obj, multiconf._ConfigBase):
                #print "# Handle ConfigItems", type(obj)
                self._check_already_dumped(obj)
                dd = self._class_dict(obj)
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
                for key in dir(obj):
                    if key in obj.attributes or key.startswith('_'):
                        continue
                    if key in ('selected_env', 'contained_in', 'root_conf', 'attributes'):
                        continue
                    if key in root_special_keys:
                        continue
    
                    try:
                        val = getattr(obj, key)
                    except InvalidUsageException:
                        dd[key + ' #invalid usage context'] = True
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
    
            if isinstance(obj, envs.Env):
                #print "# Handle Env objects", type(obj)
                self._check_already_dumped(obj)
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
                self._check_already_dumped(obj)    
                return list(iterable)
    
            try:
                odict = obj.__dict__
            except AttributeError:
                pass
            else:
                #print "# Handle other class objects", type(obj)
                self._check_already_dumped(obj)
                dd = self._class_dict(obj)
                for key, val in obj.__dict__.iteritems():
                    if key[0] != '_':
                        dd[key] = val
                return dd
    
            print "# Handle builtin types", type(obj)
            return obj


        except _AlreadySeen as seen:
            return seen.message

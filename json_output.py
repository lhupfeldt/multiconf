from collections import OrderedDict
import json
import types

import multiconf, envs


class ConfigItemEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        super(ConfigItemEncoder, self).__init__(**kwargs)
        self.seen = {}

    def default(self, obj):
        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)

        if isinstance(obj, multiconf._ConfigBase):
            # Handle ConfigItems
            original = self.seen.get(id(obj))
            if original:
                where = [original.named_as()]
                while original:
                    original = original.contained_in
                    if original:
                        where = [original.named_as()] + where
                return "#confitem ref: " + '.'.join(where)

            self.seen[id(obj)] = obj

            d = OrderedDict((('__class__', obj.__class__.__name__ ),))

            # Order 'env' and first on root object
            root_special_keys = ('env', 'valid_envs')
            is_root = isinstance(obj, multiconf.ConfigRoot)
            if is_root:
                key = root_special_keys[0]
                value = obj.__getattribute__(key)
                d[key] = value                
            
            # Handle attributes
            for key, val in obj.iteritems():
                if key[0] != '_':
                    d[key] = val

            # Handle property methods (defined in inherited classes)
            for key in dir(obj):
                if key in obj.attributes or key.startswith('_'):
                    continue
                if key in ('selected_env', 'contained_in', 'root_conf', 'attributes'):
                    continue
                if key in root_special_keys:
                    continue

                value = obj.__getattribute__(key)
                if type(value) == types.MethodType:
                    continue

                d[key] = value
                if not key in ('valid_envs', 'env'):
                    d[key + ' #calculated'] = True

            return d

        if isinstance(obj, envs.Env):
            d = OrderedDict((('__class__', obj.__class__.__name__ ),))
            for eg in obj.all():
                d['name'] = eg.name
            return d

        try:
            # Handle other objects
            d = OrderedDict((('__class__', obj.__class__.__name__ ),))
            for key, val in obj.__dict__.iteritems():
                if key[0] != '_':
                    d[key] = val
            for key in dir(obj):
                if not key in obj.__dict__ and not key.startswith('__'):                    
                    value = obj.__getattribute__(key)
                    if type(value) == types.MethodType:
                        continue
                    d[key] = value
                    d[key + ' #calculated'] = True                        
            return d
        except AttributeError:
            pass

        # Handle builtin types
        return super.default(self, obj)

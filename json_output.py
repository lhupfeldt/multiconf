import json
import types

import multiconf


class ConfigItemEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)

        if isinstance(obj, multiconf._ConfigBase):
            d = {'__class__':obj.__class__.__name__ }
            for key, val in obj.iteritems():
                if key[0] != '_':
                    d[key] = val
            for key in dir(obj):
                if not key in obj.attributes and not key.startswith('_'):
                    if key in ('selected_env', 'contained_in', 'root_conf', 'attributes'):
                        continue
                    if not isinstance(obj, multiconf.ConfigRoot):
                        if key in ('valid_envs', 'env'):
                            continue
                    value = obj.__getattribute__(key)
                    if type(value) == types.MethodType:
                        continue
                    d[key] = value
                    d[key + ' #calculated'] = True
            return d

        try:
            d = {'__class__':obj.__class__.__name__ }
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

        return json.JSONEncoder.default(self, obj)

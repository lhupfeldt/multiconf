# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
from collections import Sequence, namedtuple
import inspect
from attrdict import AttrDict
from envs import Env, EnvGroup, env_or_group, EnvException


def required(attr_names):
    def deco(cls):
        cls._deco_required_attributes = [attr.strip() for attr in attr_names.split(',')]
        return cls

    return deco


class ConfigException(Exception):
    pass


_Traceback = namedtuple('Traceback', 'filename, lineno, function, code_context, index')

def _error_msg(num_errors, message):
    tb = _Traceback(*inspect.stack()[2][1:])
    print >>sys.stderr, 'File "' + tb.filename + '", line', tb.lineno
    print >>sys.stderr, 'ConfigError:', message
    return num_errors + 1


class AttributeCollector(object):
    def __init__(self, attribute_name, container):
        self._attribute_name = attribute_name
        self._container = container
        self._env_values = {}
        self._frozen = False

    def __call__(self, **kwargs):
        self._frozen = True

        if self._attribute_name in self._container._attributes:
            _error_msg(0, "Redefined attribute " + repr(self._attribute_name))
            raise ConfigException("Attribute redefinition error: " + repr(self._attribute_name))

        self._container._attributes[self._attribute_name] = self

        # For error messages
        eg_from = {}
        errors = 0

        attr_types = set()

        defaults = self._container._defaults
        if self._attribute_name in defaults:
            attr_types.add(type(defaults[self._attribute_name]))

        # Validate and assign given env values to container
        for eg_name, value in kwargs.iteritems():
            try:
                eg = env_or_group(eg_name)

                # Validate that an attribute has the same type for all envs
                if type(value) not in attr_types and attr_types:
                    msg = "Found different types of property " + repr(self._attribute_name) + " for different envs: " + repr(type(value)) + " previously found types: " + repr(list(attr_types))
                    errors = _error_msg(errors, msg)
                attr_types.add(type(value))

                # TODO: allow env overrides group, allow group nested override?
                for env in eg.envs():
                    if env in self._env_values:
                        new_eg_msg = repr(env) + ("" if env == eg else " from group " + repr(eg))
                        prev_eg_msg = repr(eg_from[env])
                        msg = "A value is already specified for: " + new_eg_msg + '=' + repr(value) + ", previous value: " + prev_eg_msg + '=' + repr(self._env_values[env])
                        errors = _error_msg(errors, msg)

                    self._env_values[env] = value
                    eg_from[env] = eg

            except EnvException as ex:
                errors = _error_msg(errors, ex.message)

        # Validate that the attribute is defined for all envs / assign default value
        for eg in self._container._root_conf._valid_envs:
            for env in eg.envs():
                if env in self._env_values:
                    continue
                if self._attribute_name in defaults:
                    self._env_values[env] = defaults[self._attribute_name]
                    continue
                group_msg = ", which is a member of " + repr(eg) if isinstance(eg, EnvGroup) else ""
                msg = "Attribute: " + repr(self._attribute_name) + " did not receive a value for env " + repr(env)
                errors = _error_msg(errors, msg + group_msg)

        if self._attribute_name in defaults:
            del defaults[self._attribute_name]

        if errors:
            raise ConfigException("There were " + repr(errors) + " errors when defining attribute " + repr(self._attribute_name))

        return self

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__ and __call__
            super(AttributeCollector, self).__setattr__(name, value)
            return
        raise ConfigException("Trying to set a property " + repr(name) + " on an attribute collector")

    def __repr__(self):
        return self.__class__.__name__ + ': ' + repr(self._attribute_name) + ':' + ('frozen' if self._frozen else 'not-frozen') + ", values: " + repr(self._env_values)

    def value(self):
        if not self._frozen:
            raise ConfigException("Attribute " + repr(self._attribute_name) + " is not frozen.")
        return self._container.getattr_env(self._attribute_name, self._container._root_conf._selected_env)

    @property
    def env_values(self):
        return self._env_values


class _ConfigBase(object):
    nested = []

    def __init__(self, **attr):
        self._debug_exc = True

        # Object linking
        self._root_conf = None
        self._nesting_level = 0

        # Dict of dicts: attributes['a'] = dict(Env('prod')=1, EnvGroup('dev')=0)
        self._attributes = {}
        self._defaults = attr

        # Decoration attributes
        self._deco_required_attributes = []

        self._name = self.__class__.__name__
        self._finalized = True

    def irepr(self, indent_level):
        """Indented repr"""
        indent1 = '  ' * indent_level
        indent2 =  indent1 + '     '
        return self._name + ' {\n' + \
            ''.join([indent2 + name + ': ' + repr(value) + ',\n' for name, value in self.iteritems()]) + \
            indent1 + '}'

    def __repr__(self):
        return self.irepr(self._nesting_level)

    def __enter__(self):
        self._nesting_level = len(self.__class__.nested)
        self.__class__.nested.append(self)
        self._finalized = False
        return self

    def _exit_validate_required(self):
        for req in self._deco_required_attributes:
            if not req in self._attributes:
                raise ConfigException("No value given for required attribute " + repr(req))

    def exit_validation(self):
        """Override this method if you need special checks"""
        self._exit_validate_required()

    def __exit__(self, exc_type, exc_value, traceback):
        self.__class__.nested.pop()

        if exc_type:
            return None

        try:
            self.exit_validation()
        except ConfigException as ex:
            if self._debug_exc:
                raise
            # Strip stack
            raise ex

        # Collect remaining default values
        for name in list(self._defaults):
            AttributeCollector(name, self)()
        self._finalized = True

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__
            super(_ConfigBase, self).__setattr__(name, value)
            return
        raise ConfigException("Trying to set a property " + repr(name) + " on a config item")

    def _check_valid_env(self, env, valid_envs):
        if type(env) != Env:
            raise ConfigException(self.__class__.__name__ + ': env must be of type ' + repr(Env.__name__) + '; found type ' + repr(env.__class__.__name__))

        for valid_env in valid_envs:
            if env in valid_env:
                return
        raise ConfigException("The env " + repr(env) + " must be in the (nested) list of valid_envs " + repr(valid_envs))

    def _env_specific_value(self, attr_coll, env):
        if isinstance(attr_coll, ConfigItem) or isinstance(attr_coll, list):
            return attr_coll

        try:
            return attr_coll.env_values[env]
        except KeyError:
            self._check_valid_env(env, self._root_conf._valid_envs)
            raise InternalError()

    def getattr_env(self, name, env):
        try:
            attr_coll = self._attributes[name]
        except KeyError:
            error_message = ""
            repeatable_name = name + 's'
            if self._attributes.get(repeatable_name):
                error_message = ", but found attribute " + repr(repeatable_name)
            raise ConfigException(repr(self) + " has no attribute " + repr(name) + error_message)

        return self._env_specific_value(attr_coll, env)

    def __getattr__(self, name):
        if name[0] == '_':
            return super(_ConfigBase, self).__getattr__(name)

        if not self._root_conf:
            raise ConfigException(self._name + " object must be nested (indirectly) in a " + repr(ConfigRoot.__name__))

        if not self._finalized:
            try:
                # Return existing collector if any
                coll = self._attributes[name]
                if type(coll) == AttributeCollector:
                    return coll
                return AttributeCollector(name, self)
            except KeyError:
                return AttributeCollector(name, self)

        try:
            return self.getattr_env(name, self._root_conf._selected_env)
        except ConfigException as ex:
            if self._debug_exc:
                raise
            raise ConfigException(ex.message)

    def iteritems(self):
        for key, value in self._attributes.iteritems():
            yield key, self._env_specific_value(value, self._root_conf._selected_env)

    def items(self):
        return list(self.iteritems())


class ConfigRoot(_ConfigBase):
    def __init__(self, selected_env, valid_envs, **attr):
        if not isinstance(valid_envs, Sequence) or isinstance(valid_envs, str):
            raise ConfigException(self.__class__.__name__ + ": valid_envs arg must be a 'Sequence'; found type " + repr(valid_envs.__class__.__name__))

        for env in valid_envs:
            if not isinstance(env, Env):
                raise ConfigException(self.__class__.__name__ + ": valid_envs items must be instance of 'Env'; found a " + repr(env.__class__.__name__))

        self._check_valid_env(selected_env, valid_envs)

        self._selected_env = selected_env
        self._valid_envs = valid_envs
        super(ConfigRoot, self).__init__(**attr)
        self._root_conf = self

    def _insert(self, other):
        other_class = ConfigItem
        if not isinstance(other, other_class):
            raise ConfigException("Only a " + repr(other_class.__name__) + " may be inserted in a " + repr(self.__class__.__name__))

    def __lshift__(self, other):
        self._insert(other)
        return other

    def __ilshift__(self, other):
        self._insert(other)
        return self

    @property
    def selected_env(self):
        return self._selected_env


class ConfigItem(_ConfigBase):
    def __init__(self, repeat, **attr):
        assert isinstance(repeat, type(True))
        super(ConfigItem, self).__init__(**attr)
        self._repeat = repeat

        # Automatic Nested Insert in parent
        # Set back reference to containing Item and root item
        self._contained_in = self.__class__.nested[-1]
        self._root_conf = self._contained_in._root_conf

        # Insert self in containing Item's attributes
        if self._repeat:
            my_key = self._name + 's'

            # Validate that an attribute value of parent is not overridden by nested item (self)
            if my_key in self._contained_in._attributes:
                if not isinstance(self._contained_in._attributes[my_key], list):
                    msg = repr(my_key) + ' is defined both as simple value and a contained item: ' + repr(self)
                    raise ConfigException(msg)
                # TODO?: type check of list items (instanceof(ConfigItem). Same type?

            # To s or not to s?
            self._contained_in._attributes.setdefault(my_key, []).append(self)
            return

        my_key = self._name
        if my_key in self._contained_in._attributes:
            if isinstance(self._contained_in._attributes[my_key], ConfigItem):
                raise ConfigException("Repeated non repeatable conf item: " + repr(my_key))
            msg = repr(my_key) + ' is defined both as simple value and a contained item: ' + repr(self)
            raise ConfigException(msg)

        self._contained_in._attributes[my_key] = self

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from envs import EnvGroup, env_or_group, EnvException
from config_errors import ConfigException, NoAttributeException, _error_msg


class AttributeCollector(object):
    def __init__(self, attribute_name, container):
        self._attribute_name = attribute_name
        self._container = container
        self._env_values = {}
        self._frozen = False

    def __call__(self, **kwargs):
        self._frozen = True

        if self._attribute_name in self._container.attributes:
            _error_msg(0, "Redefined attribute " + repr(self._attribute_name))
            raise ConfigException("Attribute redefinition error: " + repr(self._attribute_name))

        self._container.attributes[self._attribute_name] = self

        # For error messages
        eg_from = {}
        errors = 0

        attr_types = set()

        defaults = self._container._defaults
        if self._attribute_name in defaults:
            if defaults[self._attribute_name] != None:
                attr_types.add(type(defaults[self._attribute_name]))

        # Validate and assign given env values to container
        for eg_name, value in kwargs.iteritems():
            try:
                eg = env_or_group(eg_name)

                # Validate that an attribute has the same type for all envs
                if type(value) != type(None):
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
        required_if_key = self._container.__class__._deco_required_if_attributes[0]
        if required_if_key:
            try:
                required_if_attributes = self._container.__class__._deco_required_if_attributes[1]
                required_if = self._container.attributes[required_if_key]
            except KeyError:
                required_if = False

        for eg in self._container.root_conf._valid_envs:
            for env in eg.envs():
                if env in self._env_values:
                    # The attribute is set with an env specific value
                    continue

                if self._attribute_name in defaults:
                    # The attribute is set with a default value, update env value
                    self._env_values[env] = defaults[self._attribute_name]
                    continue

                # Check for required_if, the required_if atributes are optional if required_if is false or not specified for the env
                if required_if_key:
                    if self._attribute_name == required_if_key:
                        # A required_if key is optional
                        continue

                    required_if_env_value = False
                    try:
                        required_if_env_value = required_if.env_value(env)
                    except NoAttributeException:
                        pass
                    if not required_if_env_value and self._attribute_name in required_if_attributes:
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

    def env_value(self, env):
        if not self._frozen:
            raise ConfigException("Attribute " + repr(self._attribute_name) + " is not frozen.")
        return self._container.getattr_env(self._attribute_name, env)

    def value(self):
        return self.env_value(self._container.root_conf.selected_env)

    @property
    def env_values(self):
        return self._env_values

    def override(self, other):
        assert other._frozen
        self._env_values.update(other._env_values)

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .envs import EnvGroup, EnvException
from .config_errors import ConfigException, NoAttributeException, _error_msg as error


class AttributeCollector(object):
    def __init__(self, attribute_name, container, has_default, default_value):
        self._attribute_name = attribute_name
        self._container = container
        # Insert self in container
        self._container.attributes[self._attribute_name] = self
        self._has_default = has_default
        self._default_value = default_value
        self._env_values = {}
        self._frozen = False

    def __call__(self, **kwargs):
        self._frozen = True

        # For error messages
        eg_from = {}
        num_errors = 0

        attr_types = set()
        if self._has_default and self._default_value != None:
            attr_types.add(type(self._default_value))
        
        if 'default' in kwargs:            
            if self._has_default:
                raise ConfigException("Attribute already has a default value: " + repr(self._attribute_name))
            self._has_default = True
            self._default_value = kwargs['default']
            del kwargs['default']

        # Validate and assign given env values to container
        for eg_name, value in kwargs.iteritems():
            try:
                eg = self._container.root_conf.env.factory.env_or_group(eg_name)

                # Validate that an attribute has the same type for all envs
                if type(value) != type(None):
                    if type(value) not in attr_types and attr_types:
                        msg = "Found different types of property " + repr(self._attribute_name) + " for different envs: " + repr(type(value)) + " previously found types: " + repr(list(attr_types))
                        num_errors = error(num_errors, msg)
                    attr_types.add(type(value))

                for env in eg.envs():
                    # If env == eg then this is a direct env specification, allow overwriting value previously specified through a group
                    if env not in self._env_values or (isinstance(eg_from[env], EnvGroup) and (env == eg)):
                        self._env_values[env] = value
                        eg_from[env] = eg
                        continue

                    # If env != eg then this is specified through a group, if it was previously specified directly, just ignore
                    if (not isinstance(eg_from[env], EnvGroup)) and (env != eg):
                        continue

                    new_eg_msg = repr(env) + ("" if env == eg else " from group " + repr(eg))
                    prev_eg_msg = repr(eg_from[env])
                    msg = "A value is already specified for: " + new_eg_msg + '=' + repr(value) + ", previous value: " + prev_eg_msg + '=' + repr(self._env_values[env])
                    num_errors = error(num_errors, msg)

            except EnvException as ex:
                num_errors = error(num_errors, ex.message)

        # Check whether we need to check for conditionally required attributes
        required_if_key = self._container.__class__._deco_required_if[0]
        if required_if_key:
            required_if_attributes = self._container.__class__._deco_required_if[1]
            try:
                required_if = self._container.attributes[required_if_key]
            except KeyError:
                # The condition property was not specified, so the conditional properties are not required
                required_if_key = False                

        # Validate that the attribute is defined for all envs / assign default value
        for eg in self._container.root_conf._valid_envs:
            for env in eg.envs():
                if env in self._env_values:
                    # The attribute is set with an env specific value
                    continue

                if self._has_default:
                    # The attribute is set with a default value, update env value
                    self._env_values[env] = self._default_value
                    continue

                # Check for required_if, the required_if atributes are optional if required_if is false or not specified for the env
                if required_if_key:
                    if self._attribute_name == required_if_key:
                        # A required_if condition attribute is optional, so it is ok that it is not set for all environment
                        continue

                    required_if_env_value = False
                    try:
                        required_if_env_value = required_if._env_value(env)
                    except NoAttributeException:
                        pass
                    if not required_if_env_value and self._attribute_name in required_if_attributes:
                        continue

                group_msg = ", which is a member of " + repr(eg) if isinstance(eg, EnvGroup) else ""
                msg = "Attribute: " + repr(self._attribute_name) + " did not receive a value for env " + repr(env)
                num_errors = error(num_errors, msg + group_msg)

        if num_errors:
            raise ConfigException("There were " + repr(num_errors) + " errors when defining attribute " + repr(self._attribute_name))

        return self

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__ and __call__
            super(AttributeCollector, self).__setattr__(name, value)
            return
        raise ConfigException("Trying to set a property " + repr(name) + " on an attribute collector")

    def __repr__(self):
        return self.__class__.__name__ + ': ' + repr(self._attribute_name) + ':' + ('frozen' if self._frozen else 'not-frozen') + ", values: " + repr(self._env_values)

    def _env_value(self, env):
        return self._container.getattr_env(self._attribute_name, env)

    def value(self):
        return self._env_value(self._container.env)

    @property
    def env_values(self):
        return self._env_values

    def override(self, other):
        assert other._frozen
        self._env_values.update(other._env_values)

    def freeze(self):
        self()

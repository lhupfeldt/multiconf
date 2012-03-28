# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from collections import Sequence
from attrdict import AttrDict
from _checked_insert_dict import CheckedInsertDict, CheckedInsertDictGroup
from envs import Env, EnvGroup

class ConfigException(Exception):
    pass

class _ConfigException(Exception):
    pass


class _ConfigBase(object):
    nested = []

    def __init__(self, **attr):
        self._debug_exc = False

        # Object linking
        self._root_conf = None
        self._nesting_level = 0

        # Attribute holders
        self._checked_insert_group = CheckedInsertDictGroup(fail_fast=self._debug_exc)
        self._contains = AttrDict()
        self._default_attrs = AttrDict(attr)

        self._name = self.__class__.__name__

    def _iter_attr_names(self):
        """return all keys in all confs"""
        seen = set()
        def uniq(seq):
            for item in seq:
                if item not in seen:
                    yield item
                seen.add(item)

        for key in uniq(self._default_attrs):
            yield key

        for conf in self._checked_insert_group.env_confs.itervalues():
            for key in uniq(conf):
                yield key

    def irepr(self, indent_level):
        """Indented repr"""
        indent1 = '  ' * indent_level
        indent2 =  indent1 + '     '
        return self._name + ' {\n' + \
            ''.join([indent2 + name + ': ' + repr(value) + '\n' for name, value in self.iteritems()]) + \
            indent1 + '}'

    def __repr__(self):
        return self.irepr(self._nesting_level)

    def __enter__(self):
        self._nesting_level = len(self.__class__.nested)
        self.__class__.nested.append(self)

        for env in self._root_conf._valid_envs.all():
            self.__dict__[env.name] = CheckedInsertDict(self._checked_insert_group, env)

        return self

    def validate_property_defined_for_all_envs(self):
        # Validate that the same attributes are defined for all confs
        try:
            for key in self._iter_attr_names():
                for env in self._root_conf._valid_envs.envs():
                    value = self.get_for_conf(env, key)
        except _ConfigException:
            if self._debug_exc:
                raise
            msg = "Attribute: " + repr(key) + " did not receive a value for " + repr(env)
            raise ConfigException(msg)

    def validate_property_same_type_for_all_envs(self):
        for key in self._iter_attr_names():
            previous_type = None
            for env in self._root_conf._valid_envs.envs():
                value = self.get_for_conf(env, key)
                # TODO: This check should be done at assignment
                if previous_type and type(value) != previous_type:
                    raise ConfigException("Found different types of property " + repr(key) + " for different envs: " + repr(type(value)) + " previous type: " + repr(previous_type))
                previous_type = type(value)

    def exit_validation(self):
        self.validate_property_defined_for_all_envs()
        self.validate_property_same_type_for_all_envs()

    def __exit__(self, exc_type, exc_value, traceback):
        self.__class__.nested.pop()

        if exc_type:
            return None

        if self._checked_insert_group.errors:
            num_errors = self._checked_insert_group.errors
            self._checked_insert_group.errors = 0
            raise ConfigException("There were " + repr(num_errors) + " errors found when assigning specific properties")

        try:
            self.exit_validation()
        except ConfigException as ex:
            if self._debug_exc:
                raise
            # Strip stack
            raise ex

    def __setattr__(self, name, value):
        if name[0] == '_':
            # Needed to set private values in __init__
            super(_ConfigBase, self).__setattr__(name, value)
            return

        raise ConfigException("Trying to set a property " + repr(name) + " on a config item")

        # Make sure a conf was not overwritten by a property
        # Also make sure we don't try to do validation in init
        #root_conf = self.__dict__.get('_root_conf')
        #if root_conf:
        #    for env in root_conf._valid_envs:
        #        if name == env.name:
        #            raise ConfigException("Trying to set property " + name + " which would overwrite conf " + repr(env))


    def get_for_conf(self, env, name):
        try:
            conf = self._checked_insert_group.env_confs[env]
            #print 'conf:', conf
            conf_val = conf[name]
            #print 'conf_val:', conf_val
            return conf_val
        except KeyError:
            pass

        try:
            default_val = self._default_attrs[name]
            #print 'default_val:', default_val
            return default_val
        except KeyError:
            pass

        error_message = ""
        try:
            contained_val = self._contains[name]
            #print 'contained_val:', contained_val
            return contained_val
        except KeyError:
            repeatable_name = name + 's'
            if self._contains.get(repeatable_name):
                error_message = ", but found attribute " + repr(repeatable_name)
            pass

        raise _ConfigException(name + error_message)

    def __getattr__(self, name):
        if name[0] == '_':
            return super(_ConfigBase, self).__getattr__(name)

        if not self._root_conf:
            raise ConfigException(self._name + " object must be nested (indirectly) in a " + repr(ConfigRoot.__class__.__name__))

        try:
            return self.get_for_conf(self._root_conf._selected_env, name)
        except _ConfigException as ex:
            if self._debug_exc:
                raise
            raise ConfigException(ex.message)

    def iteritems(self):
        return ((key, self.__getattr__(key)) for key in self._iter_attr_names())

    def items(self):
        return list(self.iteritems())


class ConfigRoot(_ConfigBase):
    def __init__(self, selected_env, valid_envs, **attr):
        if type(selected_env) != Env:
            raise ConfigException(self.__class__.__name__ + ': selected_env arg must be of type ' + repr(Env.__class__.__name__) + '; found type ' + repr(selected_env.__class__.__name__))

        if not isinstance(valid_envs, Sequence) or isinstance(valid_envs, str):
            raise ConfigException(self.__class__.__name__ + ": valid_envs arg must be a 'Sequence'; found type " + repr(valid_envs.__class__.__name__))

        for env in valid_envs:
            if not isinstance(env, Env):
                raise ConfigException(self.__class__.__name__ + ": valid_envs items must be instance of 'Env'; found a " + repr(env.__class__.__name__))

        self._valid_envs = EnvGroup('all_', *valid_envs)

        if selected_env not in self._valid_envs:
            raise ConfigException("The selected_env " + repr(selected_env) + " must be in the list of (nested) valid_envs " + repr(valid_envs))

        self._selected_env = selected_env
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

        my_key = self._name + 's' if self._repeat else self._name

        # Validate that a default/env-specif value of parent is not overridden by nested item (self)
        for key in self._contained_in._iter_attr_names():
            if key == my_key:
                msg = repr(key) + ' is defined both as simple value and a contained item ' + repr(self)
                raise ConfigException(msg)

        # Insert self in containing Item's dict of contained Items
        if self._repeat:
            # To s or not to s?
            self._contained_in._contains.setdefault(my_key, []).append(self)
            return

        if my_key in self._contained_in._contains:
            raise ConfigException("Repeated non repeatable conf item: " + repr(my_key))
        self._contained_in._contains[my_key] = self

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from collections import Sequence, OrderedDict
from envs import Env
from attribute_collector import AttributeCollector
from config_errors import ConfigException, NoAttributeException


class _ConfigBase(object):
    nested = []

    # Decoration attributes
    _deco_named_as = None
    _deco_repeatable = False
    _deco_nested_repeatables = []
    _deco_required_attributes = []
    _deco_required_if_attributes = (None, ())

    def __init__(self, **attr):
        self._debug_exc = True

        # Object linking
        self._root_conf = None

        # Dict of dicts: attributes['a'] = dict(Env('prod')=1, EnvGroup('dev')=0)
        self._attributes = OrderedDict()
        for key in self.__class__._deco_nested_repeatables:
            self._attributes[key] = OrderedDict()

        self._defaults = attr
        self._frozen = True

    def named_as(self):
        if self.__class__._deco_named_as:
            return self.__class__._deco_named_as
        if self.__class__._deco_repeatable:
            return self.__class__.__name__ + 's'
        return self.__class__.__name__

    def irepr(self, indent_level):
        """Indented repr"""
        indent1 = '  ' * indent_level
        indent2 =  indent1 + '     '
        # + ':' + self.__class__.__name__
        not_frozen_msg = "" if self._frozen else " not-frozen, defaults: " + repr(self._defaults) + '\n'
        return self.named_as() + not_frozen_msg + ' {\n' + \
            ''.join([indent2 + name + ': ' + repr(value) + ',\n' for name, value in self.iteritems()]) + \
            indent1 + '}'

    def __repr__(self):
        return self.irepr(len(self.__class__.nested) -1)

    def __enter__(self):
        self._frozen = False
        return self

    def freeze_validate_required(self):
        missing = []
        for req in self.__class__._deco_required_attributes:
            if not req in self._attributes:
                missing.append(req)
        if missing:
            raise ConfigException("No value given for required attributes: " + repr(missing))

    def freeze_validate_required_if(self):
        required_if_key = self.__class__._deco_required_if_attributes[0]
        if not required_if_key:
            return

        try:
            required_if = self._attributes[required_if_key].value()
            if not required_if:
                return
        except KeyError:
            return
        except NoAttributeException:
            return

        missing = []
        for req in self.__class__._deco_required_if_attributes[1]:
            if not req in self._attributes:
                missing.append(req)
        if missing:
            raise ConfigException("Missing required_if attributes. Condition attribute: " + repr(required_if_key) + "==" +  repr(required_if) + ", missing: " + repr(missing))

    def freeze_validation(self):
        """Override this method if you need special checks"""
        self.freeze_validate_required()
        self.freeze_validate_required_if()

    def freeze(self):
        # Collect remaining default values
        for name in list(self._defaults):
            AttributeCollector(name, self)()

        try:
            self.freeze_validation()
        except ConfigException as ex:
            if self._debug_exc:
                raise
            # Strip stack
            raise ex
        except NoAttributeException as ex:
            if self._debug_exc:
                raise
            raise ex

        self._frozen = True

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            return None

        try:
            self.freeze()
        except ConfigException as ex:
            if self._debug_exc:
                raise
            raise ex
        except NoAttributeException as ex:
            if self._debug_exc:
                raise
            raise ex

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

    def _env_specific_value(self, attr_name, attr_coll, env):
        if isinstance(attr_coll, ConfigItem) or isinstance(attr_coll, OrderedDict):
            return attr_coll

        try:
            return attr_coll.env_values[env]
        except KeyError:
            self._check_valid_env(env, self._root_conf._valid_envs)
            raise NoAttributeException("Attribute " + repr(attr_name) + " undefined for env " + repr(env))

    def getattr_env(self, name, env):
        try:
            attr_coll = self._attributes[name]
        except KeyError:
            error_message = ""
            repeatable_name = name + 's'
            if self._attributes.get(repeatable_name):
                error_message = ", but found attribute " + repr(repeatable_name)
            raise ConfigException(repr(self) + " has no attribute " + repr(name) + error_message)

        return self._env_specific_value(name, attr_coll, env)

    def __getattr__(self, name):
        if not self._frozen:
            try:
                # Return existing collector/dict of nested items if any
                coll = self._attributes[name]
                if type(coll) in (AttributeCollector, OrderedDict):
                    return coll
                if isinstance(coll, _ConfigItem):
                    return AttributeCollector(name, self)
                raise Exception("Internal error, unexpected type: " + repr(type(coll)) + ':' + repr(coll))
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
            try:
                yield key, self._env_specific_value(key, value, self._root_conf._selected_env)
            except NoAttributeException:
                # This should only happen in case of  a conditional attribute
                pass

    def items(self):
        return list(self.iteritems())

    @property
    def contained_in(self):
        return self._contained_in

    @property
    def root_conf(self):
        return self._root_conf


class _ConfigItem(_ConfigBase):
    def _validate(self):
        self.validate()
        for _child_name, child_value in self.iteritems():
            if isinstance(child_value, OrderedDict):
                for dict_entry in child_value.values():
                    dict_entry._validate()

            if isinstance(child_value, _ConfigItem):
                child_value._validate()

    def validate(self):
        """Can be overridden to provide post-frozen validation"""
        pass

    def __enter__(self):
        super(_ConfigItem, self).__enter__()
        self.__class__.nested.append(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__class__.nested.pop()
        super(_ConfigItem, self).__exit__(exc_type, exc_value, traceback)


class ConfigRoot(_ConfigItem):
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
        self._contained_in = None

    def __exit__(self, exc_type, exc_value, traceback):
        super(ConfigRoot, self).__exit__(exc_type, exc_value, traceback)
        self._validate()

    @property
    def selected_env(self):
        return self._selected_env


class ConfigItem(_ConfigItem):
    def __init__(self, **attr):
        super(ConfigItem, self).__init__(**attr)

        # Automatic Nested Insert in parent
        if not self.__class__.nested:
            raise ConfigException(self.__class__.__name__ + " object must be nested (indirectly) in a " + repr(ConfigRoot.__name__))

        # Set back reference to containing Item and root item
        self._contained_in = self.__class__.nested[-1]
        self._root_conf = self._contained_in._root_conf

        # Insert self in containing Item's attributes
        my_key = self.named_as()

        if self.__class__._deco_repeatable:
            # Validate that the containing item has specified this item as repeatable
            if not my_key in self._contained_in.__class__._deco_nested_repeatables:
                msg = repr(my_key) + ': ' + repr(self) + ' is defined as repeatable, but this is not defined as a repeatable item in the containing class: ' + \
                    repr(self._contained_in.named_as())
                raise ConfigException(msg)
                # TODO?: type check of list items (instanceof(ConfigItem). Same type?

            if my_key in self._contained_in._attributes:
                # Validate that an attribute value of parent is not overridden by nested item (self),
                if not isinstance(self._contained_in._attributes[my_key], OrderedDict):
                    msg = repr(my_key) + ' is defined both as simple value and a contained item: ' + repr(self)
                    raise ConfigException(msg)
                # TODO?: type check of list items (instanceof(ConfigItem). Same type?

            # Insert in Ordered dict by 'id' or 'name', 'id' is preferred if given
            try:
                try:
                    obj_key = self._defaults['id']
                except KeyError:
                    obj_key = self._defaults['name']

                # Check that we are no replacing an object with the same id/name
                if self._contained_in._attributes[my_key].get(obj_key):
                    raise ConfigException("Re-used id/name " + repr(obj_key) + " in nested objects")
            except KeyError:
                obj_key = id(self)

            self._contained_in._attributes[my_key][obj_key] = self
            return

        if my_key in self._contained_in._attributes:
            if isinstance(self._contained_in._attributes[my_key], ConfigItem):
                raise ConfigException("Repeated non repeatable conf item: " + repr(my_key))
            if isinstance(self._contained_in._attributes[my_key], OrderedDict):
                msg = repr(my_key) + ': ' + repr(self) + ' is defined as non-repeatable, but the containing object has repatable items with the same name: ' + \
                    repr(self._contained_in)
                raise ConfigException(msg)
            raise ConfigException(repr(my_key) + ' is defined both as simple value and a contained item: ' + repr(self))

        self._contained_in._attributes[my_key] = self


class ConfigBuilder(_ConfigBase):
    def __init__(self, **attr):
        super(ConfigBuilder, self).__init__(**attr)

        # Set back reference to containing Item and root item
        self._contained_in = self.__class__.nested[-1]
        self._root_conf = self._contained_in._root_conf

    def __exit__(self, exc_type, exc_value, traceback):
        super(ConfigBuilder, self).__exit__(exc_type, exc_value, traceback)
        self.build()

    def build(self):
        """Override this in derived classes. This is where child ConfigItems are declared"""
        raise ConfigException("'build' must be overridded")

    def override(self, config_item):
        """Assign attributes from builder to child Item"""
        for key, value in self._attributes.iteritems():
            config_item_attr = config_item._attributes.get(key)
            if config_item_attr:
                config_item_attr.override(value)
                continue
            config_item._attributes[key] = value



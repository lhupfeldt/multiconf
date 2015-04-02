# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import Container, OrderedDict
import json

from .bits import int_to_bin_str


class EnvException(Exception):
    pass


class BaseEnv(object):
    def __init__(self, name, factory, mask):
        """ Private, use EnvFactory.Env() """
        self._name = name
        self.members = []
        self.factory = factory
        self.index = self.factory._index
        self.bit = 1 << self.index
        self.mask = mask | self.bit
        self.factory._all_egs_mask |= mask
        self.factory._index += 1

    @classmethod
    def validate(cls, name):
        if not isinstance(name, type("")):
            raise EnvException(cls.__name__ + ": 'name' must be instance of " + type("").__name__ + ", found: " + type(name).__name__)
        if not len(name):
            raise EnvException(cls.__name__ + ": 'name' must not be empty")
        if name[0] == '_':
            raise EnvException(cls.__name__ + ": 'name' must not start with '_', got: " + repr(name))
        if name == 'default':
            raise EnvException(cls.__name__ + ": name '" + name + "' is reserved")

    @property
    def name(self):
        return self._name

    def json(self, skipkeys=True):
        class Encoder(json.JSONEncoder):
            def default(self, env):  # pylint: disable=method-hidden
                return env.json_equivalent()

        # python3 doesn't need  separators=(',', ': ')
        return json.dumps(self, skipkeys=skipkeys, cls=Encoder, check_circular=True, sort_keys=False, indent=4, separators=(',', ': '))

    def json_equivalent(self):
        return OrderedDict((
            ("type", repr(self.__class__)),
            ("name", self.name),
            ("bit", self.bit),
            ("mask", int_to_bin_str(self.mask)),
            # ("hash", self.__hash__()),
            ("members", self.members))
        )

    def irepr(self, _indent_level):
        return self.__class__.__name__ + '(' + repr(self.name) + ')'

    def __repr__(self):
        return self.irepr(0)

    def __lt__(self, other):
        return self.bit < other.bit

    def __hash__(self):
        return self.bit

    def __contains__(self, other):
        return self.mask & other.mask == other.mask and self.mask != other.mask


class Env(BaseEnv):
    def __init__(self, name, factory):
        self.env_bits = [factory._index]
        self.eg_bits = self.env_bits
        super(Env, self).__init__(name=name, factory=factory, mask=0)
        self.factory._all_envs_mask |= self.bit
        self.envs = [self]
        self.all = [self]


class EnvGroup(BaseEnv, Container):
    def __init__(self, name, factory, members):
        """ Private, use EnvFactory.Group() method """
        # Check for empty group
        if not members:
            raise EnvException(self.__class__.__name__ + ': No group members specified')

        # Collect mask of all children. Check arg types
        mask = 0b0
        for eg in members:
            if not isinstance(eg, BaseEnv):
                raise EnvException(self.__class__.__name__ + ': Group members args must be instance of ' +
                                   repr(Env.__name__) + ' or ' + repr(EnvGroup.__name__) + ', found: ' + repr(eg))
            if eg.factory is not factory:
                raise EnvException(self.__class__.__name__ + ": The group members must be from the same 'env_factory' as the group being declared. " +
                                   repr(Env.__name__) + ' or ' + repr(EnvGroup.__name__) + ' found: ' + repr(eg))
            mask |= eg.mask

        super(EnvGroup, self).__init__(name=name, factory=factory, mask=mask)

        # Check for doublets
        seen_envs = set()
        for eg in members:
            if eg in seen_envs:
                raise EnvException("Repeated group member: " + repr(eg) + " in " + repr(self))
            seen_envs.add(eg)

        # All good
        self.members = members
        self.env_bits = list(self._env_bits())
        self.eg_bits = list(self._eg_bits())

        self.groups = [self]
        for member_group in self._groups_recursive():
            self.groups.append(member_group)

        envs = OrderedDict()
        for member in self.members:
            if not isinstance(member, EnvGroup):
                envs[member.name] = member
                continue
            for member in member.envs:
                envs[member.name] = member
        self.envs = list(envs.values())

        self.all = self.groups + self.envs

    def irepr(self, indent_level):
        indent1 = '  ' * indent_level
        indent2 = indent1 + '     '
        return self.__class__.__name__ + '(' + repr(self.name) + ') {\n' + \
            ',\n'.join([indent2 + member.irepr(indent_level + 1) for member in self.members]) + '\n' + \
            indent1 + '}'

    def __repr__(self):
        return self.irepr(0)

    def _eg_bits(self):
        bit = 0
        while bit < self.factory._index:
            if 1 << bit & self.mask:
                yield bit
            bit += 1

    def _env_bits(self):
        bit = 0
        while bit < self.factory._index:
            if 1 << bit & self.mask & self.factory._all_envs_mask:
                yield bit
            bit += 1

    def _groups_recursive(self):
        for member in self.members:
            if isinstance(member, EnvGroup):
                for member in member.groups:
                    yield member


class EnvFactory(object):
    def __init__(self):
        self.envs = OrderedDict()
        self.groups = OrderedDict()
        self._index = 1  # bit zero reserved to be set for all groups, so that a Group mask will never be equal to an env mask
        self._all_egs_mask = 0
        self._all_envs_mask = 0
        self._mc_default_group = None
        self._mc_frozen = False

    def Env(self, name):
        """ Declare a new Env """
        if self._mc_frozen:
            raise EnvException(self.__class__.__name__ + " is already in use. No more envs may be added.")
        if name in self.groups:
            raise EnvException("Name " + repr(name) + " is already used by group: " + repr(self.groups[name]))
        if name in self.envs:
            raise EnvException("Name " + repr(name) + " is already used by env: " + repr(self.envs[name]))
        Env.validate(name)
        new_env = Env(name, factory=self)
        self.envs[name] = new_env
        return new_env

    def _EnvGroup(self, name, members):
        new_group = EnvGroup(name=name, factory=self, members=members)
        self.groups[name] = new_group
        return new_group

    def EnvGroup(self, name, *members):
        """ Declare a new EnvGroup """
        if self._mc_frozen:
            raise EnvException(self.__class__.__name__ + " is already in use. No more groups may be added.")
        if name in self.groups:
            raise EnvException("Name " + repr(name) + " is already used by group: " + repr(self.groups[name]))
        if name in self.envs:
            raise EnvException("Name " + repr(name) + " is already used by env: " + repr(self.envs[name]))
        EnvGroup.validate(name)
        return self._EnvGroup(name=name, members=members)

    def _mc_create_default_group(self):
        """
        Must be called after all user defined envs and groups are defined.
        creates 'default' group which is the superset of all user defined groups and envs
        after this is called, no more envs or groups may be created by this factory.
        """
        if not self._mc_frozen:
            self._mc_default_group = self._EnvGroup('default', members=list(self.groups.values()) + list(self.envs.values()))
            self._mc_frozen = True

    def env(self, name):
        """Get an already declared env from it's name"""
        _env = self.envs.get(name)
        if _env:
            return _env

        raise EnvException("No such " + Env.__name__ + ": " + repr(name))

    def env_or_group_from_name(self, name):
        """Get an already declared env or group from it's name"""
        _env = self.envs.get(name)
        if _env:
            return _env

        _env_group = self.groups.get(name)
        if _env_group:
            return _env_group

        raise EnvException("No such " + Env.__name__ + " or " + EnvGroup.__name__ + ": " + repr(name))

    def env_or_group_from_bit(self, bit):
        """Get an already declared env or group from it's bit mask"""

        for env in self.envs.values():
            if env.bit & bit:
                return env

        for group in self.groups.values():
            if group.bit & bit:
                return group

        raise EnvException("No " + Env.__name__ + " or " + EnvGroup.__name__ + " with bit " + int_to_bin_str(bit, self._index + 1))

    def envs_from_mask(self, mask):
        """Yield envs matching mask"""

        for env in self.envs.values():
            if env.bit & mask:
                yield env

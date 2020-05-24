# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections.abc import Container
import itertools
import json

from .bits import int_to_bin_str


class EnvException(Exception):
    pass


class AmbiguousEnvException(EnvException):
    def __init__(self, msg, ambiguous):
        super().__init__(msg)
        self.ambiguous = ambiguous


class BaseEnv():
    def __init__(self, name, factory, mask):
        """ Private, use EnvFactory.Env() """
        self.name = name
        self.members = []
        self.factory = factory

        self.bit = 1 << self.factory._index
        self.mask = mask | self.bit
        self.factory._index += 1

    @classmethod
    def validate(cls, name):
        if not isinstance(name, type("")):
            raise EnvException(cls.__name__ + ": 'name' must be instance of " + type("").__name__ + ", found: " + type(name).__name__)
        if not len(name):
            raise EnvException(cls.__name__ + ": 'name' must not be empty")
        if name[0] == '_':
            raise EnvException(cls.__name__ + ": 'name' must not start with '_', got: " + repr(name))
        if name in ('default', 'MC_NO_ENV'):
            raise EnvException(cls.__name__ + ": name '" + name + "' is reserved")

    def json(self, skipkeys=True):
        class Encoder(json.JSONEncoder):
            def default(self, env):  # pylint: disable=method-hidden
                return env.json_equivalent()

        # python3 doesn't need  separators=(',', ': ')
        return json.dumps(self, skipkeys=skipkeys, cls=Encoder, check_circular=True, sort_keys=False, indent=4, separators=(',', ': '))

    def json_equivalent(self):
        return dict(
            type=repr(self.__class__),
            name=self.name,
            bit=self.bit,
            mask=int_to_bin_str(self.mask),
            # hash=self.__hash__(),
            members=self.members,
        )

    def irepr(self, _indent_level):
        return self.__class__.__name__ + '(' + repr(self.name) + ')'

    def __repr__(self):
        return self.irepr(0)

    def __hash__(self):
        return self.bit

    def __contains__(self, other):
        return self.mask & other.mask == other.mask and self.mask != other.mask


class Env(BaseEnv):
    def __init__(self, name, factory, allow_todo):
        super().__init__(name=name, factory=factory, mask=0)
        self.envs = [self]
        self.lookup_order = None
        self.allow_todo = allow_todo


class EnvGroup(BaseEnv, Container):
    def __init__(self, name, factory, members):
        """ Private, use EnvFactory.Group() method """
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

        super().__init__(name=name, factory=factory, mask=mask)

        # Check for doublets
        seen_envs = set()
        for eg in members:
            if eg in seen_envs:
                raise EnvException("Repeated group member: " + repr(eg) + " in " + repr(self))
            seen_envs.add(eg)

        # All good
        self.members = members

        self.groups = [self]
        for member_group in self._groups_recursive():
            self.groups.append(member_group)

        envs = {}
        for member in self.members:
            if not isinstance(member, EnvGroup):
                envs[member.name] = member
                continue
            for member in member.envs:
                envs[member.name] = member
        self.envs = list(envs.values())

        self.ambiguous = {env.name: [] for env in self.envs}

    def irepr(self, indent_level):
        indent1 = '   ' * indent_level
        indent2 = indent1 + '   '
        return self.__class__.__name__ + '(' + repr(self.name) + ') {\n' + \
            ',\n'.join([indent2 + member.irepr(indent_level + 1) for member in self.members]) + '\n' + \
            indent1 + '}'

    def __repr__(self):
        return self.irepr(0)

    def _groups_recursive(self):
        for member in self.members:
            if isinstance(member, EnvGroup):
                yield from member.groups


class EnvFactory():
    def __init__(self):
        self.envs = {}
        self.groups = {}
        self._index = 1  # bit zero reserved to be set for all groups, so that a Group mask will never be equal to an env mask
        self._mc_frozen = False

    def Env(self, name, allow_todo=False):
        """ Declare a new Env """
        if self._mc_frozen:
            raise EnvException(self.__class__.__name__ + " is already in use. No more envs may be added.")
        if name in self.groups:
            raise EnvException("Name " + repr(name) + " is already used by group: " + repr(self.groups[name]))
        if name in self.envs:
            raise EnvException("Name " + repr(name) + " is already used by env: " + repr(self.envs[name]))
        Env.validate(name)
        new_env = Env(name, factory=self, allow_todo=allow_todo)
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
        # Check for empty group
        if not members:
            raise EnvException(EnvGroup.__name__ + ': No group members specified')
        return self._EnvGroup(name=name, members=members)

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

    def validate_env_group_names(self, eg_names):
        """Check that all names in eg_names are defined Envs or Groups"""
        undefined = []

        for eg_name in eg_names:
            if eg_name in self.envs:
                continue
            if eg_name in self.groups:
                continue
            undefined.append(eg_name)

        if undefined:
            if len(undefined) > 1:
                raise EnvException("No such " + Env.__name__ + "s or " + EnvGroup.__name__ + "s: " + repr(undefined))
            raise EnvException("No such " + Env.__name__ + " or " + EnvGroup.__name__ + ": " + repr(undefined[0]))

    def _mc_calc_env_group_order(self):
        """
        Must be called after all user defined envs and groups are defined.

        Creates 'default' group which is the superset of all user defined groups and envs.
        Calculates the group lookup order and ambiguity lists for all envs.
        After this is called, no more envs or groups may be created by this factory.
        """

        if self._mc_frozen:
            return
        self._mc_frozen = True

        self.default = self._EnvGroup('default', members=list(self.groups.values()) + list(self.envs.values()))

        for env_name, env in self.envs.items():
            # print("env, name, typ:", env_name, env)
            env_groups = []
            for group_name, group in self.groups.items():
                # print("group name:", group_name)
                if env in group:
                    env_groups.append(group)

            max_index = len(env_groups) - 1
            for index, gg in enumerate(env_groups):
                if index == max_index:
                    break

                for amb_group in env_groups[index + 1:]:
                    if gg in amb_group:
                        continue
                    assert amb_group not in gg
                    gg.ambiguous[env.name].append(amb_group)

            env.lookup_order = env_groups

            # Debug
            # print()
            # print("env lookup_order:", )
            # print("    ", env.name)
            # for group in env.lookup_order:
            #     print("    ", group.name, '- amb ->', [gg.name for gg in group.ambiguous[env.name]])

        self.eg_none = self._EnvGroup('_mc_eg_none', members=[])

    def _mc_resolve_env_group_value(self, env, env_values):
        try:
            return env_values[env.name], env
        except KeyError:
            found_ambiguous = []
            for gg in env.lookup_order:
                if gg.name in env_values:
                    for amb_group in gg.ambiguous[env.name]:
                        if amb_group.name in env_values:
                            found_ambiguous.append(amb_group)
                    if found_ambiguous:
                        raise AmbiguousEnvException("Ambiguous values for: " + str(env), [gg] + found_ambiguous)
                    return env_values[gg.name], gg
        return None, None

    def _mc_select_env_list(self, env, eg_list1, eg_list2):
        """Resolve in which lists env is most specific, if in any.

        Returns (int or None): 1, 2 or None:
            1 if list1 has the most specific group or direct env.
            2 if list2
            None if env or group is in neither of the lists.

        Raises: AmbiguousEnvException if neither list is more specific.
        """

        eg1 = None
        for eg in itertools.chain([env], env.lookup_order):
            if eg in eg_list1:
                eg1 = eg
                break

        eg2 = None
        for eg in itertools.chain([env], env.lookup_order):
            if eg in eg_list2:
                eg2 = eg
                break

        if eg1:
            if not eg2 or eg1 in eg2:
                return 1

            if eg2 in eg1:
                return 2

            raise AmbiguousEnvException("Ambiguous env select for '{}'.".format(env), [eg1, eg2])

        if eg2:
            return 2

        return None


MC_NO_ENV = Env("MC_NO_ENV", type('', (object,), {'_index': 0}), allow_todo=True)
MC_NO_ENV.mask = 0
MC_NO_ENV.lookup_order = ()

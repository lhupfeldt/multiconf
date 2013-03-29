# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import Container


class EnvException(Exception):
    pass


class BaseEnv(object):
    def __init__(self, name, factory):
        """ Private, use EnvFactory.Env() """
        if not isinstance(name, type("")):
            raise EnvException(self.__class__.__name__ + ": 'name' must be instance of " + type("").__name__ + ", found: " +  type(name).__name__)
        if not len(name):
            raise EnvException(self.__class__.__name__ + ": 'name' must not be empty")
        if name[0] == '_':
            raise EnvException(self.__class__.__name__ + ": 'name' must not start with '_', got: " + repr(name))
        if name == 'default':
            raise EnvException(self.__class__.__name__ + ": 'default' is a reserved name")

        self._name = name
        self.members = []
        self.factory = factory

    @property
    def name(self):
        return self._name

    def irepr(self, _indent_level):
        return self.__class__.__name__ + '(' + repr(self.name) + ')'

    def __repr__(self):
        return self.irepr(0)

    def envs(self):
        """ return self"""
        yield self

    all = envs

    def __eq__(self, other):
        return self._name == other.name

    def __hash__(self):
        return hash(self._name)

    def __contains__(self, other):
        if other == self:
            return True


class Env(BaseEnv):
    def __init__(self, name, factory):
        super(Env, self).__init__(name, factory)
        self.factory._envs[name] = self


class EnvGroup(BaseEnv, Container):
    def __init__(self, name, factory, *members):
        """ Private, use EnvFactory.Group() method """
        super(EnvGroup, self).__init__(name, factory)
        self.factory._groups[name] = self

        # Check for empty group
        if not members:
            raise EnvException(self.__class__.__name__ + ': No group members specified')

        # Check arg types
        for cfg in members:
            if not isinstance(cfg, BaseEnv):
                raise EnvException(self.__class__.__name__ +  ': ' + ' Group members args must be instance of ' + 
                                   repr(Env.__name__) + ' or ' + repr(EnvGroup.__name__) + ', found: ' + repr(cfg))

        # Check for doublets
        seen_envs = set()
        def check_doublets(envs):
            for cfg in envs:
                if cfg in seen_envs:
                    raise EnvException("Repeated group member: " + repr(cfg) + " in " + repr(self))
                seen_envs.add(cfg)

                # Check children
                check_doublets(cfg.members)

        check_doublets(members)

        if self in seen_envs:
            raise EnvException("Can't have a member with my own name: " + repr(name) + ", members:  " + repr(list(members)))

        # All good
        self.members = members

    def irepr(self, indent_level):
        indent1 = '  ' * indent_level
        indent2 =  indent1 + '     '
        return self.__class__.__name__ + '(' + repr(self.name) + ') {\n' + \
            ',\n'.join([indent2 + member.irepr(indent_level + 1) for member in self.members]) + '\n' + \
            indent1 + '}'

    def __repr__(self):
        return self.irepr(0)

    def _groups(self):
        # Note: recursive whereas the 'groups' function is not
        for member in self.members:
            if isinstance(member, EnvGroup):
                yield member
                for member in member._groups():
                    yield member

    def groups(self):
        """ return all groups from all env groups"""
        yield self
        for member_group in self._groups():
            yield member_group

    def envs(self):
        """ return all envs from all env groups"""
        for member in self.members:
            if not isinstance(member, EnvGroup):
                yield member
                continue
            for member in member.envs():
                yield member

    def all(self):
        """ return all envs and groups from all env groups"""
        for group in self.groups():
            yield group
        for env in self.envs():
            yield env

    def __contains__(self, other):
        if other == self:
            return True
        for member in self.members:
            if other == member:
                return True
            if isinstance(member, EnvGroup):
                if other in member:
                    return True

        return False


class EnvFactory(object):
    def __init__(self):
        self._envs = {}
        self._groups = {}
    
    def Env(self, name):
        """ Declare a new Env """
        return Env(name, self)

    def EnvGroup(self, name, *members):
        """ Declare a new EnvGroup """
        return EnvGroup(name, self, *members)
    
    def env(self, name):
        """Get an already declared env from it's name"""
        _env = self._envs.get(name)
        if _env:
            return _env
    
        raise EnvException("No such " + Env.__name__ + ": " + repr(name))
    
    def group(self, name):
        """Get an already declared group from it's name"""
        _env_group = self._groups.get(name)
        if _env_group:
            return _env_group
    
        raise EnvException("No such " + EnvGroup.__name__ + ": " + repr(name))
        
    def env_or_group(self, name):
        """Get an already declared env or group from it's name"""
        _env = self._envs.get(name)
        if _env:
            return _env
    
        _env_group = self._groups.get(name)
        if _env_group:
            return _env_group
    
        raise EnvException("No such " + Env.__name__ + " or " + EnvGroup.__name__ + ": " + repr(name))

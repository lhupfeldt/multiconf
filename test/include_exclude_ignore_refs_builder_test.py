# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..decorators import named_as, repeat, nested_repeatables

from ..envs import EnvFactory


ef = EnvFactory()
dev1 = ef.Env('dev1')
prod = ef.Env('prod')


class root(ConfigRoot):
    def __init__(self, env, env_factory, name=None):
        super(root, self).__init__(env, env_factory)
        self.name = name


@nested_repeatables('reps')
class HasRepeatables(ConfigItem):
    def __init__(self, name, mc_exclude):
        super(HasRepeatables, self).__init__(mc_exclude=mc_exclude)
        self.name = name


@repeat()
@named_as('reps')
class RepeatableItem(ConfigItem):
    def __init__(self, name, mc_exclude=None):
        super(RepeatableItem, self).__init__(mc_key=name, mc_exclude=mc_exclude)
        self.name = name


class BB(ConfigBuilder):
    def __init__(self, aa):
        super(BB, self).__init__()
        self.aa = aa

    def build(self):
        RepeatableItem(name=self.aa)


def test_exclude_with_builder():
    def conf(env):
        with root(env, ef, name='x') as cr:
            with HasRepeatables(name='r1', mc_exclude=[prod]) as it:
                with BB('bbb'):
                    pass
                _x = it.reps['bbb']

        return cr

    cr = conf(prod)
    assert not cr.HasRepeatables

    cr = conf(dev1)
    assert cr.HasRepeatables.reps
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].aa == 'bbb'


def test_exclude_no_builder():
    def conf(env):
        with root(env, ef, name='esb') as cr:
            with HasRepeatables(name='r1', mc_exclude=[prod]) as it:
                with RepeatableItem('bbb'):
                    pass
                _x = it.reps['bbb']

        return cr

    cr = conf(prod)
    assert not cr.HasRepeatables

    cr = conf(dev1)
    assert cr.HasRepeatables.reps
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].name == 'bbb'


def test_exclude_with_builder_repeated():
    def conf(env):
        with root(env, ef, name='x') as cr:
            with HasRepeatables(name='r1', mc_exclude=[prod]) as it:
                BB('aaa')
                BB('bbb')
                with BB('ccc'):
                    pass
                _x = it.reps['bbb']
        return cr

    cr = conf(prod)
    assert not cr.HasRepeatables

    cr = conf(dev1)
    assert cr.HasRepeatables.reps
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].aa == 'bbb'


class ExclInBuild1(ConfigBuilder):
    def __init__(self):
        super(ExclInBuild1, self).__init__()

    def build(self):
        RepeatableItem(name='aaa', mc_exclude=[prod])
        RepeatableItem(name='bbb')


class ExclInBuild2(ConfigBuilder):
    def __init__(self):
        super(ExclInBuild2, self).__init__()

    def build(self):
        RepeatableItem(name='ccc', mc_exclude=None)
        with RepeatableItem(name='ddd') as ddd:
            ddd.mc_select_envs(exclude=[prod])
        self.mc_select_envs(exclude=[prod])
        RepeatableItem(name='bbb', mc_exclude=None)


def test_exclude_in_build():
    def conf(env):
        with root(env, ef, name='x') as cr:
            with HasRepeatables(name='r1', mc_exclude=None) as it:
                ExclInBuild1()
                ExclInBuild2()
                print(it)
                _x = it.reps['bbb']
        return cr

    cr = conf(prod)
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].name == 'bbb'
    assert cr.HasRepeatables.reps['ccc']
    assert len(cr.HasRepeatables.reps) == 2


def test_mc_select_envs_with_builder():
    @nested_repeatables('reps')
    class HasRepeatables2(ConfigItem):
        def __init__(self, name):
            super(HasRepeatables2, self).__init__()
            self.name = name
    
    def conf(env):
        with root(env, ef, name='x') as cr:
            with HasRepeatables2(name='r1') as it:
                with BB('bbb') as bbb:
                    bbb.mc_select_envs(exclude=[prod])

        return cr

    cr = conf(prod)
    assert not cr.HasRepeatables2.reps

    cr = conf(dev1)
    assert cr.HasRepeatables2.reps
    assert cr.HasRepeatables2.reps['bbb']
    assert cr.HasRepeatables2.reps['bbb'].aa == 'bbb'

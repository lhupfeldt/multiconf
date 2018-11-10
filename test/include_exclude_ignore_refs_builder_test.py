# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder
from multiconf.decorators import named_as, nested_repeatables
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithName


ef = EnvFactory()
dev1 = ef.Env('dev1')
prod = ef.Env('prod')


@nested_repeatables('reps')
class HasRepeatables(ConfigItem):
    def __init__(self, name, mc_exclude):
        super().__init__(mc_exclude=mc_exclude)
        self.name = name


@named_as('reps')
class RepeatableItem(RepeatableConfigItem):
    def __init__(self, mc_key, mc_exclude=None):
        super().__init__(mc_key=mc_key, mc_exclude=mc_exclude)
        self.name = mc_key
        self.aa = None


class BB(ConfigBuilder):
    def __init__(self, aa):
        super().__init__()
        self.aa = aa

    def mc_build(self):
        with RepeatableItem(self.aa) as ri:
            ri.aa = self.aa  # Note that pre v6 this assignment would have happened automatically


def test_exclude_with_builder():
    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName(name='x') as cr:
            with HasRepeatables(name='r1', mc_exclude=[prod]) as it:
                with BB('bbb'):
                    pass
                _x = it.reps['bbb']

    cr = config(prod).ItemWithName
    assert not cr.HasRepeatables

    cr = config(dev1).ItemWithName
    assert cr.HasRepeatables.reps
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].aa == 'bbb'


def test_exclude_no_builder():
    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName(name='esb') as cr:
            with HasRepeatables(name='r1', mc_exclude=[prod]) as it:
                with RepeatableItem('bbb'):
                    pass
                _x = it.reps['bbb']

        return cr

    cr = config(prod).ItemWithName
    assert not cr.HasRepeatables

    cr = config(dev1).ItemWithName
    assert cr.HasRepeatables.reps
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].name == 'bbb'


def test_exclude_with_builder_repeated():
    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName(name='x') as cr:
            with HasRepeatables(name='r1', mc_exclude=[prod]) as it:
                BB('aaa')
                BB('bbb')
                with BB('ccc'):
                    pass
                _x = it.reps['bbb']
        return cr

    cr = config(prod).ItemWithName
    assert not cr.HasRepeatables

    cr = config(dev1).ItemWithName
    assert cr.HasRepeatables.reps
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].aa == 'bbb'


class ExclInBuild1(ConfigBuilder):
    def __init__(self):
        super().__init__()

    def mc_build(self):
        RepeatableItem('aaa', mc_exclude=[prod])
        RepeatableItem('bbb')


class ExclInBuild2(ConfigBuilder):
    def __init__(self):
        super().__init__()

    def mc_build(self):
        RepeatableItem('ccc', mc_exclude=None)
        with RepeatableItem('ddd') as ddd:
            ddd.mc_select_envs(exclude=[prod])
        self.mc_select_envs(exclude=[prod])
        RepeatableItem('eee', mc_exclude=None)


def test_exclude_in_build():
    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName(name='x') as cr:
            with HasRepeatables(name='r1', mc_exclude=None) as it:
                ExclInBuild1()
                ExclInBuild2()
                _x = it.reps['bbb']
        return cr

    cr = config(dev1).ItemWithName
    assert cr.HasRepeatables.reps['aaa']
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].name == 'bbb'
    assert cr.HasRepeatables.reps['ccc']
    assert cr.HasRepeatables.reps['ddd']
    assert cr.HasRepeatables.reps['eee']
    assert len(cr.HasRepeatables.reps) == 5

    cr = config(prod).ItemWithName
    print(cr.HasRepeatables.reps)
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].name == 'bbb'
    assert cr.HasRepeatables.reps['ccc']
    assert len(cr.HasRepeatables.reps) == 2


def test_mc_select_envs_with_builder():
    @nested_repeatables('reps')
    class HasRepeatables2(ConfigItem):
        def __init__(self, name):
            super().__init__()
            self.name = name

    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName(name='x') as cr:
            with HasRepeatables2(name='r1') as it:
                with BB('bbb') as bbb:
                    bbb.mc_select_envs(exclude=[prod])

        return cr

    cr = config(prod).ItemWithName
    assert not cr.HasRepeatables2.reps

    cr = config(dev1).ItemWithName
    assert cr.HasRepeatables2.reps
    assert cr.HasRepeatables2.reps['bbb']
    assert cr.HasRepeatables2.reps['bbb'].aa == 'bbb'

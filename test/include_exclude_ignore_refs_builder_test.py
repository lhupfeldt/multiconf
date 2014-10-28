# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, ConfigItem, ConfigBuilder
from ..decorators import named_as, repeat, nested_repeatables

from ..envs import EnvFactory


ef = EnvFactory()
dev1 = ef.Env('dev1')
prod = ef.Env('prod')


class root(ConfigRoot):
    pass


@nested_repeatables('reps')
class HasRepeatables(ConfigItem):
    def __init__(self, name, mc_exclude):
        super(HasRepeatables, self).__init__(name=name, mc_exclude=mc_exclude)


@repeat()
@named_as('reps')
class Repeatable(ConfigItem):
    def __init__(self, name):
        super(Repeatable, self).__init__(name=name)


class BB(ConfigBuilder):
    def __init__(self, aa):
        super(BB, self).__init__()
        self.aa = aa

    def build(self):
        Repeatable(name=self.aa)


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
        with root(env, ef, name='esb', scrb_hostnames=[]) as cr:
            with HasRepeatables(name='r1', mc_exclude=[prod]) as it:
                with Repeatable('bbb'):
                    pass
                _x = it.reps['bbb']

        return cr

    cr = conf(prod)
    assert not cr.HasRepeatables

    cr = conf(dev1)
    assert cr.HasRepeatables.reps
    assert cr.HasRepeatables.reps['bbb']
    assert cr.HasRepeatables.reps['bbb'].name == 'bbb'

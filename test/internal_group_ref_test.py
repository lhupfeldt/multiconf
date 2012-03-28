# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
sys.path.append('../..')

from multiconf.multiconf import ConfigRoot, ConfigItem
from multiconf.multiconf import Env, EnvGroup

prod = Env('prod')
dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
g_dev = EnvGroup('g_dev', dev2st, dev2ct)

valid_envs = [g_dev, prod]

def conf(env):
    print '---- Creating ConfigRoot -----'
    with ConfigRoot(env, valid_envs) as dc:
        print '---- ConfigRoot block starting -----'
        dc.prod.ms_suffixes = [1, 2, 3, 4]
        dc.g_dev.ms_suffixes = [1]

        for ms_suffix in dc.ms_suffixes:
            print 'ms_suffix', ms_suffix
            print '---- Creating ConfigItem -----'
            with ConfigItem(True, suffix=ms_suffix) as c:
                print '---- ConfigItem block starting -----'
                assert c.suffix == ms_suffix
                print '---- ConfigItem block finished-----'

        print '---- ConfigRoot block finished -----'
        return dc


def test(env, exp_ms_suffixes, exp_suffix):
    print '---- Loading Config: ' + repr(env) + ' -----'
    c = conf(env)
    print '---- Loaded -----'
    print '---- Printing -----'
    print 'c.ms_suffixes:', repr(c.ms_suffixes)
    assert c.ms_suffixes == exp_ms_suffixes
    print 'c.ConfigItems:', repr(c.ConfigItems)
    print 'c.ConfigItems[0]:', repr(c.ConfigItems[0])
    print 'c.ConfigItems[0].suffix:', repr(c.ConfigItems[0].suffix)
    assert c.ConfigItems[0].suffix == exp_suffix
    print '---- Printed -----'

test(dev2ct, [1], 1)
test(prod, [1, 2, 3, 4], 1)

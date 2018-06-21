# Copyright (c) 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, threading, time

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException

from multiconf.decorators import named_as, nested_repeatables
from multiconf.envs import EnvFactory


ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


def test_property_attribute_access_threads():
    @named_as('someitem')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    def test0():
        @mc_config(ef, load_now=True)
        def config0(_):
            with Nested() as nn:
                nn.setattr('m', default=7, mc_overwrite_property=True)

        cr = config0(prod)
        time.sleep(0.06)
        assert cr.someitem.m == 7

    t0 = threading.Thread(target=test0, name='test0')

    def test1():
        @mc_config(ef, load_now=True)
        def config1(_):
            with Nested() as nn:
                nn.setattr('m', prod=7, mc_overwrite_property=True)

        cr = config1(prod)
        time.sleep(0.04)
        assert cr.someitem.m == 7

    t1 = threading.Thread(target=test1, name='test1')

    @mc_config(ef, load_now=True)
    def config2(_):
        with Nested() as nn:
            nn.setattr('m', pprd=7, mc_overwrite_property=True)

    def test2():
        cr = config2(prod)
        time.sleep(0.02)
        assert cr.someitem.m == 1

    t2 = threading.Thread(target=test2, name='test2')

    def test3():
        cr = config2(pprd)
        assert cr.someitem.m == 7

    t3 = threading.Thread(target=test3, name='test3')

    t0.start()
    t1.start()
    t2.start()
    t3.start()

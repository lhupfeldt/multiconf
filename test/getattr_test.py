# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, MC_REQUIRED, McInvalidValue, ConfigAttributeError
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA


ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)


def test_getattr_env():
    class root(ItemWithAA):
        def mc_init(self):
            self.setattr('aa', default=7, prod=8)

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        root()

    exp_indexed = [7, 8]
    exp_envs = {pp2: 7, prod2: 8}

    rt = config(prod2).root
    assert rt.aa == 8
    assert rt.getattr('aa', pp2) == 7
    assert rt.getattr('aa', prod2) == 8

    for ii, val in enumerate(rt.attr_env_values('aa')):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('aa'):
        assert val == exp_envs[env]

    rt = config(pp2).root
    assert rt.aa == 7
    assert rt.getattr('aa', pp2) == 7
    assert rt.getattr('aa', prod2) == 8

    for ii, val in enumerate(rt.attr_env_values('aa')):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('aa'):
        assert val == exp_envs[env]


def test_getattr_property():
    class root(ConfigItem):
        @property
        def myprop(self):
            return 17

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        root()

    exp_indexed = [17, 17]
    exp_envs = {pp2: 17, prod2: 17}

    rt = config(prod2).root
    assert rt.myprop == 17
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 17

    for ii, val in enumerate(rt.attr_env_values('myprop')):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('myprop'):
        assert val == exp_envs[env]

    rt = config(pp2).root
    assert rt.myprop == 17
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 17

    for ii, val in enumerate(rt.attr_env_values('myprop')):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('myprop'):
        assert val == exp_envs[env]


def test_getattr_overwritten_property():
    class root(ConfigItem):
        @property
        def myprop(self):
            return 17

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with root() as rt:
            rt.setattr('myprop', prod=18, mc_overwrite_property=True)

    exp_indexed = [17, 18]
    exp_envs = {pp2: 17, prod2: 18}

    rt = config(prod2).root
    assert rt.myprop == 18
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop')):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('myprop'):
        assert val == exp_envs[env]

    rt = config(pp2).root
    assert rt.myprop == 17
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop')):
        assert val == exp_indexed[ii]

def test_getattr_overwritten_property_ref_mc_attribute():
    class root(ConfigItem):
        def __init__(self, xx=MC_REQUIRED):
            super().__init__()
            self.xx = xx

        @property
        def myprop(self):
            return self.xx + 1

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with root() as rt:
            rt.setattr('xx', pp=15, prod=16)
            rt.setattr('myprop', prod=18, mc_overwrite_property=True)

    exp_indexed = [16, 18]

    rt = config(prod2).root
    assert rt.myprop == 18
    assert rt.getattr('myprop', pp2) == 16
    assert rt.getattr('myprop', prod2) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop')):
        assert val == exp_indexed[ii]

    rt = config(pp2).root
    assert rt.myprop == 16
    assert rt.getattr('myprop', pp2) == 16
    assert rt.getattr('myprop', prod2) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop')):
        assert val == exp_indexed[ii]


def test_getattr_overwritten_property_error():
    class root(ConfigItem):
        def __init__(self, xx=MC_REQUIRED):
            super().__init__()
            self.xx = xx

        @property
        def myprop(self):
            raise Exception("Error in myprop")

    @mc_config(ef2_pp_prod)
    def config(_):
        with root() as rt:
            rt.setattr('xx', pp=15, prod=16)
            rt.setattr('myprop', prod=18, mc_overwrite_property=True)

    exp_indexed = [McInvalidValue.MC_NO_VALUE, 18]
    exp_envs = {pp2: McInvalidValue.MC_NO_VALUE, prod2: 18}

    config.load(validate_properties=False)
    rt = config(prod2).root

    assert rt.myprop == 18
    with raises(Exception):
        _ = rt.getattr('myprop', pp2)

    assert rt.getattr('myprop', prod2) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop', ConfigAttributeError)):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('myprop', ConfigAttributeError):
        assert val == exp_envs[env]

    rt = config(pp2).root

    with raises(Exception):
        _ = rt.myprop

    with raises(Exception):
        _ = rt.getattr('myprop', pp2)

    assert rt.getattr('myprop', prod2) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop', ConfigAttributeError)):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('myprop', ConfigAttributeError):
        assert val == exp_envs[env]


def test_getattr_non_existing():
    class root(ConfigItem):
        pass

    @mc_config(ef2_pp_prod)
    def config(_):
        root()

    config.load(validate_properties=False)
    rt = config(prod2).root

    with raises(AttributeError):
        _ = rt.getattr('myprop', pp2)

    with raises(AttributeError):
        _ = rt.getattr('myprop', prod2)

    with raises(AttributeError):
        # This will yield the first value, but fail before yielding last error, when it is detected that attribute access fails for all envs
        for val in rt.attr_env_values('myprop', AttributeError):
            assert val == McInvalidValue.MC_NO_VALUE

    with raises(AttributeError):
        for env, val in rt.attr_env_items('myprop', AttributeError):
            assert val == McInvalidValue.MC_NO_VALUE


def test_attr_env_items_excluded_env():
    class item(ItemWithAA):
        def mc_init(self):
            self.setattr('aa', default=7)

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with item() as it:
            it.mc_select_envs(exclude=[prod2])

    exp_indexed = [7, McInvalidValue.MC_NO_VALUE]
    exp_envs = {pp2: 7, prod2: McInvalidValue.MC_NO_VALUE}

    it = config(prod2).item

    with raises(AttributeError):
        print(it.aa)

    assert it.getattr('aa', pp2) == 7

    with raises(AttributeError):
        it.getattr('aa', prod2)

    for ii, val in enumerate(it.attr_env_values('aa')):
        assert val == exp_indexed[ii]

    for env, val in it.attr_env_items('aa'):
        assert val == exp_envs[env]

    it = config(pp2).item
    assert it.aa == 7
    assert it.getattr('aa', pp2) == 7

    with raises(AttributeError):
        it.getattr('aa', prod2)

    for ii, val in enumerate(it.attr_env_values('aa')):
        assert val == exp_indexed[ii]

    for env, val in it.attr_env_items('aa'):
        assert val == exp_envs[env]


ef3_pprd_prod = EnvFactory()
tst3 = ef3_pprd_prod.Env('tst')
pprd3 = ef3_pprd_prod.Env('pprd')
prod3 = ef3_pprd_prod.Env('prod')
ef3_pprd_prod.EnvGroup('g_prod_like', pprd3, prod3)


def test_attr_env_items_excluded_multiple_envs():
    class item(ItemWithAA):
        def mc_init(self):
            self.setattr('aa', default=7)

    @mc_config(ef3_pprd_prod, load_now=True)
    def config(_):
        with item() as it:
            it.mc_select_envs(exclude=[tst3, prod3])

    exp_indexed = [McInvalidValue.MC_NO_VALUE, 7, McInvalidValue.MC_NO_VALUE]
    exp_envs = {tst3: McInvalidValue.MC_NO_VALUE, pprd3: 7, prod3: McInvalidValue.MC_NO_VALUE}

    it = config(prod3).item

    with raises(AttributeError):
        print(it.aa)

    assert it.getattr('aa', pprd3) == 7

    with raises(AttributeError):
        it.getattr('aa', prod3)

    for ii, val in enumerate(it.attr_env_values('aa')):
        assert val == exp_indexed[ii]

    for env, val in it.attr_env_items('aa'):
        assert val == exp_envs[env]

    it = config(pprd3).item
    assert it.aa == 7
    assert it.getattr('aa', pprd3) == 7

    with raises(AttributeError):
        it.getattr('aa', prod3)

    for ii, val in enumerate(it.attr_env_values('aa')):
        assert val == exp_indexed[ii]

    for env, val in it.attr_env_items('aa'):
        assert val == exp_envs[env]


def test_getattr_overwritten_property_error_multiple_envs_first_ok():
    class root(ConfigItem):
        def __init__(self, xx=MC_REQUIRED):
            super().__init__()
            self.xx = xx

        @property
        def myprop(self):
            raise Exception("Error in myprop")

    @mc_config(ef3_pprd_prod)
    def config(_):
        with root() as rt:
            rt.setattr('xx', tst=1, pprd=15, prod=16)
            rt.setattr('myprop', tst=17, prod=18, mc_overwrite_property=True)

    exp_indexed = [17, McInvalidValue.MC_NO_VALUE, 18]
    exp_envs = {tst3: 17, pprd3: McInvalidValue.MC_NO_VALUE, prod3: 18}

    config.load(validate_properties=False)
    rt = config(prod3).root

    assert rt.myprop == 18
    with raises(Exception):
        _ = rt.getattr('myprop', pprd3)

    assert rt.getattr('myprop', prod3) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop', ConfigAttributeError)):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('myprop', ConfigAttributeError):
        assert val == exp_envs[env]

    rt = config(pprd3).root

    with raises(Exception):
        _ = rt.myprop

    with raises(Exception):
        _ = rt.getattr('myprop', pprd3)

    assert rt.getattr('myprop', prod3) == 18

    for ii, val in enumerate(rt.attr_env_values('myprop', ConfigAttributeError)):
        assert val == exp_indexed[ii]

    for env, val in rt.attr_env_items('myprop', ConfigAttributeError):
        assert val == exp_envs[env]

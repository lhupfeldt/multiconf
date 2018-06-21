# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA

ef_dev_prod = EnvFactory()

dev2cta = ef_dev_prod.Env('dev2cta')
dev2sta = ef_dev_prod.Env('dev2sta')
dev2tta = ef_dev_prod.Env('dev2tta')

dev2ctb = ef_dev_prod.Env('dev2ctb')
dev2stb = ef_dev_prod.Env('dev2stb')
dev2ttb = ef_dev_prod.Env('dev2ttb')

g_dev2ctst1 = ef_dev_prod.EnvGroup('g_dev2ctst1', dev2cta, dev2sta, dev2ctb)  # No dev2stb
g_dev2ctst2 = ef_dev_prod.EnvGroup('g_dev2ctst2', dev2sta, dev2ctb, dev2stb)  # No dev2cta
g_dev2 = ef_dev_prod.EnvGroup('g_dev2', g_dev2ctst1, dev2tta, dev2ttb)

dev3ct = ef_dev_prod.Env('dev3ct')
dev3st = ef_dev_prod.Env('dev3st')
dev3tt = ef_dev_prod.Env('dev3tt')
g_dev3ctst = ef_dev_prod.EnvGroup('g_dev3ctst', dev3ct, dev3st)
g_dev3 = ef_dev_prod.EnvGroup('g_dev3', g_dev3ctst, dev3tt)

g_dev_overlap1 = ef_dev_prod.EnvGroup('g_dev_overlap1', dev2cta)
g_dev_overlap2 = ef_dev_prod.EnvGroup('g_dev_overlap2', dev2cta)

g_dev_overlap23ct = ef_dev_prod.EnvGroup('g_dev_overlap23ct', dev2cta, dev3ct)
g_dev_overlap23st = ef_dev_prod.EnvGroup('g_dev_overlap23st', dev2sta, dev3st)
g_dev_overlap23ctst = ef_dev_prod.EnvGroup('g_dev_overlap23ctst', dev2cta, dev3st)

pp = ef_dev_prod.Env('pp')
prod = ef_dev_prod.Env('prod')
g_prod = ef_dev_prod.EnvGroup('g_prod', pp, prod)


def test_value_defined_through_three_groups_resolved_immediately():
    @mc_config(ef_dev_prod, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.setattr('aa', g_dev_overlap2=7, default=7, dev2cta=15, prod=1, g_dev2=2, g_dev_overlap1=3)

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    cr = config(dev2cta).ItemWithAA
    assert cr.aa == 15


def test_value_defined_through_three_groups_resolved_immediately_multiple1():
    @mc_config(ef_dev_prod, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.setattr('aa', g_dev_overlap23ct=7, default=7, dev2cta=15, prod=1, g_dev2=2, g_dev_overlap23st=3, dev2sta=8)

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    cr = config(dev2cta).ItemWithAA
    assert cr.aa == 15


def test_value_defined_through_three_groups_resolved_immediately_multiple2():
    @mc_config(ef_dev_prod, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.setattr('aa', g_dev_overlap23ct=7, default=7, dev2cta=15, prod=1, g_dev2=2, g_dev_overlap23st=3, dev2sta=8, g_dev_overlap23ctst=23, dev3st=0)
            with ItemWithAA() as it1:
                it1.setattr('aa', g_dev_overlap23ct=7, default=7, prod=1, g_dev_overlap23st=3, g_dev_overlap23ctst=23, g_dev2=2, dev3st=0, dev2sta=8, dev2cta=15)
                with ItemWithAA() as it2:
                    it2.setattr('aa', g_dev_overlap23ct=7, g_dev_overlap23st=3, g_dev_overlap23ctst=23, g_dev2=2, dev3st=0, dev2sta=8, dev2cta=15, default=7, prod=1)
                    with ItemWithAA() as it3:
                        it3.setattr('aa', default=7, prod=1, g_dev_overlap23st=3, g_dev_overlap23ctst=23, g_dev2=2, dev3st=0, dev2sta=8, dev2cta=15)

    cr = config(prod).ItemWithAA
    assert cr.aa == 1
    assert cr.ItemWithAA.aa == 1
    assert cr.ItemWithAA.ItemWithAA.aa == 1
    assert cr.ItemWithAA.ItemWithAA.ItemWithAA.aa == 1

    cr = config(dev2cta).ItemWithAA
    assert cr.aa == 15
    assert cr.ItemWithAA.aa == 15
    assert cr.ItemWithAA.ItemWithAA.aa == 15
    assert cr.ItemWithAA.ItemWithAA.ItemWithAA.aa == 15



# Yes, **kwargs are not ordered, so these are just named differently, can give another order
# just to make sure we don't depend on the order
ef2_x_prod = EnvFactory()

x2ct2 = ef2_x_prod.Env('x2ct')
x2st2 = ef2_x_prod.Env('x2st')
x2tt2 = ef2_x_prod.Env('x2tt')
g_x2ctst2 = ef2_x_prod.EnvGroup('g_x2ctst', x2ct2, x2st2)
g_x22 = ef2_x_prod.EnvGroup('g_x2', g_x2ctst2, x2tt2)

x3ct2 = ef2_x_prod.Env('x3ct')
x3st2 = ef2_x_prod.Env('x3st')
x3tt2 = ef2_x_prod.Env('x3tt')
g_x3ctst2 = ef2_x_prod.EnvGroup('g_x3ctst', x3ct2, x3st2)
g_x32 = ef2_x_prod.EnvGroup('g_x3', g_x3ctst2, x3tt2)

g_x_overlap12 = ef2_x_prod.EnvGroup('g_x_overlap12', x2ct2)
g_x_overlap22 = ef2_x_prod.EnvGroup('g_x_overlap22', x2ct2)

g_x_overlap23ct2 = ef2_x_prod.EnvGroup('g_x_overlap23ct', x2ct2, x3ct2)
g_x_overlap23st2 = ef2_x_prod.EnvGroup('g_x_overlap23st', x2st2, x3st2)
g_x_overlap23ctst2 = ef2_x_prod.EnvGroup('g_x_overlap23ctst', x2ct2, x3st2)

pp2 = ef2_x_prod.Env('pp')
prod2 = ef2_x_prod.Env('prod')
g_prod2 = ef2_x_prod.EnvGroup('g_prod', pp2, prod2)


def test_value_defined_through_three_groups_resolved_multiple_x():
    @mc_config(ef2_x_prod, load_now=True)
    def config(root):
        with ItemWithAA() as cr:
            cr.setattr('aa', g_x_overlap23ct=7, default=7, x2st=8, prod=1, g_x2ctst=2, g_x_overlap23st=3, g_x_overlap23ctst=23, x3st=0, x2ct=15)
            with ItemWithAA() as it:
                it.setattr('aa', g_x_overlap23ct=7, default=7, prod=1, g_x_overlap23st=3, g_x_overlap23ctst=23, g_x2ctst=2, x3st=0, x2ct=15, x2st=8)
                with ItemWithAA() as it:
                    it.setattr('aa', g_x_overlap23ct=7, g_x_overlap23st=3, g_x_overlap23ctst=23, g_x2ctst=2, x3st=0, x2ct=15, x2st=8, default=7, prod=1)
                    with ItemWithAA() as it:
                        it.setattr('aa', default=7, prod=1, g_x_overlap23st=3, g_x_overlap23ctst=23, g_x2ctst=2, x3st=0, x2ct=15, x2st=8, g_x_overlap23ct=7)

    config(prod2)
    config(x2ct2)
    # TODO test values

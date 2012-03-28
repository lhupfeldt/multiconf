# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
sys.path.append('../..')

import unittest
from oktest import ok, test

from multiconf.envs import Env, EnvGroup
from multiconf._checked_insert_dict import CheckedInsertDict, CheckedInsertDictGroup, InsertException

pp = Env('pp')
prod = Env('prod')
g_prod = EnvGroup('g_prod', pp, prod)

dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
g_dev2 = EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = Env('dev3CT')
dev3st = Env('dev3ST')
g_dev3 = EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = EnvGroup('g_dev', g_dev2, g_dev3)

cidg = CheckedInsertDictGroup()

cid_prod = CheckedInsertDict(cidg, prod)
cid_g_prod = CheckedInsertDict(cidg, g_prod)

cid_g_dev = CheckedInsertDict(cidg, g_dev)
cid_g_dev2 = CheckedInsertDict(cidg, g_dev2)
cid_dev2ct = CheckedInsertDict(cidg, dev2ct)
cid_dev2st = CheckedInsertDict(cidg, dev2st)
cid_dev3ct = CheckedInsertDict(cidg, dev3ct)
cid_dev3st = CheckedInsertDict(cidg, dev3st)
cid_g_dev3 = CheckedInsertDict(cidg, g_dev3)

class CheckedInsertTest(unittest.TestCase):
    @test("Checked Insert Dict")
    def _0(self):
        # Verify setting value directly through env
        cid_prod.a = 11
        ok (cidg.check_confs[prod]['a']) == 11

        # Verify setting value through group
        cid_g_prod.b = 12
        ok (cidg.check_confs[g_prod]['b']) == 12

        # Verify that a value set through a group may be overridden by setting it directly through env
        cid_prod.b = 1
        ok (cidg.check_confs[prod]['b']) == 1

        # Verify setting value through multiple side ordered groups contained in same group
        cid_g_dev2.f = 12
        ok (cidg.check_confs[g_dev2]['f']) == 12
        cid_g_dev3.f = 13
        ok (cidg.check_confs[g_dev3]['f']) == 13

        # Verify that the same env + key combo can't be specified more that once
        try:
            print "expect exception:"
            cid_prod.a = 2
        except InsertException as ex:
            print ex.__class__.__name__ + ':', ex
        else:
            raise Exception("missing exception")

        # Verify that the same group + key combo can't be specified more that once
        cid_g_prod.c = 1
        ok (cidg.check_confs[g_prod]['c']) == 1
        try:
            print "expect exception:"
            cid_g_prod.c = 2
        except InsertException as ex:
            print ex.__class__.__name__ + ':', ex
        else:
            raise Exception("missing exception")

        # Verify that a value specified through a env can't be overridden by a group
        cid_dev2ct.d = 3
        ok (cidg.check_confs[dev2ct]['d']) == 3
        try:
            print "expect exception:"
            cid_g_dev2.d = 4
        except InsertException as ex:
            print ex.__class__.__name__ + ':', ex
        else:
            raise Exception("missing exception")

        # Verify that a value specified through a env can't be overridden by a group nested
        cid_dev2ct.e = 3
        ok (cidg.check_confs[dev2ct]['e']) == 3
        try:
            print "expect exception:"
            cid_g_dev.e = 4
        except InsertException as ex:
            print ex.__class__.__name__ + ':', ex
        else:
            raise Exception("missing exception")

        # Verify that a value specified through a group can't be overridden by a (TODO: more generic?) group
        cid_g_dev2.b = 4
        ok (cidg.check_confs[g_dev2]['b']) == 4
        try:
            print "expect exception:"
            cid_g_dev.b = 3
        except InsertException as ex:
            print ex.__class__.__name__ + ':', ex
        else:
            raise Exception("missing exception")

if __name__ == '__main__':
    unittest.main()

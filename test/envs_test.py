#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import unittest
from oktest import ok, test

from multiconf.envs import Env, EnvGroup

envs_only = []

dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
envs_only.extend((dev2ct, dev2st))
g_dev2 = EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = Env('dev3CT')
dev3st = Env('dev3ST')
envs_only.extend((dev3ct, dev3st))
g_dev3 = EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = EnvGroup('g_dev', g_dev2, g_dev3)

pp = Env('pp')
prod = Env('prod')
envs_only.extend((pp, prod))
g_prod = EnvGroup('g_prod', pp, prod)

valid_envs = EnvGroup('g_all', g_dev, g_prod)

groups_only = [valid_envs, g_dev, g_dev2, g_dev3, g_prod]
all_envs = groups_only + envs_only

valid_envs_repr = """
EnvGroup('g_all') {
     EnvGroup('g_dev') {
       EnvGroup('g_dev2') {
         Env('dev2CT'),
         Env('dev2ST')
    },
       EnvGroup('g_dev3') {
         Env('dev3CT'),
         Env('dev3ST')
    }
  },
     EnvGroup('g_prod') {
       Env('pp'),
       Env('prod')
  }
}
"""


class EnvsTest(unittest.TestCase):

    @test("repr of valid_envs")
    def _0(self):
        ok (repr(valid_envs)) == valid_envs_repr.strip()

    @test("Membership")
    def _1(self):
        # Env is in itself
        ok (prod in prod) == True
        # Group is in itself
        ok (g_dev in g_dev) == True

        ok (prod in valid_envs) == True
        ok (prod not in g_dev) == True
        ok (g_dev not in g_prod) == True
        ok (dev2ct in g_dev2) == True
        ok (dev2ct in g_dev) == True
        ok (dev2ct not in g_dev3) == True
        ok (g_dev2 in g_dev) == True
        ok (g_dev not in g_dev2) == True
    
    @test("Iterating envs only")
    def _2(self):
        envs = []
        for env in valid_envs.envs():
            envs.append(env)
        ok (envs) == envs_only
    

    @test("Iterating Groups only")
    def _3(self):
        groups = []
        for group in valid_envs.groups():
            groups.append(group)
        ok (groups) == groups_only
    
    @test("Iterating Groups and Envs")
    def _4(self):
        envs = []
        for env in valid_envs.all():
            envs.append(env)
        ok (envs) == all_envs

    @test("As key")
    def _5(self):
        envs = {}
        for env in valid_envs.all():
            envs[env] = True
        for env in valid_envs.all():
            ok (envs[env]) == True

if __name__ == '__main__':
    unittest.main()

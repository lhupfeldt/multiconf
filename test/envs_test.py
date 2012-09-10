#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test

from ..envs import EnvFactory

ef = EnvFactory()

envs_only = []

dev2ct = ef.Env('dev2CT')
dev2st = ef.Env('dev2ST')
envs_only.extend((dev2ct, dev2st))
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3CT')
dev3st = ef.Env('dev3ST')
envs_only.extend((dev3ct, dev3st))
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
envs_only.extend((pp, prod))
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)

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

    @test("env from string")
    def _l(self):
        ok(ef.env("dev2CT").name) == "dev2CT"

    @test("group from string")
    def _m(self):
        ok(ef.group("g_dev2").name) == "g_dev2"

    @test("env_or_group from string")
    def _n(self):
        ok(ef.env_or_group("dev2CT").name) == "dev2CT"
        ok(ef.env_or_group("g_dev2").name) == "g_dev2"

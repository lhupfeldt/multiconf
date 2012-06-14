#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import unittest
from oktest import ok, test, fail, dummy
from utils import config_error, lineno

from ..envs import Env, EnvGroup, EnvException, env, group, env_or_group

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

class EnvsTest(unittest.TestCase):

    @test("env member with same name as self")
    def _c1(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                cc11 = Env('cc11')
                errorline = lineno() + 1
                cc11 = EnvGroup('cc11', cc11)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Can't have a member with my own name: 'cc11', members:  [Env('cc11')]"

    @test("group member with same name as self")
    def _c2(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                cc21 = Env('cc21')
                cc22 = EnvGroup('cc22', cc21)
                errorline = lineno() + 1
                cc22 = EnvGroup('cc22', cc22)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Can't have a member with my own name: 'cc22', members:  [EnvGroup('cc22') {\n     Env('cc21')\n}]"

    @test("repeated direct env member")
    def _f(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                ff1 = Env('ff1')
                errorline = lineno() + 1
                ff2 = EnvGroup('ff2', ff1, ff1)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Repeated group member: Env('ff1') in EnvGroup('ff2') {\n\n}"

    @test("repeated direct group member")
    def _g(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                gg1 = Env('gg1')
                gg2 = EnvGroup('gg2', gg1)
                errorline = lineno() + 1
                gg3 = EnvGroup('gg3', gg2, gg2)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Repeated group member: EnvGroup('gg2') {\n     Env('gg1')\n} in EnvGroup('gg3') {\n\n}"

    @test("repeated nested env member")
    def _h(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                hh1 = Env('hh1')
                hh2 = EnvGroup('hh2', hh1)
                errorline = lineno() + 1
                hh3 = EnvGroup('hh3', hh1, hh2)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Repeated group member: Env('hh1') in EnvGroup('hh3') {\n\n}"

    @test("repeated nested env member reversed")
    def _i(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                ii1 = Env('ii1')
                ii2 = EnvGroup('ii2', ii1)
                errorline = lineno() + 1
                ii3 = EnvGroup('ii3', ii2, ii1)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Repeated group member: Env('ii1') in EnvGroup('ii3') {\n\n}"

    @test("repeated nested group member")
    def _j(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                jj1 = Env('jj1')
                jj2 = EnvGroup('jj2', jj1)
                jj3 = EnvGroup('jj3', jj2)
                errorline = lineno() + 1
                jj4 = EnvGroup('jj4', jj3, jj2)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Repeated group member: EnvGroup('jj2') {\n     Env('jj1')\n} in EnvGroup('jj4') {\n\n}"

    @test("repeated nested group member reversed")
    def _k(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                jj1 = Env('jj1')
                jj2 = EnvGroup('jj2', jj1)
                jj3 = EnvGroup('jj3', jj2)
                errorline = lineno() + 1
                jj4 = EnvGroup('jj4', jj2, jj3)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            #ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "Repeated group member: EnvGroup('jj2') {\n     Env('jj1')\n} in EnvGroup('jj4') {\n\n}"

    @test("env from string - undefined")
    def _l(self):
        try:
            env("undefined")
            fail ("Expected exception")
        except EnvException as ex:
            ok (ex.message) == "No such Env: 'undefined'"

    @test("group from string - undefined")
    def _m(self):
        try:
            group("undefined")
            fail ("Expected exception")
        except EnvException as ex:
            ok (ex.message) == "No such EnvGroup: 'undefined'"

    @test("env_or_group from string - undefined")
    def _n(self):
        try:
            env_or_group("undefined")
            fail ("Expected exception")
        except EnvException as ex:
            ok (ex.message) == "No such Env or EnvGroup: 'undefined'"

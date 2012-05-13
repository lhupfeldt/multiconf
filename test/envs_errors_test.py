#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

import unittest
from oktest import ok, test, fail, todo, dummy
from utils import lazy, config_error, lineno

from multiconf.envs import Env, EnvGroup, EnvException

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

class EnvsTest(unittest.TestCase):

    @test("redefined env")
    def _a(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                aa = Env('aa')
                errorline = lineno() + 1
                aa = Env('aa')
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

    @test("redefined group")
    def _b(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                bb1 = Env('bb')
                bb2 = EnvGroup('bb', bb)
                errorline = lineno() + 1
                bb3 = EnvGroup('bb', bb)
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

    @test("group redefines env")
    def _d(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                dd1 = Env('dd')
                errorline = lineno() + 1
                dd2 = EnvGroup('dd')
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

    @test("env redefines group")
    def _e(self):
        try:
            with dummy.dummy_io('stdin not used') as d_io:
                ee1 = Env('ee1')
                ee2 = EnvGroup('ee2', ee1)
                errorline = lineno() + 1
                ee2 = Env('ee2')
                fail ("Expected exception")
        except EnvException as ex:
            sout, serr = d_io
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

    @test("repeated nested group member reversed")
    def _j(self):
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
            ok (serr) == ce(errorline, "TODO")
            ok (ex.message) == "TODO"

if __name__ == '__main__':
    unittest.main()

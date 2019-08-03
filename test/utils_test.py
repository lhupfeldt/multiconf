# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import caller_file_line

from .utils.utils import next_line_num

from .utils_test_helpers import bb, fn_aa_exp, ln_aa_exp


ln_bb_exp = None


def test_caller_file_line():
    def cc():
        global ln_bb_exp

        fnc, lnc = caller_file_line(2)
        print("fnc, lnc:", fnc, lnc)

        ln_bb_exp = next_line_num()
        fnb, lnb, fna, lna = bb()

        return fnc, lnc, fnb, lnb, fna, lna

    fn_exp = __file__
    ln_cc_exp = next_line_num()
    fnc, lnc, fnb, lnb, fna, lna = cc()

    assert fn_exp == fnc
    assert ln_cc_exp == lnc

    assert fn_exp == fnb
    assert ln_bb_exp == lnb

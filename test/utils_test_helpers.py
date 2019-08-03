# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import caller_file_line

from .utils.utils import next_line_num


fn_aa_exp = __file__
ln_aa_exp = None


def aa():
    fna, lna = caller_file_line()
    print("fna, lna:", fna, lna)

    return fna, lna


def bb():
    global ln_aa_exp

    fnb, lnb = caller_file_line()
    print("fnb, lnb:", fnb, lnb)

    ln_aa_exp = next_line_num()
    fna, lna = aa()

    return fnb, lnb, fna, lna

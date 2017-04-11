# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


def int_to_bin_str(value, max_bits=8192):
    """Convert an int to a string representation of a bitmask (binary number)"""

    mask = value

    bits = 1
    while 1 << bits < value or bits < 16 and bits < max_bits:
        bits *= 2

    rep = ''
    while bits:
        rep = ('1' if mask & 1 else '0') + rep
        bits = bits - 1
        mask = mask >> 1
    return '0b' + rep

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.bits import int_to_bin_str


def test_int_to_bin_str():
    all_envs = 0b01100011

    exclude_a = 0b00000110
    exclude_b = 0b00101100

    included_a = 0b00111011
    included_b = 0b00001101

    included = all_envs & ~exclude_a
    assert int_to_bin_str(included) == '0b0000000001100001'

    included = included & ~exclude_b
    assert int_to_bin_str(included) == '0b0000000001000001'

    included = included & included_a
    assert int_to_bin_str(included) == '0b0000000000000001'

    included = included & included_b
    assert int_to_bin_str(included) == '0b0000000000000001'

    large = 0b11000110010010110000000000000000000000000000000000000000000000000000000000000000
    assert int_to_bin_str(large) == '0b00000000000000000000000000000000000000000000000011000110010010110000000000000000000000000000000000000000000000000000000000000000'

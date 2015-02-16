from __future__ import print_function
from collections import OrderedDict

from ..bits import int_to_bin_str


e0 = 0b00000001
e1 = 0b00000010
e2 = 0b00000100
e3 = 0b00001000
e4 = 0b00010000
e5 = 0b00100000
e6 = 0b01000000
e7 = 0b10000000

ga = 0b00001111  # e0 - e3
gb = 0b11110000  # e4 - e7
gc = 0b00111100  # e2 - e5
gd = 0b00001100  # e2 - e3
ge = 0b00011101  # e0, e2 - e4
gf = 0b10001000  # e3, e7


def mask_in_or_eq_other(mask, other):
    return mask & other == mask


def mask_in_other(mask, other):
    return mask & other == mask and mask != other


def trace(*args):
    print(*args)


def aarep(all_ambiguous):
    return [(key, int_to_bin_str(amb)) for key, amb in all_ambiguous.items()]


def ttt(current_env, *env_masks):
    trace("*********************************")
    current_env_from_index = None
    all_ambiguous = OrderedDict()
    all_masks = 0x0

    trace()
    trace("Starting update and check loop, current_env:", int_to_bin_str(current_env), "env_masks:", env_masks)
    for ii, mask in enumerate(env_masks):
        trace()
        trace('------------------------')

        all_masks |= mask
        trace("New:", ii, int_to_bin_str(mask), "All masks:", int_to_bin_str(all_masks))

        for jj, other_mask in enumerate(env_masks[:ii]):
            trace()
            trace("Other:", jj, int_to_bin_str(other_mask))
            more_specific = mask_in_other(mask, other_mask)
            less_specific = mask_in_other(other_mask, mask)
            trace("New in other:", more_specific)
            trace("Other in new:", less_specific)

            ambiguous = 0x0
            if not (less_specific or more_specific):
                ambiguous = mask & other_mask
                if ambiguous:
                    all_ambiguous[(ii, jj)] = ambiguous
                    trace("Found Ambiguous:", int_to_bin_str(ambiguous), aarep(all_ambiguous))
                else:
                    all_masks |= mask
                    trace("No overlap, All masks:", int_to_bin_str(all_masks))
            elif more_specific:
                all_masks |= mask
                trace("More specific, All masks:", int_to_bin_str(all_masks))
            elif less_specific:
                trace("Less specific")

        if mask_in_or_eq_other(current_env, mask):
            if current_env_from_index is not None:
                current_env_from_mask = env_masks[current_env_from_index]
                if mask_in_other(mask, current_env_from_mask):
                    current_env_from_index = ii
                    trace("Current env value reset at index:", current_env_from_index, "from mask:", int_to_bin_str(mask))
            else:
                current_env_from_index = ii
                trace("Current env value initial setting at index:", current_env_from_index, "from mask:", int_to_bin_str(mask))

        trace("All masks:", int_to_bin_str(all_masks) + ", All Ambiguous:", aarep(all_ambiguous))

    trace()
    trace("Starting resolve ambiguities loop, all_ambiguous:", aarep(all_ambiguous))
    for mask in env_masks:
        trace()
        cleared = []
        for key, ambiguous in all_ambiguous.items():
            eq_or_more_specific = mask_in_or_eq_other(mask, ambiguous)
            trace("Checking Ambiguous:", key, int_to_bin_str(ambiguous) + ", mask:", int_to_bin_str(mask) + ", Eq or More specific:", eq_or_more_specific)
            if eq_or_more_specific:
                ambiguous ^= mask & ambiguous
                if ambiguous:
                    all_ambiguous[key] = ambiguous
                    trace("Clearing ambigueties:", key, int_to_bin_str(ambiguous))
                else:
                    cleared.append(key)
                    trace("Cleared all ambigueties for key:", key)

        for key in cleared:
            del all_ambiguous[key]

        trace("All Ambiguous:", aarep(all_ambiguous))

    trace("Final All masks:", int_to_bin_str(all_masks) + ", All Ambiguous:", aarep(all_ambiguous))
    if current_env_from_index is not None:
        trace("Final env value from mask:", env_masks[current_env_from_index], "at index:", current_env_from_index)
    else:
        trace("Final env value not found")
    return current_env_from_index, all_masks, all_ambiguous


def test1():
    assert ttt(e0, e0, e1, e2) == (0, 0b111, {})


def test2():
    assert ttt(e0, e0, e1, e2, e3, e4, e5, e6, e7) == (0, 0b11111111, {})


def test3():
    assert ttt(e0, ga, gc) == (0, 0b00111111, {(1, 0): 0b00001100})


def test4():
    assert ttt(e0, ga, gc, e2, e3) == (0, 0b00111111, {})


def test5():
    assert ttt(e0, e2, ga, e3, gc) == (1, 0b00111111, {})


def test6():
    assert ttt(e0, e0, e1, e2, e3, e4, e5, e6, e7, ga, gb, gc) == (0, 0b11111111, {})


def test7():
    assert ttt(e0, ga, gb, gc, e0, e1, e2, e3, e4, e5, e6, e7) == (3, 0b11111111, {})


def test8():
    assert ttt(e0, ga, gb, gc) == (0, 0b11111111, {(2, 0): 0b00001100, (2, 1): 0b00110000})
    assert ttt(e0, gb, gc, ga) == (2, 0b11111111, {(1, 0): 0b00110000, (2, 1): 0b00001100})
    assert ttt(e0, gc, ga, gb) == (1, 0b11111111, {(1, 0): 0b00001100, (2, 0): 0b00110000})
    assert ttt(e0, ga, gc, gb) == (0, 0b11111111, {(1, 0): 0b00001100, (2, 1): 0b00110000})


def test9():
    exp1 = {
        (2, 1): 0b00110000,
        (4, 0): 0b00000001,
        (4, 1): 0b00010000,
        (4, 2): 0b00010000,
    }
    assert ttt(e0, ga, gb, gc, gd, ge) == (0, 0b11111111, exp1)

    masks = sorted(exp1.values())

    res2 = ttt(e0, ge, ga, gb, gc, gd)
    assert sorted(res2[2].values()) == masks
    res3 = ttt(e0, gd, ge, ga, gb, gc)
    assert sorted(res3[2].values()) == masks
    res4 = ttt(e0, gc, gd, ge, ga, gb)
    assert sorted(res4[2].values()) == masks
    res5 = ttt(e0, gb, gc, gd, ge, ga)
    assert sorted(res5[2].values()) == masks


def test10():
    exp1 = {
        (2, 1): 0b00110000,
        (4, 1): 0b00010000,
        (4, 2): 0b00010000,
    }
    assert ttt(e0, ga, gb, gc, gd, ge, e0) == (5, 0b11111111, exp1)

    masks = sorted(exp1.values())

    res2 = ttt(e0, e0, ga, gb, gc, gd, ge)
    assert sorted(res2[2].values()) == masks
    res3 = ttt(e0, ge, e0, ga, gb, gc, gd)
    assert sorted(res3[2].values()) == masks
    res4 = ttt(e0, gd, ge, e0, ga, gb, gc)
    assert sorted(res4[2].values()) == masks
    res5 = ttt(e0, gc, gd, ge, e0, ga, gb)
    assert sorted(res5[2].values()) == masks
    res6 = ttt(e0, gb, gc, gd, ge, e0, ga)
    assert sorted(res6[2].values()) == masks


def test11():
    assert ttt(e0, ga) == (0, ga, {})
    assert ttt(e0, gb) == (None, gb, {})
    assert ttt(e0, gc) == (None, gc, {})
    assert ttt(e0, gd) == (None, gd, {})
    assert ttt(e0, ge) == (0, ge, {})

    assert ttt(e1, ga) == (0, ga, {})
    assert ttt(e1, gb) == (None, gb, {})
    assert ttt(e1, gc) == (None, gc, {})
    assert ttt(e1, gd) == (None, gd, {})
    assert ttt(e1, ge) == (None, ge, {})

    assert ttt(e2, ga) == (0, ga, {})
    assert ttt(e2, gb) == (None, gb, {})
    assert ttt(e2, gc) == (0, gc, {})
    assert ttt(e2, gd) == (0, gd, {})
    assert ttt(e2, ge) == (0, ge, {})

    assert ttt(e3, ga) == (0, ga, {})
    assert ttt(e3, gb) == (None, gb, {})
    assert ttt(e3, gc) == (0, gc, {})
    assert ttt(e3, gd) == (0, gd, {})
    assert ttt(e3, ge) == (0, ge, {})

    assert ttt(e4, ga) == (None, ga, {})
    assert ttt(e4, gb) == (0, gb, {})
    assert ttt(e4, gc) == (0, gc, {})
    assert ttt(e4, gd) == (None, gd, {})
    assert ttt(e4, ge) == (0, ge, {})

    assert ttt(e5, ga) == (None, ga, {})
    assert ttt(e5, gb) == (0, gb, {})
    assert ttt(e5, gc) == (0, gc, {})
    assert ttt(e5, gd) == (None, gd, {})
    assert ttt(e5, ge) == (None, ge, {})

    assert ttt(e6, ga) == (None, ga, {})
    assert ttt(e6, gb) == (0, gb, {})
    assert ttt(e6, gc) == (None, gc, {})
    assert ttt(e6, gd) == (None, gd, {})
    assert ttt(e6, ge) == (None, ge, {})

    assert ttt(e7, ga) == (None, ga, {})
    assert ttt(e7, gb) == (0, gb, {})
    assert ttt(e7, gc) == (None, gc, {})
    assert ttt(e7, gd) == (None, gd, {})
    assert ttt(e7, ge) == (None, ge, {})


def test12():
    assert ttt(e0, ga, gb, gc) == (0, 0b11111111, {(2, 0): 0b00001100, (2, 1): 0b00110000})
    assert ttt(e1, gb, gc, ga) == (2, 0b11111111, {(1, 0): 0b00110000, (2, 1): 0b00001100})
    assert ttt(e2, gc, ga, gb) == (0, 0b11111111, {(1, 0): 0b00001100, (2, 0): 0b00110000})
    assert ttt(e3, ga, gc, gb) == (0, 0b11111111, {(1, 0): 0b00001100, (2, 1): 0b00110000})
    assert ttt(e4, ga, gb, gc) == (1, 0b11111111, {(2, 0): 0b00001100, (2, 1): 0b00110000})
    assert ttt(e5, gb, gc, ga) == (0, 0b11111111, {(1, 0): 0b00110000, (2, 1): 0b00001100})
    assert ttt(e6, gc, ga, gb) == (2, 0b11111111, {(1, 0): 0b00001100, (2, 0): 0b00110000})
    assert ttt(e7, ga, gc, gb) == (2, 0b11111111, {(1, 0): 0b00001100, (2, 1): 0b00110000})


def test13():
    """Resolve ambigueties, set correct value"""
    assert ttt(e0, ga, gb, gc, gd) == (0, 0b11111111, {(2, 1): 0b00110000})
    assert ttt(e1, gb, gc, ga, gd) == (2, 0b11111111, {(1, 0): 0b00110000})
    assert ttt(e2, gc, ga, gb, gd) == (3, 0b11111111, {(2, 0): 0b00110000})
    assert ttt(e3, ga, gc, gb, gd) == (3, 0b11111111, {(2, 1): 0b00110000})
    assert ttt(e4, ga, gb, gc, gd, e4) == (4, 0b11111111, {(2, 1): 0b00100000})
    assert ttt(e5, gb, gc, ga, gd, e5) == (4, 0b11111111, {(1, 0): 0b00010000})
    assert ttt(e6, gc, ga, gb, gd, e6) == (4, 0b11111111, {(2, 0): 0b00110000})
    assert ttt(e7, ga, gc, gb, gd, e7) == (4, 0b11111111, {(2, 1): 0b00110000})

    assert ttt(e0, ga, gb, gd, gc) == (0, 0b11111111, {(3, 1): 0b00110000})
    assert ttt(e1, gb, gc, gd, ga) == (3, 0b11111111, {(1, 0): 0b00110000})
    assert ttt(e2, gc, ga, gd, gb) == (2, 0b11111111, {(3, 0): 0b00110000})
    assert ttt(e3, ga, gc, gd, gb) == (2, 0b11111111, {(3, 1): 0b00110000})
    assert ttt(e4, ga, gb, gd, e4, gc) == (3, 0b11111111, {(4, 1): 0b00100000})
    assert ttt(e5, gb, gc, gd, e5, ga) == (3, 0b11111111, {(1, 0): 0b00010000})
    assert ttt(e6, gc, ga, gd, e6, gb) == (3, 0b11111111, {(4, 0): 0b00110000})
    assert ttt(e7, ga, gc, gd, e7, gb) == (3, 0b11111111, {(4, 1): 0b00110000})


def test14():
    """Resolve multiple overlapping ambigueties, set correct value"""
    assert ttt(e0, ga, gb, gc, gf) == (
        0, 0b11111111, {
            (2, 0): 0b00001100,
            (2, 1): 0b00110000,
            (3, 0): 0b00001000,
            (3, 1): 0b10000000,
            (3, 2): 0b00001000
        }
    )

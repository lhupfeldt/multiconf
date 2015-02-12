# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from ..repeatable import Repeatable, UserRepeatable


def test_copy_repeatable():
    attr1 = Repeatable((('a', 1),('b', 2)))
    attr1['c'] = 3
    attr2 = attr1.copy()
    assert attr1 == attr2
    assert attr1 is not attr2


def test_copy_user_repeatable():
    class A():
        pass
    attr1 = UserRepeatable()
    attr1.contained_in = A()
    attr1['a'] = 1
    attr1['b'] = 2

    attr2 = attr1.copy()
    assert attr1 == attr2
    assert attr1 is not attr2

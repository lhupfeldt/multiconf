# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.values import MC_REQUIRED


def test_mc_required_false():
    assert not MC_REQUIRED


def test_mc_required_repr():
    assert repr(MC_REQUIRED) == "MC_REQUIRED"

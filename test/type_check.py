# Copyright (c) 2012-2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys

_major_version = sys.version_info[0]
_minor_version = sys.version_info[1]
_patch_version = sys.version_info[2]

_min_major_version = 3
_min_minor_version = 6
_min_patch_version = 1

skip_version_reason_unsupported = "Type checking only supported from Python {}.{}".format(_min_major_version, _min_minor_version)
skip_version_reason_supported = "Type checking supported for this version"

def vcheck():
    """Return True if version requirement is satisfied."""
    return _major_version > _min_major_version or (
        _major_version == _min_major_version and _minor_version >= _min_minor_version) or (
            _major_version == _min_major_version and _minor_version == _min_minor_version and _patch_version >= _min_patch_version)

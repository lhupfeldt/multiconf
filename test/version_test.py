import re

import multiconf


def test_version_of_properly_installe_package():
    assert re.match(r"[0-9]+\.[0-9]+\.[0-9]+.*", multiconf.__version__)

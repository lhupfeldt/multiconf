import sys, os

import pytest

# Put source dir first in path

here = os.path.dirname(os.path.abspath(__file__))
mc_dir = os.path.join(os.path.dirname(here), 'multiconf')
sys.path.insert(0, here)

os.environ['MULTICONF_WARN_JSON_NESTING'] = "false"

py3 = sys.version_info[0] >= 3


class DummyCollector(pytest.collect.File):
    def collect(self):
        return []


def pytest_pycollect_makemodule(path, parent):
    bn = path.basename
    if "py3" in bn and not py3 or ("py2" in bn and py3):
        return DummyCollector(path, parent=parent)

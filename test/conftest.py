import sys, os

import pytest

# Put source dir first in path

here = os.path.dirname(os.path.abspath(__file__))
mc_dir = os.path.join(os.path.dirname(here), 'multiconf')
sys.path.insert(0, here)

os.environ['MULTICONF_WARN_JSON_NESTING'] = "false"

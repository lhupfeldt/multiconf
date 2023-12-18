"""Configuration file for 'pytest'"""

import os
import errno
from pathlib import Path
import shutil

from pytest import fixture


_HERE = Path(__file__).absolute().parent

_OUT_DIRS = {}

def _test_key_shortener(key_prefix, key_suffix):
    prefix = key_prefix.replace('test.', '').replace('_test', '')
    suffix = key_suffix.replace(prefix, '').replace('test_', '').strip('_')
    outd = prefix + '.' + suffix
    args = (key_prefix, key_suffix)
    assert _OUT_DIRS.setdefault(outd, args) == args, \
        f"Out dir name '{outd}' reused! Previous from {_OUT_DIRS[outd]}, now  {args}. Test is not following namimg convention."
    return outd


def _test_node_shortener(request):
    """Shorten test node name while still keeping it unique"""
    return _test_key_shortener(request.node.module.__name__, request.node.name.split('[')[0])


@fixture(name="out_dir")
def _fixture_out_dir(request):
    """Create unique top level test directory for a test."""

    out_dir = _HERE/'out'/_test_node_shortener(request)

    try:
        shutil.rmtree(out_dir)
    except OSError as ex:
        if ex.errno != errno.ENOENT:
            raise

    return out_dir

# Add you configuration, e.g. fixtures here.

os.environ['MULTICONF_WARN_JSON_NESTING'] = "false"

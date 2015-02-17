#!/bin/env python

from __future__ import print_function

import sys, os, subprocess

try:
    import pytest
except ImportError:
    print("See setup.py for test requirements, or use 'python setup.py test'", file=sys.stderr)
    raise

here = os.path.abspath(os.path.dirname(__file__))


def main(args):
    os.environ['MULTICONF_WARN_JSON_NESTING'] = 'true'

    print("Running tests", args)
    if args and args != ['-v']:
        return pytest.main(['--capture=sys'] + args)
    rc = pytest.main(['--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing'] + (args if args == ['-v'] else []))

    print("Validating demo for all envs")
    try:
        del os.environ['PYTHONPATH']
    except KeyError:
        pass
    for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
        print()
        rc |= subprocess.call((sys.executable, here + '/../demo/demo.py', '--env', env_name))

    return rc


if __name__ == '__main__':
    main(sys.argv[1:])

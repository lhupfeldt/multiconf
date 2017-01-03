from __future__ import print_function

import sys, os, subprocess
from os.path import join as jp

import pytest

import tenjin
from tenjin.helpers import *


here = os.path.abspath(os.path.dirname(__file__))


def main(args):
    print("Running tests, args:", args)
    if args and args != ['-v']:
        return pytest.main(['--capture=sys'] + args)

    engine = tenjin.Engine()
    major_version = sys.version_info[0]
    cov_rc_file_name = jp(here, '.coverage_rc_' +  str(major_version))
    with open(cov_rc_file_name, 'w') as cov_rc_file:
        cov_rc_file.write(engine.render(jp(here, "coverage_rc.tenjin"), dict(major_version=major_version)))

    rc = pytest.main(['--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing', '--cov-config=' + cov_rc_file_name] + (args if args == ['-v'] else []))

    # print("Validating demo for all envs")
    # try:
    #     del os.environ['PYTHONPATH']
    # except KeyError:
    #     pass
    # for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
    #     print()
    #     osenv = {'PYTHONPATH': ':'.join(sys.path)}
    #     rc |= subprocess.call((sys.executable, here + '/../demo/demo.py', '--env', env_name), env=osenv)

    return rc
import sys, os, subprocess
from os.path import join as jp

import pytest

import tenjin
from tenjin.helpers import *


_here = os.path.abspath(os.path.dirname(__file__))


def main(args):
    print("Running tests, args:", args)
    if args and args != ['-v']:
        return pytest.main(['--capture=sys'] + args)

    engine = tenjin.Engine(cache=False)
    major_version = sys.version_info[0]
    minor_version = sys.version_info[1]
    # Note: This naming is duplicated in .travis.yml
    cov_rc_file_name = jp(_here, '.coverage_rc_' +  str(os.environ.get('TRAVIS_PYTHON_VERSION', str(major_version) + '.' + str(minor_version))))
    with open(cov_rc_file_name, 'w') as cov_rc_file:
        cov_rc_file.write(engine.render(jp(_here, "coverage_rc.tenjin"), dict(major_version=major_version, minor_version=minor_version)))

    pytest_args = ['--capture=sys', '--cov=' + _here + '/..', '--cov-report=term-missing', '--cov-config=' + cov_rc_file_name] + (args if args == ['-v'] else [])
    print('Running: pytest.main(' + ' '.join(pytest_args) + ')')
    rc = pytest.main(pytest_args)

    print()
    try:
        del os.environ['PYTHONPATH']
    except KeyError:
        pass
    for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
        demo_out = jp(_here, env_name + '.demo_out')
        print("Validating demo for env {env} - output in {out}".format(env=env_name, out=demo_out))
        osenv = {'PYTHONPATH': ':'.join(sys.path)}
        with open(demo_out, 'w') as outf:
            rc |= subprocess.check_call((sys.executable, _here + '/../demo/demo.py', '--env', env_name), env=osenv, stdout=outf)
    print()

    return rc

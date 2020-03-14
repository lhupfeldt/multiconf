import sys
import os
from os.path import join as jp
import subprocess

import nox


_HERE = os.path.abspath(os.path.dirname(__file__))
_TEST_DIR = jp(_HERE, 'test')
_PY_VERSIONS = os.environ.get("TRAVIS_PYTHON_VERSION") or ['3.6', '3.7', '3.8', 'pypy3']


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def test(session):
    session.install('.')
    session.install('-r', jp(_TEST_DIR, 'requirements.txt'))
    cov_rc_file_name = '.coverage_rc_' +  session.python  # The rcfile path is duplicated in .travis.yml
    session.run('python', jp(_TEST_DIR, 'utils/mk_coveragerc.py'), cov_rc_file_name)
    session.run('pytest', '--capture=sys', '--cov=' + _HERE, '--cov-report=term-missing', '--cov-config=' + jp(_TEST_DIR, cov_rc_file_name), *session.posargs)


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def demo(session):
    try:
        del os.environ['PYTHONPATH']
    except KeyError:
        pass

    for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
        demo_out = jp(_TEST_DIR, env_name + '.demo_out')
        print("Validating demo for env {env} - output in {out}".format(env=env_name, out=demo_out))
        osenv = {'PYTHONPATH': ':'.join(sys.path)}
        with open(demo_out, 'w') as outf:
            subprocess.check_call((sys.executable, jp(_HERE, 'demo/demo.py'), '--env', env_name), env=osenv, stdout=outf)

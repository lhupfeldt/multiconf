import sys
import os
from os.path import join as jp
import subprocess

import nox


_HERE = os.path.abspath(os.path.dirname(__file__))
_TEST_DIR = jp(_HERE, 'test')
_DOC_DIR = jp(_HERE, 'doc')
_TRAVIS_PYTHON_VERSION = os.environ.get("TRAVIS_PYTHON_VERSION")
_PY_VERSIONS = ['3.9', '3.8', '3.7', '3.6', 'pypy3'] if not _TRAVIS_PYTHON_VERSION else [_TRAVIS_PYTHON_VERSION]


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def test(session):
    session.install('.')
    session.install('-r', jp(_TEST_DIR, 'requirements.txt'))
    cov_rc_file_name = '.coverage_rc_' +  session.python  # The rcfile path is duplicated in .travis.yml
    session.run('python', jp(_TEST_DIR, 'utils/mk_coveragerc.py'), cov_rc_file_name)
    session.run('pytest', '--capture=sys', '--cov=' + _HERE, '--cov-report=term-missing', '--cov-config=' + jp(_TEST_DIR, cov_rc_file_name), *session.posargs)


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def demo(session):
    session.install('-e', '.')
    for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
        demo_out = jp(_TEST_DIR, env_name + '.demo_out')
        print("Validating demo for env {env} - output in {out}".format(env=env_name, out=demo_out))
        with open(demo_out, 'w') as outf:
            session.run('python', jp(_HERE, 'demo/demo.py'), '--env', env_name, stdout=outf)


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def doc(session):
    session.install('-r', jp(_DOC_DIR, 'requirements.txt'))
    session.run('make', '-C', 'doc', 'html')

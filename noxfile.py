"""nox https://nox.thea.codes/en/stable/ configuration"""

# Use nox >= 2023.4.22

import os
import glob
from pathlib import Path
import platform

import nox


_HERE = Path(__file__).absolute().parent
_TEST_DIR = _HERE/"test"
_DOC_DIR = _HERE/'doc'
# Locally we have nox handle the different versions, but in each travis run there is only a single python which can always be found as just 'python'
_PY_VERSIONS = ["3.12", "3.11", "3.10", "3.9"] if not os.environ.get("TRAVIS_PYTHON_VERSION") else ['python']
# "pypy3.10" and "pypy3.9" currently failing with thread issues.


nox.options.error_on_missing_interpreters = True


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def typecheck(session):
    session.install("-e", ".", "mypy>=1.5.1")
    session.run("mypy", str(_HERE/"src"))


# TODO: pylint-pytest does not support 3.12
@nox.session(python="3.11", reuse_venv=True)
def pylint(session):
    session.install(".", "pylint>=3.3.1", "pylint-pytest>=1.1.8")

    print("\nPylint src)")
    disable_checks = "missing-module-docstring,missing-class-docstring,missing-function-docstring,protected-access,invalid-name,consider-using-f-string"
    disable_checks += ",too-many-branches,too-many-locals,too-many-arguments,attribute-defined-outside-init,no-member"
    session.run("pylint", "--fail-under", "9.4", "--disable", disable_checks, str(_HERE/"src"))

    print("\nPylint test sources")
    disable_checks += ",multiple-imports,duplicate-code"
    session.run("pylint", "--fail-under", "9.2", "--variable-rgx", r"[a-z_][a-z0-9_]{1,30}$", "--disable", disable_checks, str(_HERE/"test"))


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def unit(session):
    session.install(".", "pytest>=7.4.1", "coverage>=7.3.1", "pytest-cov>=4.1.0", "tenjin~=1.1")
    fail_under = 100 if platform.python_implementation() == 'CPython' else 99
    session.run(
        "pytest",
        "--capture=sys", "--cov", "--cov-report=term-missing", f"--cov-fail-under={fail_under}",
        f"--cov-config={_TEST_DIR/'.coveragerc'}",
        *session.posargs)


@nox.session(python=_PY_VERSIONS, reuse_venv=True)
def demo(session):
    session.install(".")
    for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
        demo_out = _TEST_DIR/(env_name + '.demo_out')
        print("Validating demo for env {env} - output in {out}".format(env=env_name, out=demo_out))
        with open(demo_out, 'w') as outf:
            session.run('python', str(_HERE/"demo/demo.py"), '--env', env_name, stdout=outf)


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def doc(session):
    session.install(".", "sphinx>=2.2")
    session.run('make', '-C', _DOC_DIR, 'html')


@nox.session(python=_PY_VERSIONS[0], reuse_venv=True)
def build(session):
    session.install("build>=1.0.3", "twine>=4.0.2")
    for ff in glob.glob("dist/*"):
        os.remove(ff)
    session.run("python", "-m", "build")
    session.run("python", "-m", "twine", "check", "dist/*")

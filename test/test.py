#!/usr/bin/python

from __future__ import print_function

import sys, os, subprocess

here = os.path.abspath(os.path.dirname(__file__))
os.environ['MULTICONF_WARN_JSON_NESTING'] = 'true'

print("Running tests")
if len(sys.argv) > 1:
    sys.exit(subprocess.call(['python2', '-m', 'pytest', '--capture=sys'] + sys.argv[1:]))
else:
    rc = subprocess.call(('python2', '-m', 'pytest', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing'))
#rc = subprocess.call(('nosetests', '--with-coverage', '--cover-branches', '--cover-package=multiconf'))

print("Validating demo for all envs")
for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
    print()
    rc |= subprocess.call(('python2', here + '/../demo/demo.py', '--env', env_name))

sys.exit(rc)

#!/usr/bin/python

import sys, os, subprocess

here = os.path.abspath(os.path.dirname(__file__))

os.chdir(here)

print "Running tests"
if len(sys.argv) > 1:
    sys.exit(subprocess.call(['py.test', '--capture=sys'] + sys.argv[1:]))
else:
    rc = subprocess.call(('py.test', '--capture=sys', '--cov=' + here + '/..', '--cov-report=term-missing'))
#rc = subprocess.call(('nosetests', '--with-coverage', '--cover-branches', '--cover-package=multiconf'))

print "Validating demo for all envs"
for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
    print ""
    rc |= subprocess.call((here + '/../demo/demo.py', '--env', env_name))

sys.exit(rc)

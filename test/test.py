#!/usr/bin/python

import sys, subprocess
import os.path

print "Running tests"
rc = subprocess.call(('nosetests', '--with-coverage', '--cover-branches', '--cover-package=multiconf'))

print "Validating demo for all envs"
here = os.path.abspath(os.path.dirname(__file__))
for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
    print ""
    rc |= subprocess.call((here + '/../demo/demo.py', '--env', env_name))

sys.exit(rc)

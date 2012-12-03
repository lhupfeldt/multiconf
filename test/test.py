#!/usr/bin/python

import sys, subprocess

print "Validating demo"
rc = 0
for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
    rc |= subprocess.call(('../demo/demo.py', '--env', env_name))

rc |= subprocess.call(('nosetests'))

sys.exit(rc)

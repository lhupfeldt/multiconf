#!/usr/bin/python

import subprocess

print "Validating demo"
for env_name in 'prod', 'preprod', 'devlocal', 'devs', 'devi':
    subprocess.call(('../demo/demo.py', '--env', env_name))

subprocess.call(('nosetests'))


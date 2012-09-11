#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

#
# Small demo of a partial weblogic domain configuration
#
# Please look into config.py in this folder to see how sample Weblogic
# environment is configured using Multiconf
#

import argparse
import config

def generate(env):
    print '---- Loading Config: ' + repr(env) + ' -----'
    c = config.conf(env)
    print '---- Loaded Config, printing full config: -----'
    print c.json(compact=True)

    # In real life the loaded config could be used to do template substitution in a weblogic config.xml.template
    # Now we just print some env specific values
    print '---- Use config: -----'
    print 'c.admin_server:', repr(c.admin_server)
    print 'c.managed_servers:', repr(c.managed_servers)
    print 'c.datasources:', repr(c.datasources)

    print


def main():
    parser = argparse.ArgumentParser(description="Demo of mini pseudo weblogic config for multiple envs")
    parser.add_argument('--env', required=True, help="The environment for which to load the config")
    args = parser.parse_args()

    generate(args.env)


if __name__ == '__main__':
    main()

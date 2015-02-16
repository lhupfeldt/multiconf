#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

#
# Small demo of a partial weblogic domain configuration
#
# Please look into config.py in this folder to see how sample Weblogic
# environment is configured using Multiconf
#

from __future__ import print_function

import argparse
import config


def generate(env):
    print('---- Instantiating config for env: ' + repr(env) + ' -----')
    c = config.conf(env)

    print('\n---- Printing entire config as "compact" json: -----')
    # json will dump property method values as well as multiconf property values
    # compact give a more human readable output
    print(c.json(compact=True))

    # In real life the loaded config could be used to do template substitution in a weblogic config.xml.template
    # Now we just print some env specific values
    print('\n---- Access config objects/properties: -----')
    print('c.admin_server:', c.admin_server.json(compact=True))
    # Repeatable objects are inserted in an ordered dict
    print('c.managed_servers["ms1"]:', c.managed_servers['ms1'].json())
    print('ms1.port:', c.managed_servers['ms1'].port)
    print('c.datasources:', c.datasources)
    print()


def main():
    parser = argparse.ArgumentParser(description="Demo of mini pseudo weblogic config for multiple envs")
    parser.add_argument('--env', required=True, help="The environment for which to load the config")
    args = parser.parse_args()

    generate(args.env)


if __name__ == '__main__':
    main()

#!/usr/bin/python

# Small demo of a partial weblogic domain configuration

import argparse
import config
import multiconf

def generate(env):
    print '---- Loading Config: ' + repr(env) + ' -----'
    c = config.conf(env)
    # In real life the loaded config could be used to do template substitution in a weblogic config.xml.template
    # Now we just print some env specific values
    print 'c.ms_suffixes:', repr(c.ms_suffixes)
    print 'c.admin_server:', repr(c.admin_server)
    print 'c.managed_servers:', repr(c.managed_servers)
    print 'c.datasources:', repr(c.datasources)
    print '---- Loaded: ' + repr(c.selected_env) + ' -----'
    print


def main():
    parser = argparse.ArgumentParser("Demo of mini weblogic config for multiple envs")
    parser.add_argument('--env', required=True, help="The environment for which to load the config")
    args = parser.parse_args()
    
    generate(multiconf.Env(args.env))


if __name__ == '__main__':
    main()

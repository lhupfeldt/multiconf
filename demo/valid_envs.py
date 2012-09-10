# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.envs import Env, EnvGroup

# Define environments
#
# Just instantiate object Env with environment name
#
devLocal = Env('devLocal')
devi = Env('devi')
devs = Env('devs')
preprod = Env('preprod')
prod = Env('prod')

# Define group of environments
g_prod = EnvGroup('g_prod', preprod, prod)
g_dev = EnvGroup('g_dev', devi, devs)

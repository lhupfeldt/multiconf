# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.envs import EnvFactory

# Define environments
#
# Just instantiate object Env with environment name
#

ef = EnvFactory()

devLocal = ef.Env('devLocal')
devi = ef.Env('devi')
devs = ef.Env('devs')
preprod = ef.Env('preprod')
prod = ef.Env('prod')

# Define group of environments
g_prod = ef.EnvGroup('g_prod', preprod, prod)
g_dev = ef.EnvGroup('g_dev', devi, devs)

from envs import Env, EnvGroup

preprod = Env('preprod')
prod = Env('prod')
g_prod = EnvGroup('g_prod', preprod, prod)

devLocal = Env('devLocal')

devi = Env('devi')
devs = Env('devs')
g_dev = EnvGroup('g_dev', devi, devs)

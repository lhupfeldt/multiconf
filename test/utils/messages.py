# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

"""Define error message patterns"""

already_printed_msg = "\nCheck already printed error messages."

exception_previous_object_expected_stderr = """Exception validating previously defined object -
  type: <class 'multiconf.test.%(module)s.%(py3_local)sinner'>
Stack trace will be misleading!
This happens if there is an error (e.g. attributes with value MC_REQUIRED or missing '@required' ConfigItems ) in
an object that was not directly enclosed in a with statement. Objects that are not arguments to a with
statement will not be validated until the next ConfigItem is declared or an outer with statement is exited.
"""

mc_required_current_env_expected = """Attribute: '{attr}' MC_REQUIRED did not receive a value for current env {env}"""
mc_required_other_env_expected = """Attribute: '{attr}' MC_REQUIRED did not receive a value for env {env}"""

mc_todo_current_env_expected = """Attribute: '{attr}' MC_TODO did not receive a value for current env {env}"""
mc_todo_other_env_expected = """Attribute: '{attr}' MC_TODO did not receive a value for env {env}"""

no_value_current_env_expected = """Attribute: '{attr}' did not receive a value for current env {env}"""
no_value_other_env_expected = """Attribute: '{attr}' did not receive a value for env {env}"""

config_error_mc_required_current_env_expected = "^ConfigError: " + mc_required_current_env_expected
config_error_mc_required_other_env_expected = "^ConfigError: " + mc_required_other_env_expected

config_error_mc_todo_current_env_expected = "^ConfigError: " + mc_todo_current_env_expected
config_error_mc_todo_other_env_expected = "^ConfigError: " + mc_todo_other_env_expected

config_error_no_value_current_env_expected = "^ConfigError: " + no_value_current_env_expected
config_error_no_value_other_env_expected = "^ConfigError: " + no_value_other_env_expected

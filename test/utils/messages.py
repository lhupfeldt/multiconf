# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

"""Define error message patterns"""

already_printed_msg = "\nCheck already printed error messages."

exception_previous_object_expected_stderr = """Exception validating previously defined object -
  type: <class 'test.%(module)s.%(py3_local)sinner'>
Stack trace will be misleading!
This happens if there is an error (e.g. attributes with value MC_REQUIRED or missing '@required' ConfigItems ) in
an object that was not directly enclosed in a with statement. Objects that are not arguments to a with
statement will not be validated until the next ConfigItem is declared or an outer with statement is exited.
"""

config_error_never_received_value_expected = """^ConfigError: The following attribues defined earlier never received a proper value for {env}:"""

no_value_expected = """Attribute: '{attr}' did not receive a value for env {env}"""
config_error_no_value_expected = "^ConfigError: " + no_value_expected

mc_required_expected = """Attribute: '{attr}' MC_REQUIRED did not receive a value for env {env}"""
config_error_mc_required_expected = "^ConfigError: " + mc_required_expected

mc_todo_current_env_expected = """Attribute: '{attr}' MC_TODO did not receive a value for env {env}"""
config_error_mc_todo_current_env_expected = "^ConfigError: " + mc_todo_current_env_expected
config_warning_mc_todo_current_env_expected = "^ConfigWarning: " + mc_todo_current_env_expected

mc_todo_other_env_expected = """Attribute: '{attr}' MC_TODO did not receive a value for env {env}"""
config_error_mc_todo_other_env_expected = "^ConfigError: " + mc_todo_other_env_expected
config_warning_mc_todo_other_env_expected = "^ConfigWarning: " + mc_todo_other_env_expected

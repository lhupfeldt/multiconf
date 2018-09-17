# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

"""Define error message patterns"""

already_printed_msg = "\nCheck already printed error messages."

exception_previous_object_expected_stderr = """Exception validating previously defined object -
  type: <class 'test.%(module)s.%(local_func)sinner'>
Stack trace will be misleading!
This happens if there is an error (e.g. attributes with value MC_REQUIRED or missing '@required' ConfigItems) in
an object that was not directly enclosed in a with statement. Objects that are not arguments to a with
statement will not be validated until the next ConfigItem is declared or an outer with statement is exited.
"""

not_repeatable_in_parent_msg = "'{repeatable_cls_key}': {repeatable_cls} is defined as repeatable, but this is not defined as a repeatable item in the containing class: '{ci_named_as}': {ci_cls}"

config_error_never_received_value_expected = """^ConfigError: The following attribues defined earlier never received a proper value for {env}:"""

setattr_not_defined_in_init_expected = """All attributes must be defined in __init__ or set with 'mc_set_unknown'. Attempting to set attribute '{}' which does not exist."""

no_value_expected = """Attribute: '{attr}' did not receive a value for env {env}"""
config_error_no_value_expected = "^ConfigError: " + no_value_expected

mc_required_expected = """Attribute: '{attr}' MC_REQUIRED did not receive a value for env {env}"""
config_error_mc_required_expected = "^ConfigError: " + mc_required_expected

mc_todo_expected = """Attribute: '{attr}' MC_TODO did not receive a value for env {env}{allowed}"""
config_error_mc_todo_expected = "^ConfigError: " + mc_todo_expected
config_warning_mc_todo_expected = "^ConfigWarning: " + mc_todo_expected

"""
Provides basic funtions for LedgerTools.

See README.md for details.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2020-07-24
"""

import sublime
import os.path


def get_settings():

    # LedgerTools settings filename
    settings_filename = "LedgerTools.sublime-settings"

    # Load settings
    return sublime.load_settings(settings_filename)


def is_ledger_file(view):

    valid_ledger_file_ext = get_settings().get('valid_ledger_file_ext')

    filename = view.file_name()

    if filename is None:
        return False

    else:
        _, ext = os.path.splitext(filename)
        return ext in valid_ledger_file_ext


def get_definition_filename():
    """Checks if the definition filename specified in settings is valid.

    Returns
    -------
    bool
        True if the file name is valid, else False.
    """
    definition_filename = get_settings().get('definition_filename')

    # Checks that a filename is given
    if definition_filename == "":
        sublime.error_message("No ledger definition filename in settings.")
        return False

    # Check if filename exists
    if not os.path.exists(definition_filename):
        sublime.error_message("Ledger definition filename does not exists.")
        return False

    return definition_filename

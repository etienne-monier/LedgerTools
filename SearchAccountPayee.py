"""
Provides ledger account and payee insersion commands.

See README.md for details.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2020-07-24
"""

import sublime_plugin
import re

from . import utils


def get_info(filename, search_key):
    """Gets info from ledger file.

    Arguments
    ---------
    filename: str
        The ledger filename.
    search_key: str
        The key to search for.

    Returns
    -------
    list
        List of key entries.
    """
    with open(filename, encoding="utf-8") as file:
        content = file.read()

    result = re.findall(r'^{} (.+)$'.format(search_key), content, re.M)

    return list(map(str.strip, result))


class LedgerBaseSearchCommand(sublime_plugin.TextCommand):
    """Command to search a key in the definition file.

    """
    def run(self, edit, item=None, search_key='account'):

        # Get filename and check it.
        filename = utils.get_definition_filename()

        # Check it
        if not filename:
            return

        # Get account or payee
        items = get_info(filename, search_key)

        if item:
            # Insert item.

            # Get possible virtual flag
            pattern = utils.get_settings().get("virtual_regex")

            # Add brackets if virtual.
            if pattern != "" and re.search(pattern, item):
                item = '[' + item + ']'

            # Insert item.
            self.view.run_command("insert", {"characters": item})

        else:
            # Go to catch item.
            self.view.window().show_quick_panel(
                items,
                lambda idx: self.pick(idx, edit, items, search_key))

    def pick(self, index, edit, items, search_key):
        if index >= 0:
            self.run(edit, items[index], search_key)

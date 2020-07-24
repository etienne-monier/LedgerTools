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
    search_key: str, list of str
        The key to search for or a list of keys.

    Returns
    -------
    list
        List of key entries.
    """
    if isinstance(search_key, str):
        search_key = [search_key]

    with open(filename) as file:
        lines = file.readlines()

    entries_list = []
    for line in lines:

        for key in search_key:
            m = re.search(r'^{} (.+)$'.format(key), line)

            if m:
                entries_list.append(m.group(1).strip())

    return entries_list


class LedgerBaseSearchCommand(sublime_plugin.TextCommand):
    """Command to search a key in the definition file.

    """
    def run(self, edit, item=None, search_key=['payee', 'account']):

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
            v_keyword = utils.get_settings().get("virtual_keyword")

            # Add brackets if virtual.
            if v_keyword != "" and v_keyword in item:
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

"""
Provide a command to auto-align amounts in ledger file.

See README.md for details.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2020-07-24
"""

import sublime
import sublime_plugin
import re
import threading

from . import utils


class LedgerAlignAmountsCommand(sublime_plugin.TextCommand):

    def run(self, edit):

        # if not utils.is_ledger_file(self.view):
        #     # Current view is not a ledger file.
        #     return

        dot_pos = utils.get_settings().get('dot_pos')

        # Get the whole document as a region.
        region = sublime.Region(0, self.view.size())

        # Get a list of all lines
        lines = self.view.lines(region)

        # Set match pattern.
        p = re.compile(
            r'^\s+([\[\]\w:\s_-]+)\s+([-$£¥€¢\d,_]+)(.?[\d]*.*)$')

        for line in reversed(lines):

            # Get line content
            line_content = self.view.substr(line)

            # Catch amount
            res = p.search(line_content)

            # If the line has an amount, correct it.
            if res:

                # Get the position of the dot in the line.
                line_pos_dot = line_content.find(res.group(2)) + \
                    len(res.group(2))
                # Get number of spaces to add or to remove
                # If >=0, spaces should be added
                # If <0, spaces should be removed
                num = dot_pos - line_pos_dot

                # Get position of the beggining of ammount in the line
                line_pos_amount = line_content.find(res.group(2))
                # Same in the view
                view_pos_amount = line.begin() + line_pos_amount

                if num > 0:
                    self.view.insert(edit, view_pos_amount, ' '*num)
                elif num < 0:
                    self.view.erase(
                        edit,
                        sublime.Region(view_pos_amount+num, view_pos_amount))


class alignOnModified(sublime_plugin.EventListener):

    # align thread
    thread = None
    # listen actions
    registered_actions = ["insert", "left_delete", "right_delete",
                          "delete_word", "paste", "cut"]

    def on_modified(self, view):

        # If not a ledger file
        if not utils.is_ledger_file(view):
            return

        if not utils.get_settings().get('automatic_amount_alignment'):
            return

        # Do not process scratch or widget files
        if view.is_scratch() or view.settings().get('is_widget'):
            return

        # Get the last executed command
        cmdhist = view.command_history(0)
        # If that' not a command to listen, return.
        if cmdhist[0] not in self.registered_actions:
            return

        # Default delay
        delay = 0.2

        # if cmdhist[0] == "insert" and cmdhist[1]['characters'].strip() == "":
        #     delay = 1

        # We need to define a timer to add delay.
        if self.thread:
            self.thread.cancel()

        self.thread = threading.Timer(
            delay,
            lambda: view.run_command('ledger_align_amounts')
        )
        self.thread.start()

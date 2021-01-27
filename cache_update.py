"""
Provides support for definition file analysis.

See README.md for details.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2021-01-27
"""

import sublime_plugin

import os.path

from . import utils


def cache_update():
    """Parses the definition file to get relevant information.
    """
    print('Updated cache.')


class DefinitionFileAnalysisOnSave(sublime_plugin.EventListener):
    """ This view event listener watches for definition file saving to
    update the cache.
    """

    def on_post_save(self, view):

        # If not a ledger file, exit.
        if not utils.is_ledger_file(view):
            return

        # If the the definition file is not defined, exit.
        location = utils.get_definition_filename()
        if not location:
            return

        # If the saved file is not the definition file, exit.
        if not os.path.samefile(location, view.file_name()):
            return

        cache_update()

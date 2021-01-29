"""
Provides support for definition file analysis.

See README.md for details.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2021-01-27
"""

import sublime_plugin

import os.path
import time
import re

from . import utils


def is_numeric(x):
    """Returns True is x is a number.
    """
    return isinstance(x, int) or isinstance(x, float)


def is_string(x):
    """Returns True is x is a string.
    """
    return isinstance(x, str)


def homogeneous_type(seq):
    """Checks if all elements of a list are the same.
    If that's the case, it returns the common type, else False.
    """
    first_type = type(seq[0])
    return first_type if all([type(x) is first_type for x in seq]) else False


class Amount():
    """Defines an amount with a currency.

    Attributes
    ----------
    number: int or float
        The amount
    currency: str
        The currency
    type: int
        The currency type.
        0 for symbol (e.g. €),
        1 for name (e.g. EUR),
        2 for long name (e.g. "A long name").
    """

    def __init__(self, number, currency):
        """Amount constructor

        Arguments
        ---------
        number: int or float
            The amount
        currency: str
            The currency
        """
        if not is_numeric(number):
            raise ValueError('The amount number is not numeric.')
        if not is_string(currency):
            raise ValueError('The amount currency is not a string.')

        self.number = number
        self.currency = currency

        # Determine the currency type.
        # 0 for symbol (e.g. €)
        # 1 for name (e.g. EUR)
        # 2 for long name (e.g. "A long name")
        if currency in ['$', '£', '¥', '€', '¢']:
            self.type = 0
        elif '"' in currency:
            self.type = 2
        else:
            self.type = 1

    def __add__(self, other):

        if isinstance(other, Amount):

            # Check if the two currencies are the same
            if self.currency != other.currency:
                raise Exception('Two amounts can be added only if the '
                                'currencies are the same.')

            return Amount(self.number + other.number, self.currency)

        else:
            # Invalid type
            raise ValueError(
                'Addind an amount with type {} is incorect.'.format(
                    type(other)))

    def __sub__(self, other):

        if isinstance(other, Amount):

            # Check if the two currencies are the same
            if self.currency != other.currency:
                raise Exception('Two amounts can be substracted only if the '
                                'currencies are the same.')

            return Amount(self.number - other.number, self.currency)

        else:
            # Invalid type
            raise ValueError(
                'Substracting an amount with type {} is incorect.'.format(
                    type(other)))

    def __mul__(self, other):

        if is_numeric(other):
            # A number * an amount
            return Amount(self.number * other, self.currency)

        else:
            # Invalid type
            raise ValueError(
                'Multiplying an amount with type {} is incorect.'.format(
                    type(other)))

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __str__(self):
        if self.type == 0:
            return self.currency + str(self.number)
        else:
            return str(self.number) + ' ' + self.currency

    def __repr__(self):
        return 'Amount(number={}, currency={})'.format(
            self.number, self.currency)


class AutomaticTransaction():

    def __init__(self, regex, postings):
        """
        Arguments
        ---------
        regex: str
            The regular expression to match.
        postings: list of tuple
            The operations to apply when the regular expression is met.
            Each element of the list is a 2-length tuple whose first
            element is the account str and whose second element is an
            amount object, a number or None.
        """
        self.regex = regex

        # This list contains the indexes of postings which do not have
        # an amount nor number.
        None_amount_index = [
            i for i, post in enumerate(postings) if post[1] is None]

        if len(None_amount_index) > 1:
            raise ValueError('More than one posting do not have an amount.')

        elif len(None_amount_index) == 0:
            # The postings can be save in state.
            self.postings = postings

        else:
            # The missing amount should be found.

            # The index of the missing amount posting.
            index = None_amount_index[0]

            # The list of available amounts
            amounts = [post[1] for post in postings if post[1] is not None]

            # Check all types are coherent
            if not homogeneous_type(amounts):
                raise ValueError('Postings have incoherent type.')

            else:
                if is_numeric(amounts[0]):
                    # The amounts are multipliers
                    if len(amounts) == 1:
                        postings[index][1] = 0-amounts[0]

                    else:
                        postings[index][1] = 0 - sum(amounts)
                else:
                    # The amount ARE amounts
                    currency = amounts[0].currency

                    if len(amounts) == 1:
                        postings[index][1] = Amount(0, currency) - amounts[0]

                    else:
                        print(amounts)
                        postings[index][1] = Amount(0, currency) - \
                            sum(amounts)

            self.postings = postings

    def __str__(self):
        string = 'An automatic transaction seeking for regex {}\n'.format(
            self.regex)

        for post in self.postings:
            string += '\t{}\t\t{}\n'.format(post[0], post[1])

        return string[:-1]

    def __repr__(self):
        return 'AutomaticTransaction(regex={}, postings={})'.format(
            self.regex, self.postings)


def get_automatic_transactions(filename):
    """Reads the file located at FILENAME to detect automatic transactions.
    It then returns a list of AutomaticTransaction objects.

    Arguments
    ---------
    filename: string
        The file location.

    Returns
    -------
    list of AutomaticTransaction
        The automatic transactions defined in the file.
    """
    start = time.time()

    # Read file content
    with open(filename) as file:
        content = file.read()

    # Pattern to catch automatic transactions.
    #
    # It catches the following groups:
    #     1. The account regex
    #     2. The postings lines
    pattern = r"""
        (?<=\n)=\ /([^/]+)/[ \t]*\n  # REGEX definition
        ((?:\ [ \t]*
            (?:[^;#\%\|\*\n\t ]|(?<! ) )+[^;#\%\|\*\n\t ]  # ACCOUNT
            (?:[ {2}\t][ \t]*                              # HARD SEP
                [$£¥€¢]?                                   # CURRENCY SYMB
                -?\d+(?:,\d{3})*(?:\.\d{1,2})?             # NUMBER
                (?:\ [A-Za-z]+)?                           # CURRENCY NAME
                (?:\ \"[^"]+\")?                           # CURRENCY NAME LONG
            )?
        [ \t]*\n)+)
    """

    # Pattern to catch automatic transactions.
    #
    # It catches the following groups:
    #     1. The account name
    #     2. The currency symbol
    #     3. The amount
    #     4. The currency name
    #     5. The long currency name
    posting_pattern = r"""
        ^\ [ \t]*
        ((?:[^;#\%\|\*\n\t ]|(?<! ) )+[^;#\%\|\*\n\t ])# ACCOUNT
        (?:[ {2}\t][ \t]*                              # HARD SEP
            ([$£¥€¢]?)                                 # CURRENCY SYMB
            (-?\d+(?:,\d{3})*(?:\.\d{1,2})?)           # NUMBER
            ((?:\ [A-Za-z]+)?)                         # CURRENCY NAME
            ((?:\ \"[^"]+\")?)                         # CURRENCY NAME LONG
        )?
        [ \t]*$
    """

    # Find all autom. transactions
    autom_trans = re.findall(pattern, content, re.VERBOSE)

    # Find all postings inside
    autom_trans_objects = []
    for trans in autom_trans:

        # postings_info is a list whose elements are tuple.
        #
        # Each tuple contains 5 elements: account, cur. symb., amount,
        # cur. name, cur. name long.
        postings_info = re.findall(
            posting_pattern, trans[1], re.VERBOSE | re.M)

        # For each element of postings_info, the only given currency
        # name should be kept.
        #
        # Each element of postings_info_proc is a list of length 3
        # like [account, Amount or numeric or None]
        postings_info_proc = []

        for post in postings_info:

            if post[2] == "":
                # No number nor amount was given
                post_number = None

            else:
                # A number or Amount was given
                number = eval(post[2])
                currency = (post[1] or post[3] or post[4]).strip()

                if currency == '':
                    # That was a multiplier
                    post_number = number
                else:
                    # That was an amount
                    post_number = Amount(number, currency)

            # Add the current posting to the autom. transaction list.
            postings_info_proc.append([post[0], post_number])

        autom_trans_objects.append(
            AutomaticTransaction(trans[0], postings_info_proc)
        )

    print('Execution time: {:.5f}'.format(time.time()-start))
    return autom_trans_objects


class AutomaticTransactionGutterUpdateOnSave(sublime_plugin.EventListener):
    """ This view event listener watches for ledger journal file saving to
    update the gutters that show hidden automatic transactions.
    """

    def on_post_save(self, view):

        # If not a ledger file, exit.
        if not utils.is_ledger_file(view):
            return

        # If the the definition file is not defined, exit.
        location = utils.get_definition_filename()
        if not location:
            return

        # If the saved file is the definition file, exit.
        if not os.path.samefile(location, view.file_name()):
            return

        # Get automatic transactions from definition file
        autom_trans_list = get_automatic_transactions(location)

        # Prints result
        for trans in autom_trans_list:
            print(trans)

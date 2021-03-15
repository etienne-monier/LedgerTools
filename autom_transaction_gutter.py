"""
Provides support for definition file analysis.

See README.md for details.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2021-01-27
"""

import sublime
import sublime_plugin

import re

from . import utils
from. import ledger_regex


# The gutter lines and text.
GUTTER_LINES = []
GUTTER_TEXT = []

# Inspired from SublimeLinter
TOOLTIP_STYLES = """
     body {
        word-wrap: break-word;
    }
    .error {
        color: var(--redish);
        font-weight: bold;
    }
    .warning {
        color: var(--yellowish);
        font-weight: bold;
    }
    .footer {
         margin-top: 0.5em;
        font-size: .92em;
        color: color(var(--background) blend(var(--foreground) 50%));
    }
    .action {
        text-decoration: none;
    }
    .icon {
        font-family: sans-serif;
        margin-top: 0.5em;
    }
"""

TOOLTIP_TEMPLATE = """
    <body id="sublimelinter-tooltip">
        <style>{stylesheet}</style>
        <div class="warning">Automatic Transaction</div>
        <div>
            <p>
                {content}
            </p>
        </div>
        <div class="footer"><a href="{href}">Click</a>
            <span>Go to Automatic Transaction definition
        </div>
    </body>
"""


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


def number_to_str(number):
    """Constructs a string based on a number.

    Arguments
    ---------
    number: int, float or Amount
        The number.
    """
    if isinstance(number, float):
        return "{:.2f}".format(number)
    return str(number)


def align_dot(account, number=None, dot_pos=58, html=False):
    r"""Constructs a string of the form '    account     10.52 EUR' where
    the dot is located at position dot_pos.

    Arguments
    ---------
    account: str
        The account name
    number: int, float or Amount
        The number.
    dot_pos: int
        The dot position in the line.
        Default: 58
    html: bool
        If this flag is True, all whitespaces are replaces by \u00A0 to
        keep multiple spaces in tooltip.
    """
    string = ' '*4 + account

    if number is None:
        output = string

    else:
        number_str = str(number)

        # Get the number of spaces to add or remove
        m = re.match(r'([-$£¥€¢\d,_]+)(?:.\d*)?.*', number_str)

        if not m:
            num_spaces = 0
        else:
            num_spaces = dot_pos - len(string) - len(m.group(1))

        # if num_spaces > 0, this means there is a lots of spaces to add.
        # Otherwise, it means the account is too long or the number of
        # digits before dot is too high. In this case, a hard separator
        # is required.
        if num_spaces > 0:
            output = string + ' ' * num_spaces + number_str
        else:
            output = string + '  ' + number_str

    if html:
        output = output.replace(' ', '\u00A0')

    return output


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
        """Function to add two amounts.

        Arguments
        ---------
        other: Amount
            The other amount.

        Returns
        -------
        Amount
            The sum of self and other.
        """
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
        """Function to substract two amounts.

        Arguments
        ---------
        other: Amount
            The other amount.

        Returns
        -------
        Amount
            The substraction of self by other.
        """
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
        """Function to multiply an amounts by a number.

        Arguments
        ---------
        other: float or int
            The multiplier.

        Returns
        -------
        Amount
            The multiplication of self by other.
        """
        if is_numeric(other):
            # A number * an amount
            return Amount(self.number * other, self.currency)

        else:
            # Invalid type
            raise ValueError(
                'Multiplying an amount with type {} is incorect.'.format(
                    type(other)))

    def __radd__(self, other):
        """This is the same as __add__, but is called when "a + self" is
        computed with "a" not being an Amount.

        If "a" does not support a.__add__(self) as adding Amount to "a"
        is not supported, then self.__radd(a) is called.

        This is important to compute sum([list of Amount]) as it calls
        (0 + Amount1) + Amount2 ...
        If 0 + Amount1 is not defined, it returns an error.
        """
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __rmul__(self, other):
        """Same as for __radd__.
        This aims at defining 5 * Amount.
        """
        if other == 1:
            return self
        else:
            return self.__mul__(other)

    def __str__(self):
        if self.type == 0:
            return self.currency + number_to_str(self.number)
        else:
            return number_to_str(self.number) + ' ' + self.currency

    def __repr__(self):
        return 'Amount(number={}, currency={})'.format(
            self.number, self.currency)


class Posting():
    """A posting is composed of an account and an amount or a coefficient.
    That's the basic element of a transaction.
    """

    def __init__(self, account, number=None):

        self.account = account
        self.number = number

    def is_empty(self):
        """Returns True is the posting number is empty.
        """
        return self.number is None

    def is_Amount(self):
        """Returns True is the posting number is an Amount object.
        """
        return isinstance(self.number, Amount)

    def update_number(self, number):
        """Updates the number to number.
        """
        self.number = number

    def __str__(self):
        return align_dot(self.account, self.number)

    def __repr__(self):
        return 'Posting(account={}, number={})'.format(
            self.account, self.number)


class Transaction():

    def __init__(self, postings):

        self.postings = self.fill_in_empty_amount(postings)

    def fill_in_empty_amount(self, postings_list):

        # This list contains the indexes of postings which do not have
        # an amount nor number.
        None_amount_index = [
            i for i, post in enumerate(postings_list) if post.is_empty()]

        if len(None_amount_index) > 1:
            raise ValueError('More than one posting do not have an amount.')

        elif len(None_amount_index) == 1:
            # The missing amount should be found.

            # The index of the missing amount posting.
            index = None_amount_index[0]

            # The list of available amounts
            amounts = [
                post.number for post in postings_list if not post.is_empty()]

            # Check all types are coherent
            if not homogeneous_type(amounts):
                raise ValueError('Postings have incoherent type.')

            else:
                if is_numeric(amounts[0]):
                    # The amounts are multipliers
                    if len(amounts) == 1:
                        result = 0-amounts[0]

                    else:
                        result = 0 - sum(amounts)
                else:
                    # The amount ARE amounts
                    currency = amounts[0].currency

                    if len(amounts) == 1:
                        result = Amount(0, currency) - amounts[0]

                    else:
                        result = Amount(0, currency) - \
                            sum(amounts)

                # Change the missing number.
                postings_list[index].update_number(result)

        return postings_list

    def __str__(self):

        string = ''
        for post in self.postings:
            string += str(post) + '\n'

        return string[:-1]


class UserTransaction(Transaction):
    """
    Attributes
    ----------
    date: str
        The transaction date.
    payee: str
        The payee.
    postings: list of tuple
        The transaction operations.
    postings_regions: optional, None or list of sublime.Region
        The regions associated to the postings in the current view.
    """

    def __init__(self, date, payee, postings, postings_regions=None):
        """
        Arguments
        ---------
        date: str
            The transaction date.
        payee: str
            The payee.
        postings: list of tuple
            The transaction operations.
        """
        Transaction.__init__(self, postings)
        self.date = date
        self.payee = payee
        self.postings_regions = postings_regions

    def __str__(self):
        string = 'User transaction on {} to {}\n'.format(
            self.date, self.payee)

        return string + Transaction.__str__(self)

    def __repr__(self):
        return 'UserTransaction(date={}, payee={}, postings={})'.format(
            self.date, self.payee, self.postings)


class AutomaticTransaction(Transaction):

    def __init__(self, regex, postings):
        """
        Arguments
        ---------
        regex: str
            The regular expression to match.
        postings: list of Posting
            The operations to apply when the regular expression is met.
        """
        Transaction.__init__(self, postings)
        self.regex = regex

    def catches_posting(self, posting):
        """Returns True is the posting is catched by the automatic
        transaction.
        """
        if re.search(self.regex, posting.account):
            return True
        else:
            return False

    def __str__(self):
        string = 'Automatic transaction /{}/\n'.format(
            self.regex)

        return string + Transaction.__str__(self)

    def __repr__(self):
        return 'AutomaticTransaction(regex={}, postings={})'.format(
            self.regex, self.postings)


def analyze_posting_line(content):
    """This analyses a string containing one or several postings.
    It returns a list of Posting.

    Arguments
    ---------
    content: str
        The string to analyze.

    Returns
    -------
    None, list of Posting
        None if no matching, else the extracted information.
    """

    # postings_info is a list whose elements are tuple.
    #
    # Each tuple contains 5 elements: account, cur. symb., amount,
    # cur. name, cur. name long.
    postings_info = re.findall(
        ledger_regex.posting_pattern, content, re.VERBOSE | re.M)

    # No result found
    if len(postings_info) == 0:
        return None

    # For each element of postings_info, only one currency info should
    # be kept: the currency symbol (€), name ('EUR') or long name
    # ("this is a long name"). Only one of them is accepted.
    #
    # Each element of postings_info_proc is a list of length 2
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
        postings_info_proc.append(Posting(post[0], post_number))

    return postings_info_proc


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
    # Read file content
    with open(filename, encoding="utf-8") as file:
        content = file.read()

    # Find all autom. transactions
    autom_trans = re.findall(ledger_regex.pattern_autom, content, re.VERBOSE)

    # Find all postings inside
    autom_trans_objects = []
    for trans in autom_trans:

        autom_trans_objects.append(
            AutomaticTransaction(
                trans[0],
                analyze_posting_line(trans[1])
            )
        )

    return autom_trans_objects


def get_user_transactions(view):
    """Finds the User transactions in current view.

    Arguments
    ---------
    view: sublime.View
        The current view.

    Returns
    -------
    list of UserTransaction
    """
    matched_transaction = view.find_all(ledger_regex.user_trans_pattern)

    list_of_user_transaction = []
    for match in matched_transaction:

        # Extract the different lines of the user transaction.
        lines = view.lines(match)

        # Extract the date and payee
        first_line_content = view.substr(lines[0])

        m = re.match(ledger_regex.trans_date_line, first_line_content, re.X)

        date, payee = m.group(1), m.group(2)

        # Search posting in other lines
        list_of_postings = []
        list_of_regions = []
        for line in lines[1:]:

            res = analyze_posting_line(view.substr(line))

            if res is not None:
                list_of_postings += res
                list_of_regions.append(line)

        list_of_user_transaction.append(
            UserTransaction(date, payee, list_of_postings, list_of_regions)
        )

    return list_of_user_transaction


def format_tooltip(postings_list, autom_trans_regex):
    """Formats a postings list into a html code for popups.

    Arguments
    ---------
    postings_list: list of Posting
        A list of tuple of the form (account, amount).
    autom_trans_regex: str
        The related automatic transaction regex. Used to link to
        definition file.

    Returns
    -------
    str
        html code.
    """
    content = ''
    for element in postings_list:
        content += '<li>{}</li>'.format(
            align_dot(element.account, element.number, html=True)
            )

    html = TOOLTIP_TEMPLATE.format(
        stylesheet=TOOLTIP_STYLES,
        content=content,
        href=autom_trans_regex
        )

    return html


def update_gutter_settings(view, autom_trans_list):
    """
    Arguments
    ---------
    view: sublime.View object
        The current view
    autom_trans_list: list of AutomaticTransaction
        The automatic transactions detected in the definition file.

    Returns
    -------
    """
    global GUTTER_LINES, GUTTER_TEXT

    # Re-initialize lines and text.
    GUTTER_LINES = []
    GUTTER_TEXT = []

    transaction_list = get_user_transactions(view)

    for transaction in transaction_list:

        for cnt, trans_posting in enumerate(transaction.postings):

            # For each posting in the file, one needs to check if an
            # automatic transaction matches.
            for autom_trans in autom_trans_list:

                if autom_trans.catches_posting(trans_posting):

                    # The list of postings to print
                    postings_to_print = []

                    # The current automatic transaction catches the
                    # current posting. One need to conpute the result.

                    for autom_post in autom_trans.postings:

                        if autom_post.is_Amount():
                            # One should only apply the amount to the account
                            post_number = autom_post.number
                        else:
                            # Should multiply with current amount
                            post_number = autom_post.number * \
                                trans_posting.number

                        # Add the info to the list
                        postings_to_print.append(
                            Posting(autom_post.account, post_number))

                    GUTTER_LINES.append(transaction.postings_regions[cnt])
                    GUTTER_TEXT.append(
                        format_tooltip(postings_to_print, autom_trans.regex)
                        )


class TooltipController(sublime_plugin.EventListener):

    def on_hover(self, view, point, hover_zone):

        if utils.is_ledger_file(view):
            if hover_zone == sublime.HOVER_GUTTER:

                line_region = view.line(point)

                intersect_test = [
                    region.intersects(line_region) for region in GUTTER_LINES]

                if any(intersect_test):

                    index = intersect_test.index(True)

                    def on_navigate(href):
                        """When called, il opens the definition file and
                        shows the automatic transaction associated with
                        the regex.
                        """
                        # Open definition file.
                        def_file_view = view.window().open_file(
                            utils.get_definition_filename()
                            )

                        # Catch the region to highlight
                        region = def_file_view.find(
                            '= /{}/'.format(href),
                            0,
                            sublime.LITERAL)

                        # Show region
                        def_file_view.show(region)
                        def_file_view.sel().clear()
                        def_file_view.sel().add(region)

                        # Hide popup
                        view.hide_popup()

                    view.show_popup(
                        content=GUTTER_TEXT[index],
                        flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                        location=point,
                        max_width=1000,
                        on_navigate=on_navigate
                    )


class AutomaticTransactionGutterUpdateOnSave(sublime_plugin.ViewEventListener):
    """ This view event listener watches for ledger journal file saving to
    update the gutters that show hidden automatic transactions.
    """

    def update_autom_trans_info(self):

        # If not a ledger file, exit.
        if not utils.is_ledger_file(self.view):
            return

        # If the the definition file is not defined, exit.
        location = utils.get_definition_filename()
        if not location:
            return

        # Get automatic transactions from definition file
        autom_trans_list = get_automatic_transactions(location)

        # Get the gutter positions in the current file
        update_gutter_settings(self.view, autom_trans_list)

        # Add gutters
        self.view.add_regions(
            "autom_tran", GUTTER_LINES,
            "markup.warning", "dot", sublime.HIDDEN)

    def on_post_save(self):
        self.update_autom_trans_info()

    def on_load(self):
        self.update_autom_trans_info()

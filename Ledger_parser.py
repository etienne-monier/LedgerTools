"""
Defines the Ledger grammar to be used when parsing a file. A tree
visitor is also defined to extract relevant information. Last, a
black-box simple function is provided.

See README.md for details.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2021-01-27
"""
# flake8: noqa: E501

import parsimonious.grammar
import parsimonious.nodes


# The grammar beggins with the basic parts of the language
grammar = r"""
    expr               = (comment / command / transaction / emptyline)*
"""

# Comments
grammar += r"""
    comment            = ~r"^"m comment_char ~r".*$"m
    comment_char       = ~r"(;|#|\%|\||\*)"
"""

# Commands begin with a keyword followed by a value
grammar += r"""
    command            = (account_def / payee_def / tag_def / currency_def / include_def)

    account_def        = ~r"^account"m ws+ account
    payee_def          = ~r"^payee"m ws+ payee
    tag_def            = ~r"^tag"m ws+ tag
    currency_def       = ~r"^commodity"m ws+ commodity
    include_def        = ~r"^include"m ws+ filename
"""

# Transaction
#
# Three kinds of transaction:
#  - user (normal),
#  - automatic (beggins with a "="),
#  - periodic (beggins with a "~")
grammar += r"""
    transaction        = user_transaction / autom_transaction / period_transaction

    user_transaction   = tran_header ("\n" (posting / (indent tran_note)))+
    autom_transaction  = ~r"^= /"m ap_tran_regex "/" stab* ("\n" posting)+
    period_transaction = ~r"^~ /"m ap_tran_regex "/" stab* ("\n" posting)+

    tran_header        = tran_date aux_date? stab+ state? payee (hard_sep tran_note)? stab*

    tran_note          = comment_char (tag_text / note_text)
    note_text          = ~r"[^\n:]*"
    tag_text           = stab* (metadata_tag / metadata_value)  stab*
    metadata_tag       = (":" tag)+ ":"
    metadata_value     = tag ":" stab+ ~r"[^\n]+"

    posting            = indent account (hard_sep amount)? (hard_sep tran_note)? stab*

    ap_tran_regex      = ~"[^\/]+"
    state              = ~r"([*!][ \t]+)?"
"""

# Amounts, curency and numbers
#
# Ledger admits three kinds of currency:
#  - €10
#  - 10 EUR
#  - 10 "a currency with spaces"
grammar += r"""
    amount             = (currency number) / (number " " currency_name) / (number " " currency_name_long) / number

    currency           = ~r"[$£¥€¢]"
    currency_name      = ~r"[A-Za-z]+"
    currency_name_long = ~r"\"[^\"]+\""

    number             = ~r"-?\d+(,\d{3})*(\.\d{1,2})?"
"""

# Dates
#
# Available dates for the moment:
#  DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD, YYYY-MM-DD
grammar += r"""
    tran_date          = ~"^"m date
    aux_date           = "=" date

    date               = en_date / (fr_date)
    en_date            = year date_sep month_day date_sep month_day
    fr_date            = month_day date_sep month_day date_sep year

    month_day          = ~r"\d{2}"
    year               = ~r"\d{4}"
    date_sep           = ~r"[/-]"
"""

# Command values (account, payee and co.) [^;#\%\|\*\n]+(?=( {2}|\t|$))
grammar += r"""
    account            = ~r"([^;#\%\|\*\n\t ]|(?<! ) )+[^;#\%\|\*\n\t ]"m
    payee              = account
    tag                = ~r"[A-Za-z0-9]+"
    commodity          = currency_name_long / currency_name / currency
    filename           = ~r"[\w\d _\\/\.\-\(\):]+"
"""

# Separators, white space and tabs
#
# Ledger defines two types of indentation:
#  - indent at the begining of the line
#  - hard separator between account and amount, for e.g.
grammar += r"""
    ws                 = ~"\s*"
    stab               = ~"[ \t]"
    indent             = ~"^ "m stab*
    hard_sep           = ~r"[ {2}\t]" stab*
    emptyline          = ws+
"""


def Ledger_parser(filename):
    """Reads a Ledger file located at FILENAME to extract relevant
    informations.

    Arguments
    ---------
    filename: str
        The location of the file to be read.

    Returns
    -------
    dict
        A dictionnary containing the extracted relevant information.
    """
    # Open file to be parsed.
    with open(filename) as file:
        content = file.read()

    # Construct grammar object
    Grammar = parsimonious.grammar.Grammar(grammar)
    # Parse content.
    tree = Grammar.parse(content)

    return tree

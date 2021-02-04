"""
Defines all patterns to find transactions and relevant information.

@author: Etienne Monier <etienne.monier@enseeiht.fr>
@license: CC-BY-NC-SA
@since: 2021-02-01
"""
# flake8: noqa: E501

# Pattern to catch automatic transactions.
#
# It catches the following groups:
#     1. The account regex
#     2. The postings lines
pattern_autom = r"""
    (?<=\n)=\ /([^/]+)/[ \t]*\n  # REGEX definition
    ((?:\ [ \t]*
        (?:[^;#\%\|\*\n\t ]|(?<!\ )\ )+[^;#\%\|\*\n\t ]  # ACCOUNT
        (?:[ {2}\t][ \t]*                              # HARD SEP
            [$£¥€¢]?                                   # CURRENCY SYMB
            -?\d+(?:,\d{3})*(?:\.\d{1,2})?             # NUMBER
            (?:\ [A-Za-z]+)?                           # CURRENCY NAME
            (?:\ \"[^"]+\")?                           # CURRENCY NAME LONG
        )?
    [ \t]*\n)+)
"""

# Pattern to catch posting information.
#
# It catches the following groups:
#     1. The account name
#     2. The currency symbol
#     3. The amount
#     4. The currency name
#     5. The long currency name
posting_pattern = r"""
    ^\ [ \t]*
    ((?:[^;#\%\|\*\n\t ]|(?<!\ )\ )+[^;#\%\|\*\n\t ])# ACCOUNT
    (?:[ {2}\t][ \t]*                              # HARD SEP
        ([$£¥€¢]?)                                 # CURRENCY SYMB
        (-?\d+(?:,\d{3})*(?:\.\d{1,2})?)           # NUMBER
        ((?:\ [A-Za-z]+)?)                         # CURRENCY NAME
        ((?:\ \"[^"]+\")?)                         # CURRENCY NAME LONG
    )?
    .*$
"""

# Pattern to catch a whole user transaction.
user_trans_pattern = r"^((?:\d{2}[/-]\d{2}[/-]\d{4})|(?:\d{4}[/-]\d{2}[/-]\d{2})).+\n([ \t]+.+\n)+"

# Pattern to catch the first line of a user transaction.
#
# It catches the following groups:
#     1. The date
#     2. The payee
trans_date_line = r"""
    ^
    ((?:\d{2}[/-]\d{2}[/-]\d{4}) | (?:\d{4}[/-]\d{2}[/-]\d{2}))     # DATE
    (?:=(?:\d{2}[/-]\d{2}[/-]\d{4}) | (?:\d{4}[/-]\d{2}[/-]\d{2}))? # AUX DATE
    [ \t]+                                                          # SEP
    (?:[!\*][ \t]+)?                                                 # STATE
    ((?:[^;#\%\|\*\n\t ]|(?<!\ )\ )+[^;#\%\|\*\n\t ])                # PAYEE
    .*$                                                 # Commentary and co.
"""

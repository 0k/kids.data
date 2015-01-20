# -*- coding: utf-8 -*-

import re

import kids.txt as txt

from .format import LogNumberFormatter, mk_fmt
from .lib import partition


## Python 3 compatibility layer
try:
    unicode = unicode
except NameError:  ## pragma: no cover
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:  ## pragma: no cover
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring


size = LogNumberFormatter(
    units=([u"B", u"KiB", u"MiB", u"GiB", u"TiB",
            "PiB", "EiB", "ZiB", "YiB"], 2**10)
    )


cond = lambda predicate, fmt_true, fmt_false: mk_fmt(
    lambda v, c: fmt_true(v, c) if predicate(v, c) else fmt_false(v, c)
    )(predicate=predicate, fmt_true=fmt_true, fmt_false=fmt_false)


fun_id = unicode


def remove_ansi(s):
    return re.sub(r'\x1b[^m]*m', '', s)


def remove_trailing_whitespaces(s):
    return "\n".join(re.sub(r' +$', '', l) for l in s.split("\n"))

##
## Format list of records
##

def records(elts, fields=None, group_by=[], order_by=[], indent="",
            field_fmts={}, head_field_fmts={}, type_fmts={},
            totals={}):
    """Display nicely a list of elts

    >>> elts = [{"foo": 1, "bar": 'x'},
    ...            {"foo": 23, "bar": 'abc'}]
    >>> print(records(elts, fields=['foo', 'bar']))
    1  x
    23 abc

    >>> print(records(elts, fields=['bar', ], group_by=['foo', ]))
    foo: 1
      x
    foo: 23
      abc
    >>> print(records(elts, fields=['foo', 'bar'], group_by=['foo', 'bar']))
    foo: 1
      bar: x
        1 x
    foo: 23
      bar: abc
        23 abc
    >>> print(records(elts, fields=['bar', 'foo', ], totals={'foo': sum}))
    x   1
    abc 23
    ------
        24

    # >>> elts = [{"foo": 1,  "bar": 'x'},
    # ...         {"foo": 23, "bar": 'abc'},
    # ...         {"foo": 7,  "bar": 'x'}]
    # >>> print(records(elts, fields=['foo', 'bar'],
    # ...       group_by=['bar', 'foo'],
    # ...       totals={'foo': sum}))
    # foo: 1
    #   bar: x
    #     1 x
    #     ---
    #     1
    # foo: 23
    #   bar: abc
    #     23 abc
    #     ------
    #     23
    #   --------
    #     23
        
    """
    if fields is None and len(elts) > 0:
        fields = elts[0].keys()

    if len(group_by) > 0:
        parted = partition(elts, lambda r: r[group_by[0]])
        label = head_field_fmts.get("__label__", fun_id)(group_by[0])
        value_fmt = head_field_fmts.get(group_by[0], field_fmts.get(group_by[0], fun_id))
        head_value_fmt = lambda x: head_field_fmts.get("__value__", fun_id)(value_fmt(x))
        return "\n".join("%s%s: %s\n%s"
                  % (indent, label, head_value_fmt(value),
                     records(
                         subelts, fields, group_by=group_by[1:],
                         order_by=order_by, indent=indent + "  ",
                         field_fmts=field_fmts, type_fmts=type_fmts,
                         totals=totals))
                  for value, subelts in parted.items())

    ## get max length:
    fmt_field = lambda f, v: "" if v is False else \
                field_fmts.get(f, type_fmts.get(type(v), fun_id))(v)
    # import pdb ; pdb.set_trace()
    # max_lengths = dict((f, max(len(unicode(fmt_field(f, r[f]))) for r in elts)) for f in fields)
    max_lengths = dict((f, max(len(remove_ansi(fmt_field(f, r.get(f))))
                               for r in elts))
                       for f in fields)

    def fmt_sized_field(f, v):
        formatted = fmt_field(f, v)
        invisible_chars = len(formatted) - len(remove_ansi(formatted))
        return (u"%%-%ds" % (max_lengths[f] + invisible_chars)) % fmt_field(f, v)
    fmt_record_line = lambda r: " ".join(fmt_sized_field(f, r.get(f)) for f in fields)

    total = []
    if any(f in totals for f in fields):
        bar = "-" * (sum(max_lengths[f] for f in fields) + len(fields) - 1)
        record_total = dict((f, "" if f not in totals else
                             totals[f]([r[f] for r in elts]))
                            for f in fields)
        total = [bar, fmt_record_line(record_total)]
    return remove_trailing_whitespaces(
        ("%s" % indent) + \
        ("\n%s" % indent).join([fmt_record_line(r)
                                for r in elts] + total))


##
## Format a single record
##


def record(elt, fields, indent="", field_fmts={}, type_fmts={},
                   head_field_fmts={}):
    """Display nicely a elt in multiline fashion

    >>> elt = {"foo": 1, "bar": 'x', 'wiz': 'xxx'}
    >>> print(record(elt, fields=['foo', 'bar']))
    foo: 1
    bar: x

    """

    fmt_field = lambda f, v: field_fmts.get(f,
                                            type_fmts.get(type(v), fun_id))(v)
    if len(fields) == 1:
        return fmt_field(fields[0], elt[fields[0]])
    field_lines = []
    for f in fields:
        fieldname = head_field_fmts.get("__default__", fun_id)(f)
        value = fmt_field(f, elt[f])
        field_lines.append(
            "%s: %s" % (fieldname, value) if len(unicode(value).split("\n")) == 1 else
            "%s:\n%s" % (fieldname, txt.indent(value, indent + "  ")))

    return "\n".join(field_lines)

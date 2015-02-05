# -*- coding: utf-8 -*-

import re
import pprint

from kids.cache import cache


@cache
def mk_char_tokenizer(split_char, quote_char='\\'):
    r"""Returns a tokenizer for given char

    So:

        >>> tokenize = mk_char_tokenizer(".")

        >>> list(tokenize('foo.bar.wiz'))
        ['foo', 'bar', 'wiz']

    Contrary to traditional ``.split()`` method, this function has to
    deal with any type of data in the string. So it actually
    interprets the string. Characters with meaning are '.' and '\'.
    Both of these can be included in a token by quoting them with '\'.

    So dot of slashes can be contained in token:

        >>> print('\n'.join(tokenize(r'foo.dot<\.>.slash<\\>')))
        foo
        dot<.>
        slash<\>

    Notice that empty keys are also supported:

        >>> list(tokenize(r'foo..bar'))
        ['foo', '', 'bar']

    Given an empty string:

        >>> list(tokenize(r''))
        ['']

    And a None value:

        >>> list(tokenize(None))
        []


    """

    prepare = {
        'sc': re.escape(split_char),
        'qc': re.escape(quote_char),
    }

    remove_quotes = re.compile(r'%(qc)s(%(qc)s|%(sc)s)' % prepare)
    find_tokens = re.compile(r'((%(qc)s.|[^%(sc)s%(qc)s])*)' % prepare)

    def tokenize(s):
        """Returns an iterable through all subparts of string splitted by char

        """
        if s is None:
            raise StopIteration
        tokens = (remove_quotes.sub(r'\1', m.group(0))
                  for m in find_tokens.finditer(s))
        ## an empty string superfluous token is added after all non-empty token
        for token in tokens:
            if len(token) != 0:
                next(tokens)
            yield token

    return tokenize


def mget(dct, key, tokenize=mk_char_tokenizer(".")):
    r"""Allow to get values deep in recursive dict with doted keys

    Accessing leaf values is quite straightforward:

        >>> dct = {'a': {'x': 1, 'b': {'c': 2}}}
        >>> mget(dct, 'a.x')
        1
        >>> mget(dct, 'a.b.c')
        2

    But you can also get subdict if your key is not targeting a
    leaf value:

        >>> mget(dct, 'a.b')
        {'c': 2}

    As a special feature, list access is also supported by providing a
    (possibily signed) integer, it'll be interpreted as usual python
    sequence access using bracket notation:

        >>> mget({'a': {'x': [1, 5], 'b': {'c': 2}}}, 'a.x.-1')
        5
        >>> mget({'a': {'x': 1, 'b': [{'c': 2}]}}, 'a.b.0.c')
        2

    Keys that contains '.' can be accessed by escaping them:

        >>> dct = {'a': {'x': 1}, 'a.x': 3, 'a.y': 4}
        >>> mget(dct, 'a.x')
        1
        >>> mget(dct, r'a\.x')
        3
        >>> mget(dct, r'a.y')  ## doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        MissingKeyError: missing key 'y' in dict.
        >>> mget(dct, r'a\.y')
        4

    As a consequence, if your key contains a '\', you should also escape it:

        >>> dct = {r'a\x': 3, r'a\.x': 4, 'a.x': 5, 'a\\': {'x': 6}}
        >>> mget(dct, r'a\\x')
        3
        >>> mget(dct, r'a\\\.x')
        4
        >>> mget(dct, r'a\\.x')
        6
        >>> mget({'a\\': {'b': 1}}, r'a\\.b')
        1
        >>> mget({r'a.b\.c': 1}, r'a\.b\\\.c')
        1

    And even empty strings key are supported:

        >>> dct = {r'a': {'': {'y': 3}, 'y': 4}, 'b': {'': {'': 1}}, '': 2}
        >>> mget(dct, r'a..y')
        3
        >>> mget(dct, r'a.y')
        4
        >>> mget(dct, r'')
        2
        >>> mget(dct, r'b..')
        1

    It will complain if you are trying to get into a leaf:

        >>> mget({'a': 1}, 'a.y')   ## doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        NonDictLikeTypeError: can't query subvalue 'y' of a leaf...

    if the key is None, the whole dct should be sent back:

        >>> mget({'a': 1}, None)
        {'a': 1}

    """
    return aget(dct, tokenize(key))


class MissingKeyError(KeyError):
    """Raised when querying a dict-like structure on non-existing keys"""

    def __str__(self):
        if hasattr(self, "message"):
            return self.message  ## PY2
        else:
            return self.args[0]


class NonDictLikeTypeError(TypeError):
    """Raised when attempting to traverse non-dict like structure"""


class IndexNotIntegerError(ValueError):
    """Raised when attempting to traverse sequence without using an integer"""


class IndexOutOfRange(IndexError):
    """Raised when attempting to traverse sequence without using an integer"""


def aget(dct, key):
    r"""Allow to get values deep in a dict with iterable keys

    Accessing leaf values is quite straightforward:

        >>> dct = {'a': {'x': 1, 'b': {'c': 2}}}
        >>> aget(dct, ('a', 'x'))
        1
        >>> aget(dct, ('a', 'b', 'c'))
        2

    If key is empty, it returns unchanged the ``dct`` value.

        >>> aget({'x': 1}, ())
        {'x': 1}

    """
    key = iter(key)
    try:
        head = next(key)
    except StopIteration:
        return dct

    if isinstance(dct, list):
        try:
            idx = int(head)
        except ValueError:
            raise IndexNotIntegerError(
                "non-integer index %r provided on a list."
                % head)
        try:
            value = dct[idx]
        except IndexError:
            raise IndexOutOfRange(
                "index %d is out of range (%d elements in list)."
                % (idx, len(dct)))
    else:
        try:
            value = dct[head]
        except KeyError:
            ## Replace with a more informative KeyError
            raise MissingKeyError(
                "missing key %r in dict."
                % (head, ))
        except:
            raise NonDictLikeTypeError(
                "can't query subvalue %r of a leaf%s."
                % (head,
                   (" (leaf value is %r)" % dct)
                   if len(repr(dct)) < 15 else ""))
    return aget(value, key)


# def mget(dct, key=None, default=None, create=False):
#     if key is None:
#         return dct
#     if "." not in key:
#         if key not in dct:
#             if create:
#                 dct[key] = {}
#             else:
#                 return default
#         return dct[key]

#     head, tail = key.split('.', 1)
#     if head not in dct:
#         if create:
#             dct[head] = {}
#         elif default:
#             return default
#         else:
#             raise ValueError("No subsection %r defined." % head)
#     return mget(dct[head], tail, default, create)


Null = object()


def mset(dct, key, value, tokenize=mk_char_tokenizer(".")):
    """Set a value in multiple depth dict.


    Will go down the dict hierarchy following the tokens in the key::

        >>> from pprint import pprint as pp

    On direct values, its job is quite easy::

        >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
        >>> mset(dct, 'x', 2)
        >>> pp(dct)
        {'a': {'b': {'y': 0}}, 'x': 2}

    On nested dict, it'll traverse them::

        >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
        >>> mset(dct, 'a.b.y', 3)
        >>> pp(dct)
        {'a': {'b': {'y': 3}}, 'x': 1}

    If the key doesn't exist, it will create it of course::

        >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
        >>> mset(dct, 'a.b.z', 9)
        >>> mset(dct, 't', 8)
        >>> pp(dct)
        {'a': {'b': {'y': 0, 'z': 9}}, 't': 8, 'x': 1}

    And it'll create intermediate dict if not existing::

        >>> dct = {'x': 1}
        >>> mset(dct, 'a.b.z', 9)
        >>> pp(dct)
        {'a': {'b': {'z': 9}}, 'x': 1}

    """
    last = Null
    token = None
    for token in tokenize(key):
        if last is not Null:
            try:
                dct = aget(dct, (last, ))
            except MissingKeyError:
                dct[last] = {}
                dct = dct[last]
        last = token
    dct[token] = value


def mdel(dct, key, tokenize=mk_char_tokenizer(".")):
    """delete a value in multiple depth dict

    Will go down the dict hierarchy following the tokens in the key::

        >>> from pprint import pprint as pp

    On direct values, its job is quite easy::

        >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
        >>> mdel(dct, 'x')
        >>> pp(dct)
        {'a': {'b': {'y': 0}}}

    On nested dict, it'll traverse them::

        >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
        >>> mdel(dct, 'a.b.y')
        >>> pp(dct)
        {'a': {'b': {}}, 'x': 1}

    If the key doesn't exist, it should complain::

        >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
        >>> mdel(dct, 'a.b.z')
        Traceback (most recent call last):
        ...
        KeyError: 'z'

    """
    last = Null
    token = None
    for token in tokenize(key):
        if last is not Null:
            dct = aget(dct, (last, ))
        last = token
    del dct[token]


class mdict(object):
    """Returns a mdict from a dict-like


    So you can instanciate one::

        >>> d = mdict(
        ...     {'a': {'b': {'y': 0}}, 'x': 1},
        ...     tokenize=mk_char_tokenizer('/'))

    And use normal get/getitem::

        >>> d['x']
        1
        >>> d['a/b/y']
        0
        >>> d['a/b/z']
        Traceback (most recent call last):
        ...
        MissingKeyError: missing key 'z' in dict.

        >>> d.get('a/b/z')
        >>> d.get('a/b/z', 3)
        3
        >>> d['a/b']
        m{'y': 0}

    Notice that you can access sub dicts and that they are returning
    a mdict instance. You can notice mdict instances by the 'm' prefix.

    Of course setting item works the same::

        >>> d['a/b/z'] = 2
        >>> d
        m{'a': {'b': {'y': 0, 'z': 2}}, 'x': 1}

    And deleting items::

        >>> del d['a/b']
        >>> d
        m{'a': {}, 'x': 1}

    """

    def __init__(self, dct, tokenize=mk_char_tokenizer(".")):
        self.dct = dict(dct)
        self.tokenize = tokenize

    def get(self, label, default=None):
        try:
            return self[label]
        except MissingKeyError:
            return default

    def __getitem__(self, label):
        res = mget(self.dct, label, tokenize=self.tokenize)
        if isinstance(res, dict):
            res = mdict(res)
        return res

    def __setitem__(self, label, value):
        return mset(self.dct, label, value, tokenize=self.tokenize)

    def __repr__(self):
        return 'm%s' % pprint.pformat(self.dct)

    def __delitem__(self, key):
        mdel(self.dct, key, tokenize=self.tokenize)

# -*- coding: utf-8 -*-

import re
import pprint
import collections

from kids.cache import cache, hippie_hashing

from .dct import DictLikeAbstract, is_dict_like


def mk_solid_split(split_char=".", quote_char="\\"):
    r"""Split string with escaping capabilities

        >>> ssplit = mk_solid_split()

    The classical usage is without surprises::

        >>> ssplit('abc')
        'abc'
        >>> ssplit('a.bc')
        ('a', 'bc')
        >>> ssplit('a.b.c')
        ('a', 'b.c')

    Notice that final string or key gets unquoted, but not values::

        >>> assert ssplit(r'a\.bc')  ==  r'a.bc'
        >>> assert ssplit(r'a\\.bc') == ('a' + '\\', r'bc')
        >>> ssplit(r'a\.b.c')
        ('a.b', 'c')
        >>> ssplit(r'a\.b.c\.d')
        ('a.b', 'c\\.d')

    Empty string can be keys::

        >>> ssplit('.b.c')
        ('', 'b.c')
        >>> ssplit('')
        ''

    """

    ## Current format::
    ##   state_machine := (STATE0, STATE2, ...)
    ##   STATEx := [(match_char, STATEy), ...]

    ## On this state_machine::
    ##   0 is normal and starting state
    ##   1 is quoted,
    ##   None is final state.

    state_machine = ([(quote_char, 1),
                      (split_char, None),
                      (None, 0)],
                     [(None, 0)])

    def next_state(state, char):
        for pattern, dest in state_machine[state]:
            if pattern == char or pattern is None:
                return dest
        assert "Invalid State Machine"

    def split(s):
        state = 0
        acc = []
        for i, char in enumerate(s):
            state = next_state(state, char)
            if state is None:
                return ''.join(acc), s[i + 1:]
            if state == 0:
                acc.append(char)
        return ''.join(acc)
    return split


def mk_sep_fun(sep, strip=True, quote_char="\\"):
    """Create a standard separator upon string keys

    >>> f = mk_sep_fun(".")
    >>> f(("a.b.c", 3))
    ('a', ('b.c', 3), False)

    >>> f(("a", 3))
    ('a', 3, True)

    """

    ssplit = mk_solid_split(sep, quote_char)

    def sep_fun(value, deep=-1):
        """Return couple Head Key, Tail Value

        If you want to classify elements, this function will have the
        responsibility to return a head key string, and a possible
        different tail value (elements may be transformed by
        classification).

        """
        if deep == 0:
            return value[0], value[1], True
        splitted = ssplit(value[0])
        if not isinstance(splitted, tuple):
            return splitted, value[1], True
        head, tail = splitted
        return head, (tail, value[1]), False

    return sep_fun


def mk_join_fun(sep, quote_char="\\"):
    r"""Create a standard join string keys with given sep

        >>> f = mk_join_fun(".")
        >>> f('a', ('b.c', 3), False)
        ('a.b.c', 3)

        >>> f('a', 3, True)
        ('a', 3)

        >>> f('a.b', 3, True)
        ('a\\.b', 3)

        >>> f('a.b', ('c', 3), False)
        ('a\\.b.c', 3)

    It's generating the perfect inverse of ``mk_sep_fun()``::

        >>> sep, join = mk_sep_fun("/"), mk_join_fun("/")
        >>> id1 = lambda *a: sep(join(*a))
        >>> id2 = lambda *a: join(*sep(*a))
        >>> id1('a', ('b/c', 3), False)
        ('a', ('b/c', 3), False)
        >>> id2(("a/b/c", 3))
        ('a/b/c', 3)

    And also with quoting enabled::

        >>> assert id1('a.b', (r'c.d\\.e\.h', 3), False) == ('a.b', (r'c.d\\.e\.h', 3), False)

        >>> id2((r'a.b\.c', 3))
        ('a.b.c', 3)

    Notice that we lost the \ before the point, because it is not important.

        >>> id2((r'a/b\/c', 3))
        ('a/b\\/c', 3)

    And we didn't loose this one, as it is important.

        >>> id2((r'a\/b/c', 3))
        ('a\\/b/c', 3)

        >>> assert id2((r'a\/b\\/c', 3)) == (r'a\/b\\/c', 3)

    """

    prepare = {
        'sc': re.escape(sep),
        'qc': re.escape(quote_char),
    }

    quote_chars = re.compile(r'(%(qc)s|%(sc)s)' % prepare)

    def quote(s):
        return quote_chars.sub(r'%(qc)s\1' % prepare, s)

    def join_fun(key, value, final):
        """Return the join key and value

        if final is set, then
        If you want to classify elements, this function will have the
        responsibility to return a head key string, and a possible
        different tail value (elements may be transformed by
        classification).

        """
        if final:
            return quote(key), value
        return sep.join((quote(key), value[0])), value[1]

    return join_fun


def classify(values, sep_fun, deep=-1):
    """Classify your values in a hierarchical dict

        >>> def sep_fun(value, deep=-1):
        ...     primes = [v for v in [2, 3, 5, 7] if value % v == 0]
        ...     if len(primes) == 0:
        ...         return None, value, True
        ...     tailv = value / primes[0]
        ...     return primes[0], int(tailv), tailv == 1
        >>> classify([6, 9, 15, 20, 32], sep_fun)
        {2: {2: {2: {2: {2: 1}}, 5: 1}, 3: 1}, 3: {3: 1, 5: 1}}

    Note that we can classify all these numbers only because none
    of them is multiple of another and ... Hum to complicated to
    sum up, but this will make it crash::

        >>> classify([6, 9, 15, 20, 2], sep_fun)
        Traceback (most recent call last):
        ...
        TypeError: Previous key 2 ..., but we would like to set final 1 in it.

    Depending on which order these are classified, the order could
    be reversed::

        >>> classify([2, 6, 9, 15, 20], sep_fun)
        Traceback (most recent call last):
        ...
        TypeError: Previous key 2 ..., but we would like to set final 1 in it.


    """

    def mset(dct, value, sep_fun, deep=-1):
        headk, tailv, final = sep_fun(value, deep)
        if final:
            if headk in dct:
                raise TypeError(
                    "Previous key %s was set to a subhierarchy"
                    " value %r, but we would like to set final %r in it."
                    % (headk, dct[headk], tailv))

            dct[headk] = tailv
        else:
            if headk not in dct:
                dct[headk] = {}
            if not is_dict_like(dct[headk]):
                raise TypeError(
                    "Previous key %s was set to a final"
                    " value %r, but we would like to classify %r in it."
                    % (headk, dct[headk], tailv))
            mset(dct[headk], tailv,
                 sep_fun=sep_fun,
                 deep=-1 if deep < 0 else deep - 1)

    res = {}
    for value in values:
        mset(res, value, sep_fun, deep)
    return res


def unclassify(dct, join_fun, deep=-1):
    """Returns all values precedently classified in dict

        >>> def join_fun(key, value, _final):
        ...     return key * value

        >>> from pprint import pprint as pp
        >>> pp(sorted(unclassify(
        ...     {2: {2: {2: {2: {2: 1}}, 5: 1}, 3: 1}, 3: {3: 1, 5: 1}},
        ...     join_fun)))
        [6, 9, 15, 20, 32]

    """
    for k, v in dct.items():
        if is_dict_like(v) and (deep > 0 or deep == -1):
            for v2 in unclassify(v, join_fun,
                                 deep=-1 if deep < 0 else deep - 1):
                yield join_fun(k, v2, False)
        else:
            yield join_fun(k, v, True)


def inflate(dct, sep=".", deep=-1):
    """Inflates a flattened dict.

    Will look in simple dict of string key with string values to
    create a dict containing sub dicts as values.

    Samples are better than explanation:

        >>> from pprint import pprint as pp
        >>> pp(inflate({'a.x': 3, 'a.y': 2}))
        {'a': {'x': 3, 'y': 2}}

    The keyword argument ``sep`` allows to change the separator used
    to get subpart of keys:

        >>> pp(inflate({'etc/group': 'geek', 'etc/user': 'bob'}, "/"))
        {'etc': {'group': 'geek', 'user': 'bob'}}

    Warning: you cannot associate a value to a section:

        >>> inflate({'section.key': 3, 'section': 'bad'})
        Traceback (most recent call last):
        ...
        TypeError: ...

    Of course, dict containing only keys that doesn't use separator will be
    returned without changes:

        >>> inflate({})
        {}
        >>> inflate({'a': 1})
        {'a': 1}

    Argument ``deep``, is the level of deepness allowed to inflate dict:

        >>> pp(inflate({'a.b.c': 3, 'a.d': 4}, deep=1))
        {'a': {'b.c': 3, 'd': 4}}

    Of course, a deepness of 0 won't do anychanges, whereas deepness of -1 is
    the default value and means infinite deepness:

        >>> pp(inflate({'a.b.c': 3, 'a.d': 4}, deep=0))
        {'a.b.c': 3, 'a.d': 4}

    """
    return classify(dct.items(), sep_fun=mk_sep_fun(sep), deep=deep)


def deflate(dct, sep=".", deep=-1):
    r"""Flattens a recursive dict

    This will create a flat dict (with no subdict) from dict structure::

        >>> import pprint
        >>> pprint.pprint(deflate({'a': {'b': 1, 'c': 2}, 'd': 3}))
        {'a.b': 1, 'a.c': 2, 'd': 3}

    Quoting any separator char found in the keys::

        >>> pprint.pprint(deflate({'a.b': {'c': 1}}))
        {'a\\.b.c': 1}

    With the ``deep`` argument, you can stop the deflateing to a
    specified deepness::

        >>> pprint.pprint(deflate({'a': {'b': 1, 'c': {'x': 9}}, 'd': 3},
        ...               deep=1))
        {'a.b': 1, 'a.c': {'x': 9}, 'd': 3}

    """
    return dict(unclassify(dct, join_fun=mk_join_fun(sep), deep=deep))


flatten = deflate


def mk_tokenize_from_sep_fun(sep):
    """Return a tokenizer from a sep function

    >>> sep_fun = mk_sep_fun(".")
    >>> tokenize = mk_tokenize_from_sep_fun(sep_fun)
    >>> list(tokenize('a.b.c'))
    ['a', 'b', 'c']

    """

    def tokenizing(s):
        """Returns an iterable through all subtoken"""
        def _rec(s):
            head, tail, final = sep(s)
            yield head
            if final:
                yield tail
            else:
                for e in _rec(tail):
                    yield e
        for e in _rec(s):
            yield e

    End = object()

    def tokenize(s):
        for token in tokenizing((s, End)):
            if token is End:
                raise StopIteration
            yield token

    return tokenize


def mk_untokenize_from_join_fun(join):
    r"""Return a untokenize function from a join function

    >>> join_fun = mk_join_fun(".")
    >>> untokenize = mk_untokenize_from_join_fun(join_fun)
    >>> untokenize(['a', 'b', 'c'])
    'a.b.c'

    >>> untokenize(['a.x', 'b', 'c'])
    'a\\.x.b.c'

    """

    End = object()

    def untokenizing(tokens):
        head, tail = tokens[0], tokens[1:]
        if len(tail) == 0:
            return join(head, End, True)
        return join(head, untokenizing(tail), False)
 
    def untokenize(tokens):
        if len(tokens) == 0:
            raise ValueError("Must provide at least one token to tokenize.")
        return untokenizing(tokens)[0]

    return untokenize


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

        >>> print('\n'.join(tokenize(r'foo.dot<\.>.slash<\\>.slash<\\>')))
        foo
        dot<.>
        slash<\>
        slash<\>

    Notice that empty keys are also supported:

        >>> list(tokenize(r'foo..bar'))
        ['foo', '', 'bar']

    Given an empty string:

        >>> list(tokenize(r''))
        ['']

    # And a None value:

    #     >>> list(tokenize(None))
    #     []


    """
    return mk_tokenize_from_sep_fun(
        mk_sep_fun(split_char, quote_char=quote_char))


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

    # if the key is None, the whole dct should be sent back:

    #     >>> mget({'a': 1}, None)
    #     {'a': 1}

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


Tokenizer = collections.namedtuple(
    'Tokenizer',
    ["split", "join",
     "quote", "unquote",
     "tokenize", "untokenize"])


class CharTokenizer(object):

    def __init__(self, sep, quote_char="\\"):
        self.sep = sep
        self.quote_char = quote_char

    @cache
    @property
    def split(self):
        return mk_sep_fun(self.sep, self.quote_char)

    @cache
    @property
    def join(self):
        return mk_join_fun(self.sep, self.quote_char)

    @cache
    @property
    def tokenize(self):
        return mk_tokenize_from_sep_fun(self.split)

    @cache
    @property
    def untokenize(self):
        return mk_untokenize_from_join_fun(self.join)

    def quote(self, k):
        return self.untokenize([k])

    def unquote(self, k):
        return self.tokenize(k).next()


class mdict(DictLikeAbstract):
    r"""Returns a mdict from a dict-like

        >>> from pprint import pprint as pp

    So you can instanciate one::

        >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
        >>> d = mdict(dct, tokenizer=CharTokenizer('/'))

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

    Or::

        >>> d['a/b']['y'] = 9

    And it will modify in place the original dct::

        >>> pp(dct)
        {'a': {'b': {'y': 9, 'z': 2}}, 'x': 1}

    And deleting items::

        >>> del d['a/b']
        >>> d
        m{'a': {}, 'x': 1}
        >>> pp(dct)
        {'a': {}, 'x': 1}

    It supports also the ``.items()`` method::

        >>> sorted(d.items())
        [('a', m{}), ('x', 1)]

    It supports also ``.items()``::

        >>> d = mdict(
        ...     {'a': {'b': {'y': 0}}, 'x': 1},
        ...     tokenizer=CharTokenizer('/'))
        >>> sorted(d.items())
        [('a', m{'b': {'y': 0}}),
         ('x', 1)]

    And ``len``:

        >>> len(d)
        2


    Quoting
    -------

    If your original keys happens to hold the separator char, any keys
    will appears with the quoted char::

       >>> d = mdict({'8.8.8.8': 'google'})
       >>> sorted(d.items())
       [('8\\.8\\.8\\.8', 'google')]

       >>> d = mdict({'a.b': {'c': 'google'}})
       >>> sorted(d.keys())
       ['a\\.b']


    Flatten form
    ------------

    You can also ask for the flattened version of the mdict:

        >>> from pprint import pprint as pp
        >>> d = mdict(
        ...     {'a': {'b': {'y': 0}}, 'x': 1},
        ...     tokenizer=CharTokenizer('/'))
        >>> pp(d.flat)
        {'a/b/y': 0,
         'x': 1}

        >>> del d['a/b']
        >>> pp(d.flat)
        {'x': 1}

    Notice how 'a' has disappeared as it is an empty section.

    """

    def __init__(self, dct, tokenizer=CharTokenizer(".")):
        self.dct = dct
        self.tokenizer = tokenizer

    def __getitem__(self, label):
        res = mget(self.dct, label, tokenize=self.tokenizer.tokenize)
        if is_dict_like(res):
            res = mdict(res, tokenizer=self.tokenizer)
        return res

    def __setitem__(self, label, value):
        return mset(self.dct, label, value, tokenize=self.tokenizer.tokenize)

    def __repr__(self):
        return 'm%s' % pprint.pformat(self.dct)

    def __delitem__(self, key):
        mdel(self.dct, key, tokenize=self.tokenizer.tokenize)

    def __iter__(self):
        for k in self.dct.__iter__():
            yield self.tokenizer.quote(k)

    @property
    @cache(key=lambda s: hippie_hashing(s.dct))
    def flat(self):
        return dict(unclassify(self.dct, join_fun=self.tokenizer.join))

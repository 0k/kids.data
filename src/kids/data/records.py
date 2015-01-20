"""Work on element list.


"""


def mk_sep_fun(sep, strip=True):
    """Create a standard separator upon string keys

    >>> f = mk_sep_fun(".")
    >>> f(("a.b.c", 3))
    ('a', ('b.c', 3), False)

    """
    def sep_fun(value):
        """Return couple Head Key, Tail Value

        If you want to classify elements, this function will have the
        responsibility to return a head key string, and a possible different tail
        value (elements may be transformed by classification).

        """
        if sep not in value[0]:
            return value[0], value[1], True
        else:
            head, tail = value[0].split(sep, 1)
            return head, (tail, value[1]), False

    return sep_fun


def classify(values, sep_fun, deep=-1):
    """Classify your values in a hierarchical dict


    >>> def sep_fun(value):
    ...     primes = [v for v in [2, 3, 5, 7] if value % v == 0]
    ...     if len(primes) == 0:
    ...         return None, value, True
    ...     tailv = value / primes[0]
    ...     return primes[0], int(tailv), tailv == 1
    >>> classify([6, 9, 15, 20, 32], sep_fun)
    {2: {2: {2: {2: {2: 1}}, 5: 1}, 3: 1}, 3: {3: 1, 5: 1}}

    """

    def mset(dct, value, sep_fun, deep=-1):
        headk, tailv, final = sep_fun(value)
        if final:
            dct[headk] = tailv
        else:
            if headk not in dct:
                dct[headk] = {}
            if not isinstance(dct[headk], dict):
                raise TypeError("Previous key %s was set to a non subhierarchy"
                                " value %r, but we would like to classify %r in it."
                                % (headk, dct[headk], tailv)
                                )
            if deep == 1:
                dct[headk] = tailv
            else:
                mset(dct[headk], tailv,
                     sep_fun=sep_fun,
                     deep=-1 if deep < 0 else deep - 1)

    res = {}
    for value in values:
        mset(res, value, sep_fun, deep)
    return res





# def inflate_dict(dct, sep=".", strip=deep=-1):
#     """Inflates a flattened dict.

#     Will look in simple dict of string key with string values to
#     create a dict containing sub dicts as values.

#     Samples are better than explanation:

#         >>> from pprint import pprint as pp
#         >>> pp(inflate_dict({'a.x': 3, 'a.y': 2}))
#         {'a': {'x': 3, 'y': 2}}

#     The keyword argument ``sep`` allows to change the separator used
#     to get subpart of keys:

#         >>> pp(inflate_dict({'etc/group': 'geek', 'etc/user': 'bob'}, "/"))
#         {'etc': {'group': 'geek', 'user': 'bob'}}

#     Warning: you cannot associate a value to a section:

#         >>> inflate_dict({'section.key': 3, 'section': 'bad'}) # doctest: +ELLIPSIS
#         Traceback (most recent call last):
#         ...
#         TypeError: ...

#     Of course, dict containing only keys that doesn't use separator will be
#     returned without changes:

#         >>> inflate_dict({})
#         {}
#         >>> inflate_dict({'a': 1})
#         {'a': 1}

#     Argument ``deep``, is the level of deepness allowed to inflate dict:

#         >>> pp(inflate_dict({'a.b.c': 3, 'a.d': 4}, deep=1))
#         {'a': {'b.c': 3, 'd': 4}}

#     Of course, a deepness of 0 won't do anychanges, whereas deepness of -1 is
#     the default value and means infinite deepness:

#         >>> pp(inflate_dict({'a.b.c': 3, 'a.d': 4}, deep=0))
#         {'a.b.c': 3, 'a.d': 4}

#     """

#     return classify(dct.iteritems(), sep_fun=mk_sep_fun(sep), deep=deep)


def inflate_dict(dct, sep=".", deep=-1, strip=True):
    """Inflates a flattened dict.

    Will look in simple dict of string key with string values to
    create a dict containing sub dicts as values.

    Samples are better than explanation:

        >>> from pprint import pprint as pp
        >>> pp(inflate_dict({'a.x': 3, 'a.y': 2}))
        {'a': {'x': 3, 'y': 2}}

    The keyword argument ``sep`` allows to change the separator used
    to get subpart of keys:

        >>> pp(inflate_dict({'etc/group': 'geek', 'etc/user': 'bob'}, "/"))
        {'etc': {'group': 'geek', 'user': 'bob'}}

    Warning: you cannot associate a value to a section:

        >>> inflate_dict({'section.key': 3, 'section': 'bad'})
        Traceback (most recent call last):
        ...
        TypeError: 'str' object does not support item assignment

    Of course, dict containing only keys that doesn't use separator will be
    returned without changes:

        >>> inflate_dict({})
        {}
        >>> inflate_dict({'a': 1})
        {'a': 1}

    Argument ``deep``, is the level of deepness allowed to inflate dict:

        >>> pp(inflate_dict({'a.b.c': 3, 'a.d': 4}, deep=1))
        {'a': {'b.c': 3, 'd': 4}}

    Of course, a deepness of 0 won't do anychanges, whereas deepness of -1 is
    the default value and means infinite deepness:

        >>> pp(inflate_dict({'a.b.c': 3, 'a.d': 4}, deep=0))
        {'a.b.c': 3, 'a.d': 4}

    """

    def mset(dct, k, v, sep=".", deep=-1):
        if deep == 0 or sep not in k:
            dct[k] = v
        else:
            khead, ktail = k.split(sep, 1)
            if strip:
                khead, ktail = khead.strip(), ktail.strip()
            if khead not in dct:
                dct[khead] = {}
            mset(dct[khead], ktail, v,
                 sep=sep,
                 deep=-1 if deep < 0 else deep - 1)

    res = {}
    ## sorting keys ensures that colliding values if any will be string
    ## first set first so mset will crash with a TypeError Exception.
    for k in sorted(dct.keys()):
        mset(res, k, dct[k], sep, deep)
    return res


def flatten(dct, sep=".", deep=-1):
    """Flattens a recursive dict

    This will create a flat dict (with no subdict) from dict structure::

        >>> import pprint
        >>> pprint.pprint(flatten({'a': {'b': 1, 'c': 2}, 'd': 3}))
        {'a.b': 1, 'a.c': 2, 'd': 3}

    With the ``deep`` argument, you can stop the flattening to a
    specified deepness::

        >>> pprint.pprint(flatten({'a': {'b': 1, 'c': {'x': 9}}, 'd': 3},
        ...               deep=1))
        {'a.b': 1, 'a.c': {'x': 9}, 'd': 3}

    """
    res = {}
    for k, v in dct.items():
        if isinstance(v, dict) and (deep > 0 or deep == -1):
            for k2, v2 in flatten(v, sep, deep - 1).items():
                res["%s%s%s" % (k, sep, k2)] = v2
        else:
            res[k] = v
    return res

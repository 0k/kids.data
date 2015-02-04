# -*- coding: utf-8 -*-


def partition(elts, f):
    res = {}
    for e in elts:
        r = f(e)
        if r not in res:
            res[r] = []
        res[r].append(e)
    return res

Null = object()


def first(elts, predicate, default=Null):
    """Returns the first elt of elts that matches predicate

        >>> first([3, 7, 11, 15, 33], predicate=lambda x: x % 11 == 0)
        11

    But if no element matches the predicate it should cast an
    exception::

        >>> first([3, 7, 11, 15, 33], predicate=lambda x: x % 13 == 0)
        Traceback (most recent call last):
        ...
        ValueError: No value matches predicate

    We can also set a default value in case of no match::

        >>> first([3, 7, 11, 15, 33], predicate=lambda x: x % 13 == 0, 0)
        0

    """
    for elt in elts:
        if predicate(elt):
            return elt
    if default is Null:
        raise ValueError("No value matches predicate")
    else:
        return default

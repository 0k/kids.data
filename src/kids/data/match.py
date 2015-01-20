# -*- coding: utf-8 -*-

import kids.cache


try:
    import distance
except ImportError:  ## pragma: no cover
    distance = None

##
## Criterias
##

if distance:  ## pragma: no cover
    levenstein = lambda a, b: 1 - distance.nlevenshtein(a, b)
else:  ## pragma: no cover
    def levenstein(a, b):
        raise Exception(
            "'levenstein' function needs python module 'distance' "
            "to be available.")
equal = lambda a, b: a == b
size = lambda a, b: len(a) == len(b)


##
## Criteria Factory
##

def weighted(criterias_weights):
    """Return callable criteria with weighted sub-criteria values

    This allows you to create a new criteria function by mixing others.

        >>> weighted([(equal, 1)])("foo", "bar")
        0.0
        >>> weighted([(equal, 1)])("foo", "foo")
        1.0
        >>> weighted([(equal, 1), (size, 1)])("foo", "bar")
        0.5
        >>> weighted([(equal, 3), (size, 1)])("foo", "bar")
        0.25

    """
    def wc(a, b):
        s = 0
        tot_wh = 0
        for cr, wh in criterias_weights:
            s += float(cr(a, b)) * wh
            tot_wh += wh
        return s / tot_wh
    return wc


def avg(criterias):
    """Return average matching for given criteria

    >>> avg([equal])("foo", "bar")
    0.0
    >>> avg([equal])("foo", "foo")
    1.0
    >>> avg([levenstein])("bar", "baz")  ## doctest: +ELLIPSIS
    0.66...
    >>> avg([levenstein])("bar", "foo")
    0.0

    >>> avg([levenstein, size, equal])("bar", "barb")
    0.25
    >>> avg([levenstein, size, equal])("bar", "baz")  ## doctest: +ELLIPSIS
    0.55...

    """
    return weighted([(cr, 1) for cr in criterias])


##
## Using criterias
##

@kids.cache.cache
def match(a, b, criteria):
    """Return a float between 0 and 1. 1 is perfect match.

    Could Store result in cache.

    """
    return criteria(a, b)


def first_match(elt, targets, criteria):
    """Returns False or perfect match in targets matching criterias if found

    Suppose you have one elt, and you want to find the first perfect match for
    this elt in list of other elts.

        >>> first_match("foo", ["bar", "barb", "fooz", "foo", "zob"],
        ...    criteria=avg([levenstein, size, equal]))
        'foo'

    If no element matches, it should return False::

        >>> first_match("foo", ["bar", "barb", "fooz", "zob"],
        ...    criteria=equal)
        False

    """
    for target in targets:
        if match(elt, target, criteria) == 1:
            return target
    return False


def close_matches(elt, targets, criteria, min_ratio=0.):
    """Return only matches above min_ratio, first matches are the best.

        >>> close_matches("foo",
        ...    ["bar", "barb", "fooz", "foo", "zob"],
        ...    criteria=avg([levenstein, size, equal]),
        ...    min_ratio=0.1)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [('foo', 1.0), ('zob', 0.44...), ('bar', 0.33...), ('fooz', 0.25)]

    Notice that 'barb' has disappeared as its ratio is below ``min_ratio``.
    They are also sorted with the best match first.

    """
    candidates = [(target, match(elt, target, criteria)) for target in targets]
    candidates = [(target, ratio)
                  for target, ratio in candidates
                  if ratio > min_ratio]
    candidates.sort(key=lambda tr: tr[1], reverse=True)
    return candidates

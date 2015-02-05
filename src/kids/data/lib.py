# -*- coding: utf-8 -*-


def partition(elts, predicate):
    """Splits elts depending on their result.

    Partitions set of elts. Result of the predicate must be hashable.

        >>> partition("qweryuop ", lambda x: "How are you ?".count(x))
        {0: ['q', 'p'], 1: ['w', 'e', 'r', 'y', 'u'], 2: ['o'], 3: [' ']}

    """
    heaps = {}
    for elt in elts:
        key = predicate(elt)
        heaps[key] = heaps.get(key, []) + [elt]
    return heaps


def half_split_on_predicate(elts, predicate):
    """Splits elts in two thanks to a predicate function.

    Partitions set of elts. Result of the predicate must be boolean.

        >>> half_split_on_predicate("qweryuop ", lambda x: x in "How are you ?")
        (['q', 'p'], ['w', 'e', 'r', 'y', 'u', 'o', ' '])

    """

    heaps = partition(elts, predicate)
    return heaps.get(False, []), heaps.get(True, [])


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

        >>> first([3, 7, 11, 15, 33], predicate=lambda x: x % 13 == 0,
        ...       default=0)
        0

    """
    for elt in elts:
        if predicate(elt):
            return elt
    if default is Null:
        raise ValueError("No value matches predicate")
    else:
        return default

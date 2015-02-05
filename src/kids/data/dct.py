# -*- coding: utf-8 -*-

from itertools import chain


def merge(*args):
    """Merging n dicts into one.

    Warning, it's not recursive.

    """
    return dict(chain(*[d.items() for d in args]))

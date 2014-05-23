# -*- coding: utf-8 -*-


def partition(elts, f):
    res = {}
    for e in elts:
        r = f(e)
        if r not in res:
            res[r] = []
        res[r].append(e)
    return res


def first(elts, f):
    for elt in elts:
        if f(elt):
            return elt
    raise ValueError("No value matches predicate")

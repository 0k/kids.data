# -*- coding: utf-8 -*-


def cycle_exists(node, fun_children):
    """Check if there's no cycle starting from node

    >>> graph = {1: [2, 3]}
    >>> get_children = lambda n: graph.get(n, [])
    >>> cycle_exists(1, get_children)
    False
    >>> graph = {1: [2, 3], 2: [1]}
    >>> cycle_exists(1, get_children)
    True
    >>> graph = {1: [1]}
    >>> cycle_exists(1, get_children)
    True

    """
    nodes = []
    res = set(fun_children(node))
    while res:
        n = res.pop()
        if n == node:
            return True
        nodes.append(n)
        res |= set([c for c in fun_children(n)
                    if c not in nodes])
    return False


def leafage(elts, fun_deps):
    """Get all leafs of DAG

    >>> graph = {2: [1]}
    >>> get_children = lambda n: graph.get(n, [])
    >>> list(leafage([], get_children))
    []
    >>> list(leafage([2, 1], get_children))
    [1]
    >>> sorted(leafage([2, 3], get_children))
    [1, 3]

    """
    done = set([])
    todo = set(elts)
    leafs = set([])
    while todo:
        e = todo.pop()
        done.add(e)
        deps = fun_deps(e)
        if len(deps) == 0:
            leafs.add(e)
        else:
            for d in deps:
                if d not in done:
                    todo.add(d)
    return leafs


def invert_fun(elts, fun_deps):
    """Return invert of fun_deps

    >>> graph = {2: [1]}
    >>> get_children = lambda n: graph.get(n, [])
    >>> list(invert_fun([], get_children)(1))
    []
    >>> list(invert_fun([2, 1], get_children)(2))
    []
    >>> list(invert_fun([2, 1], get_children)(1))
    [2]
    >>> list(invert_fun([2, 1, 3], get_children)(3))
    []

    """

    ## build cache
    dct = {}
    for e in elts:
        for d in fun_deps(e):
            if d not in dct:
                dct[d] = set([])
            dct[d].add(e)

    def f(e):
        return dct.get(e, set([]))

    return f


def swap(l, p1, p2):
    l[p1], l[p2] = l[p2], l[p1]


def reorder(elts, fun_deps):
    """Reorder and return ordered elt list so that deps are satisfied.

    Elements can be of any types. This function will try to male
    the least changes to the original elements list and will work
    in place.

    Another assumption, is that there are no dependency to unknown
    elements.

    >>> graph = {2: [1]}
    >>> get_children = lambda n: graph.get(n, [])
    >>> reorder([], get_children)
    []
    >>> reorder([1, 3, 2], get_children)
    [1, 3, 2]
    >>> reorder([3, 2, 1], get_children)
    [3, 1, 2]

    >>> graph = {2: [1], 3: [2]}
    >>> reorder([1, 3, 2], get_children)
    [1, 2, 3]

    """

    leafs = leafage(elts, fun_deps)
    inv_fun = invert_fun(elts, fun_deps)

    idx = 0
    while idx < len(elts):
        seen = elts[:idx]
        if elts[idx] in seen:
            ## Duplicate !
            elts = seen + elts[idx+1:]
            continue
        if elts[idx] in leafs:
            ## It's ok, it depends on nothing
            leafs.remove(elts[idx])
            leafs |= set(e for e in inv_fun(elts[idx])
                         if all(x == elts[idx] or x in seen
                                for x in fun_deps(e)))
            idx += 1
            continue

        ## Bad ! if it's not a leaf it depends on something !
        ## Let's swap with it's last dependency

        last_dep = max(elts.index(n) for n in fun_deps(elts[idx]))
        assert last_dep > idx, "Circular dep ?"
        swap(elts, idx, last_dep)

    return elts

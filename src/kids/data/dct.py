# -*- coding: utf-8 -*-

import copy
from itertools import chain


def merge(*args):
    """Merging n dicts into one.

    Warning, it doesn't work on multi-depth dictionary.

    """
    return dict(chain(*[d.items() for d in args]))


def is_dict_like(obj):
    """Try to figure if the given obj gives a dict-like interface"""
    return all(hasattr(obj, method_name)
               for method_name in ["__getitem__", "__iter__", "get", "keys"])


class DictLikeAbstract(object):
    """Provide dict like methods from a limited subset.

    If you define ``__iter__`` and ``__getitem__``, it'll provide
    you with: ``get``, ``keys``, ``items``, and ``__len__``.

    """

    def __iter__(self):
        raise NotImplementedError()

    def __getitem__(self, label):
        raise NotImplementedError()

    def get(self, label, default=None):
        try:
            return self[label]
        except KeyError:
            return default

    def keys(self):
        return list(self.__iter__())

    def items(self):
        for k in self:
            yield k, self[k]

    def __len__(self):
        return len(self.keys())


class AttrDictAbstract(DictLikeAbstract):

    def __getattr__(self, label):
        if label.startswith("_"):
            return super(AttrDictAbstract, self).__getattr__(label)
        return self[label]

    def __setattr__(self, label, value):
        if label.startswith("_"):
            return super(AttrDictAbstract, self).__setattr__(label, value)
        return self.__setitem__(label, value)

    def __delattr__(self, label):
        if label.startswith("_"):
            return super(AttrDictAbstract, self).__delattr__(label)
        return self.__delitem__(label)


class MultiDictReader(AttrDictAbstract):
    """Multiple cascaded config file management

    Offers a cascaded read on several dict-like without merging them.

    It's a sort of lazy merge. Interesting if you have large dictionary.
    But it's also interesting if you are querying other things that only
    dicts, but objects that have advanced effects or interesting side
    effects when accessing them.

    It has also full support of recursive dicts.

        >>> from pprint import pprint as pp

    Usage
    =====

    Let's declare 2 dicts files::

        >>> d1 = {'x': 1, 'y': 2, 'z1': 3}
        >>> d2 = {'x': 1, 'y': 3, 'z2': 4}

        >>> mdct = MultiDictReader([d1, d2])

    Direct value
    ------------

    We can query via attribute/getitem the keys from the configuration::

        >>> mdct.x
        1
        >>> mdct['x']
        1

    This one is easy as this value is available and equal in all files.

    Notice that for ``y``, the first config file that can reply will take
    precedence::

        >>> mdct.y
        2

    Here, only one of the file has valued the requested key::

        >>> mdct.z1
        3
        >>> mdct.z2
        4

    Other dict features are also available::

        >>> mdct.get('wiz', 'default')
        'default'
        >>> mdct.get('wiz')
        >>> sorted(mdct.keys())
        ['x', 'y', 'z1', 'z2']
        >>> 'y' in mdct.keys()
        True
        >>> sorted(mdct.items())
        [('x', 1), ('y', 2), ('z1', 3), ('z2', 4)]


    Subsections
    -----------

    If the result is itself a dict-like object::

        >>> d1['b'] = {'foo': 5}
        >>> d2['b'] = {'bar': 6}

    Then the intermediate value:

        >>> isinstance(mdct.b, MultiDictReader)
        True

    It is itself also a multi dict reader, allowing such things::

        >>> mdct.b.foo
        5
        >>> mdct.b.bar
        6

    """

    def __init__(self, dcts):
        self._dcts = dcts

    def __getitem__(self, label):
        results = []
        results_nb = []
        # import pdb; pdb.set_trace()
        for i, dct in enumerate(self._dcts):
            try:
                res = dct.__getitem__(label)
            except KeyError:
                continue
            if is_dict_like(res):
                results.append(res)
                results_nb.append(i)
            else:
                if len(results) > 0:
                    raise ValueError(
                        "Incoherence between given dicts: "
                        "obj %d defines a non-empty section "
                        "where obj %d defines a leaf."
                        % (", ".join(results_nb), i))
                return res
        if len(results) == 0:
            raise KeyError(label)
        return self.__class__(results)

    def __iter__(self):
        seen = []
        for dct in self._dcts:
            for k in dct.keys():
                if k in seen:
                    continue
                yield k
                seen.append(k)


deep_copy = copy.deepcopy

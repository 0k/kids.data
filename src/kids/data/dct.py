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
deep_copy = copy.deepcopy

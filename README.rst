=========================
kids.data
=========================

.. image:: http://img.shields.io/pypi/v/kids.data.svg?style=flat
   :target: https://pypi.python.org/pypi/kids.data/
   :alt: Latest PyPI version

.. image:: http://img.shields.io/pypi/dm/kids.data.svg?style=flat
   :target: https://pypi.python.org/pypi/kids.data/
   :alt: Number of PyPI downloads

.. image:: http://img.shields.io/travis/0k/kids.data/master.svg?style=flat
   :target: https://travis-ci.org/0k/kids.data/
   :alt: Travis CI build status

.. image:: http://img.shields.io/coveralls/0k/kids.data/master.svg?style=flat
   :target: https://coveralls.io/r/0k/kids.data
   :alt: Test coverage


``kids.data`` is a Python library providing helpers to manage data.

It's part of 'Kids' (for Keep It Dead Simple) library.


Maturity
========

This code is in alpha stage. It wasn't tested on Windows. API may change.
This is more a draft for an ongoing reflection.

And I should add this is probably not ready to show. Although, a lot of these
function are used everyday in my projects and I got sick rewritting them for
every project.


Features
========

using ``kids.data``:

- You'll have a matching library to fuzzy match elements
- a formatter concept to help you format any type of data to another type
- a way to display tables of records on command line
- some everyday missing function for manipulating sets of elements


Installation
============

You don't need to download the GIT version of the code as ``kids.data`` is
available on the PyPI. So you should be able to run::

    pip install kids.data

If you have downloaded the GIT sources, then you could add install
the current version via traditional::

    python setup.py install

And if you don't have the GIT sources but would like to get the latest
master or branch from github, you could also::

    pip install git+https://github.com/0k/kids.data

Or even select a specific revision (branch/tag/commit)::

    pip install git+https://github.com/0k/kids.data@master


Usage
=====


mdict
-----

``mdict`` are nested dicts access in one go thanks to interpreting the key,
check this::

    >>> from pprint import pprint as pp
    >>> from kids.data.mdict import mdict

    >>> d = mdict({'a': {'b': {'y': 0}}, 'x': 1})
    >>> d['a.b.y']
    0
    >>> d.get('a.b.z', 3)
    3
    >>> d['a.b']
    m{'y': 0}

You can configure your mdict to use '/' instead, and if you want more you could
build your own key tokenizer to break your string into token::

    >>> from kids.data.mdict import CharTokenizer

    >>> d = mdict({'a': {'b': {'y': 0}}, 'x': 1}, CharTokenizer('/'))
    >>> d['a/b/y']
    0

Of course setting item works the same::

    >>> d['a/b/z'] = 2
    >>> d
    m{'a': {'b': {'y': 0, 'z': 2}}, 'x': 1}

And deleting items::

    >>> del d['a/b']
    >>> d
    m{'a': {}, 'x': 1}

Please note that the tokenizer is quite stable even with backslashed
or empty keys::

    >>> d[r'a/b\/c//d'] = 9
    >>> d
    m{'a': {'b/c': {'': {'d': 9}}}, 'x': 1}

And flattening back the key/values is done through ``flat`` property::

    >>> pp(d.flat)
    {'a/b\\/c//d': 9, 'x': 1}

If you just want to use it once on a nested dict, all the function are
ready for use::

    >>> from kids.data.mdict import mset, mget, mdel

    >>> dct = {'a': {'b': {'y': 0}}, 'x': 1}
    >>> mget(dct, 'a.b.y')
    0
    >>> mset(dct, 'a.b.z', 2)
    >>> pp(dct)
    {'a': {'b': {'y': 0, 'z': 2}}, 'x': 1}

    >>> mdel(dct, 'a.b')
    >>> pp(dct)
    {'a': {}, 'x': 1}


graph
-----

``graph`` provide a bunch of function to work with graph. In a
agnostic way, this means you can store your graph in whatever the form
you want. All you need to do it to provide a function to get the
related nodes from their related nodes.

Example with the ``cycle_exists`` function::

    >>> from kids.data.graph import cycle_exists

    >>> graph = {1: [2, 3], 2: [1]}
    >>> get_children = lambda n: graph.get(n, [])

    >>> cycle_exists(1, get_children)
    True

    >>> cycle_exists(3, get_children)
    False

As node ``3`` is a leaf there are no cycle starting from him.

You could get the ``leafage`` of a set of elements (a leaf is a final
node without children). The ``leafage`` is all the ``leaf`` that can
be reached from given elements::

    >>> from kids.data.graph import leafage

    >>> list(leafage([1, 4], get_children))
    [3, 4]

The nice one is ``reorder``, which will try to do the minimum change
to a given list, but will swap element to garanty no dependency
issues, this means that the children will appear before the
parents. This is very handy when loading modules that depends to
other modules::

    >>> from kids.data.graph import reorder

    >>> graph = {2: [1], 3: [2]}
    >>> reorder([1, 3, 2], get_children)
    [1, 2, 3]


dct
---

Merging dicts is something that should be in base python and is missing a lot of 
people (see this `stackoverflow question about merging dict non-inplace`_).

.. _stackoverflow question about merging dict non-inplace: http://stackoverflow.com/q/38987

You can use ``merge`` to merge several dicts into one::

     >>> from pprint import pprint
     >>> from kids.data.dct import merge

     >>> pp(merge({'a': 1}, {'a': 2, 'b': 1}, {'c': 3}))
     {'a': 2, 'b': 1, 'c': 3}


Contributing
============

Any suggestion or issue is welcome. Push request are very welcome,
please check out the guidelines.


Push Request Guidelines
-----------------------

You can send any code. I'll look at it and will integrate it myself in
the code base and leave you as the author. This process can take time and
it'll take less time if you follow the following guidelines:

- check your code with PEP8 or pylint. Try to stick to 80 columns wide.
- separate your commits per smallest concern.
- each commit should pass the tests (to allow easy bisect)
- each functionality/bugfix commit should contain the code, tests,
  and doc.
- prior minor commit with typographic or code cosmetic changes are
  very welcome. These should be tagged in their commit summary with
  ``!minor``.
- the commit message should follow gitchangelog rules (check the git
  log to get examples)
- if the commit fixes an issue or finished the implementation of a
  feature, please mention it in the summary.

If you have some questions about guidelines which is not answered here,
please check the current ``git log``, you might find previous commit that
would show you how to deal with your issue.


License
=======

Copyright (c) 2015 Valentin Lab.

Licensed under the `BSD License`_.

.. _BSD License: http://raw.github.com/0k/kids.data/master/LICENSE

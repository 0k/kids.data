========
kids.data
========


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

It is, for now, a very humble package.


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

Compatibility
=============

This code is tested for compatibility with python 2.7 and python >= 3 .


Documentation
=============

It's too early to offer a documentation for this package.




Tests
=====

Well, this package is really small, and you've just read the tests.

To execute them, install ``nosetest``, and run::

    nosetests


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

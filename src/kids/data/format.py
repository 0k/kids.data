# -*- coding: utf-8 -*-
"""
This module define the class Formatter and it main concepts.

>>> from pprint import pformat

"""

import math
import datetime
import sact.epoch


## Python 3 compatibility layer
try:
    unicode = unicode
except NameError:  ## pragma: no cover
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:  ## pragma: no cover
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring


class Formatter(object):
    r"""Generic formatter factory.

    A Formatter take a context and returns a callable which will use
    the context to format a value.

    context is optional.

      >>> from __future__ import print_function
      >>> f = Formatter()
      >>> assert f('hello') == 'hello'

    Context at init time
    --------------------

    Lets create a formatter that use the context:

      >>> from pprint import pformat

      >>> class MyFormatter(Formatter):
      ...     def format(self, value, context):
      ...          if isinstance(context, basestring): return "%r" % context
      ...          if context is None: return 'None'
      ...          return "value: %s\ncontext:\n%s" % (value, pformat(context))
      ...

    You can setup context at instanciation time or at call time:

      >>> fmt = Formatter({'data': 'foo'})
      >>> fmt.context['data']
      'foo'

    To add convenience, you can specify some value in named arguments:
      >>> fmt = Formatter(data='foo')
      >>> fmt.context['data']
      'foo'

    These two way are combinable, but beware of overwrite !

      >>> fmt = Formatter({'data': 'foo'}, data='bar')
      >>> fmt.context['data']
      'bar'

    Non dict-like values in context are not allowed if you use keyword
    arguments:

      >>> fmt = Formatter(3, data='bar')
      Traceback (most recent call last):
      ...
      TypeError: ... you cannot init your Formatter with named args.

    While any python object is allowed if you do not use keyword args :

      >>> fmt = Formatter(3)
      >>> fmt.context
      3

    Context at call time
    --------------------

    You can provide a context at call-time
      >>> fmt = Formatter()
      >>> assert fmt('hello', data='bar') == 'hello'

    Context can be explicitly named and set:

      >>> fmt = MyFormatter(context={'data': 'foo', 'ginko': 'biloba'},
      ...                   data='bar')

    Then set

      >>> print(fmt('hop', context={'data': 'bar2'}))
      value: hop
      context:
      {'_': <function ... at ...>,
      'data': 'bar2',
      'gettextargs': {},
      'ginko': 'biloba',
      'trans': <function ...trans at ...>}


    Support of old API:
    -------------------

      >>> class MyFormatter(Formatter):
      ...     def format(self, value):
      ...          return "%s" % value
      ...

      >>> fmt = MyFormatter()

      >>> print(fmt('hop'))
      hop

    """

    def __init__(self, context=None, **kwargs):
        self.context = self._get_context(context, **kwargs)

    def _get_context(self, context=None, **kwargs):
        """This function returns a context from keyword args and context

        Note: to be thread safe, this function does not store anything in
        the current object.

        Note2: to be compatible with default overriding classes we must
        check the prototype of the function format.

        """

        ## Get a dict copy of self.context if existent

        try:
            if hasattr(self, 'context'):
                _context = dict(self.context)  ## copy to be thread safe
            else:
                _context = {}
        except (ValueError, TypeError):
            _context = {}

        ## Merge with context values if any

        if context is None:
            context = {}

        if isinstance(context, dict):
            try:
                _context.update(context)  ## Update with new values
                context = _context

                ## Put i18n informations to context

                if '_' not in context:
                    def trans(msg, *args, **kwargs):
                        return unicode(msg)
                    context['_'] = trans

                context.setdefault('gettextargs', {})

                def trans(msg, *args, **kwargs):
                    """Shortcut function for translation"""
                    kwargs.update(context['gettextargs'])
                    return context['_'](msg, *args, **kwargs)

                context['trans'] = trans

            except TypeError:  ## Context is not a dict
                pass  ## context must be unchanged

        ## Merge with keyword arguments

        if kwargs:
            if not hasattr(context, '__setitem__'):
                raise TypeError(
                    'Your context %r has no __setitem__ and thus '
                    'you cannot init your Formatter with named args.'
                    % context)
            for key, value in kwargs.items():
                context[key] = value

        return context

    def __call__(self, value, context=None, **kwargs):

        ## XXXvlab: ---- COMPATIBILITY CODE BEGIN (to delete)

        self._formatting_structure = self.context

        import inspect
        from warnings import warn

        (posargs, _, _, defaults) = inspect.getargspec(self.format)

        if posargs[0] == 'self':
            posargs = posargs[1:]

        if len(posargs) == 1: ## OLD API
        ##XXXgsa: finaly we keep the old API

        #     warn('Formatter.format(..) should use 3 arguments with new API.',
        #          DeprecationWarning, stacklevel=2)
            return self.format(value)

        ## --- COMPATIBILITY CODE END

        return self.format(value, self._get_context(context, **kwargs))

    def format(self, value, context=None):
        # Default formatting does nothing
        return unicode(value)



class CompoundFormatter(Formatter):
    """Compose Formatter from several subformatter

    The formatters are passed the last ones result and thus
    are chained one to the next in the list.

    XXXvlab: should we migrate this behavior in the main formatter ?

    Usage
    =====

    >>> from kids.data.format import Formatter, CompoundFormatter

    Let's creates two simple formatters:

    >>> class AddX(Formatter):
    ...    def format(self, value, context=None):
    ...        return value + context['nb']

    This formatter factory will simply create a formatter that adds
    'nb' to the value formatted:

    >>> myAdd2 = AddX(nb=2)
    >>> myAdd2(10)
    12

    This formatter factory will embrace the formatted value with given
    characters in the 'sep' variable:

    >>> class Embrace(Formatter):
    ...    def format(self, value, context=None):
    ...        return "%s%s%s" % (context['sep'][0], value, context['sep'][1])

    >>> myParenEmbrace = Embrace(sep='()')
    >>> myParenEmbrace('hello')
    '(hello)'

    Let's create a compound formatter factory:

    >>> myCompoundFormatter = CompoundFormatter(compound=[myAdd2,
    ...                                                   myParenEmbrace])
    >>> myCompoundFormatter(20)
    '(22)'

    Similar uses:

    >>> CompoundFormatter(compound=[AddX(nb=20), Embrace(sep='<>')])(10)
    '<30>'

    """

    def format(self, value, context=None):
        for subformatter in self.context['compound']:
            value = subformatter(value, context)
        return value


def Chain(chain):
    """Shorctut to create a CompoundFormatter

    Usage
    =====

    >>> from kids.data.format import Formatter, Chain

    >>> class AddX(Formatter):
    ...    def format(self, value, context=None):
    ...        return value + context['nb']

    This formatter factory will simply create a formatter that adds
    'nb' to the value formatted:

    >>> myAdd2 = AddX(nb=2)
    >>> myAdd2(10)
    12

    This formatter factory will embrace the formatted value with given
    characters in the 'sep' variable:

    >>> class Embrace(Formatter):
    ...    def format(self, value, context=None):
    ...        return "%s%s%s" % (context['sep'][0], value, context['sep'][1])

    >>> myParenEmbrace = Embrace(sep='()')
    >>> myParenEmbrace('hello')
    '(hello)'

    Let's create a compound formatter factory:

    >>> myfmt = Chain([AddX(nb=20), Embrace(sep='<>')])
    >>> myfmt(1)
    '<21>'

    """
    return CompoundFormatter(compound=chain)


Formatter.__or__ = lambda self, value: Chain([self, value])


class TimeStampFormatter(Formatter):
    """Format a date to a short string representation

    If a timeframe is provided to the constructor, the output
    will be reduced to the minimum output.

    >>> format_timestamp = TimeStampFormatter()

    >>> assert format_timestamp(1226929090) == '2008-11-17 13:38:10'

    timeframe usage
    ~~~~~~~~~~~~~~~

    You can provide a structure to the constructor to declare
    what are the allowed segments to display:

    >>> s = ((0, 2), (1, 4), (3, 5))

    The structure must be a iterable containing couples of
    (min, max) value indicating the beginning and the ending
    of the segment allowed.

    These min and max are an integer that represent a specific
    field in the ISO format representation :

                           0  1  2  3  4  5
    ISO representation : YYYY-MM-DD HH-MM-SS

    So Y is 0, M is 1, D is 2, H is 3, M is 4, S are fifth field.

    Declaring (0, 2) in the structure means that displaying

      0   1  2
    'YYYY-MM-DD' is allowed.

    Example:

    >>> w = (1226909090, 1226959090)
    >>> format_timestamp = TimeStampFormatter(structure=s,timeframe=w)

    >>> assert format_timestamp(w[0]) == '08:04:50'

    which is the '(3, 5)' segment that matched best

    >>> assert format_timestamp(w[1]) == '21:58:10'
    >>> assert format_timestamp(1226919090) == '10:51:30'

    >>> w=(120000000,1300000000)
    >>> format_timestamp = TimeStampFormatter(structure=s,timeframe=w)

    >>> assert format_timestamp(w[0]) == '1973-10-20'
    >>> assert format_timestamp(w[1]) == '2011-03-13'
    >>> assert format_timestamp(1290000000) == '2010-11-17'

    >>> w=(123000000,124000000)
    >>> format_timestamp = TimeStampFormatter(structure=s,timeframe=w)

    >>> assert format_timestamp(w[0]) == '11-24 14:40'
    >>> assert format_timestamp(w[1]) == '12-06 04:26'

    >>> assert format_timestamp(123500000) == '11-30 09:33'

    Exceptions
    ~~~~~~~~~~

    >>> format_timestamp(1290000000)
    Traceback (most recent call last):
    ...
    ValueError: ...

    >>> format_timestamp = TimeStampFormatter(structure=s,
    ...    timeframe=(123500000,123500000))
    ...
    >>> format_timestamp(123500000)
    Traceback (most recent call last):
    ...
    ValueError: ...

    >>> format_timestamp = TimeStampFormatter(structure=s,
    ...    timeframe=(123500001,123500000))
    ...
    >>> format_timestamp(123500000)
    Traceback (most recent call last):
    ...
    ValueError: ...

    """

    def format(self, value, context=None):

        dt = sact.epoch.Time.fromtimestamp(value)

        if 'timeframe' not in context:
            return unicode(dt.short)

        first, last = context['timeframe']
        # raises TypeError if not castable:
        first, last = int(first), int(last)

        if not first <= last:
            raise ValueError("timeframe has lower bound greater than "
                             "its greated bound (%d, %d)" % (first, last))

        if not first <= value <= last:
            raise ValueError("value %d is not in provided time "
                             "window (%d, %d)" % (value, first, last))

        first = sact.epoch.Time.fromtimestamp(first).short
        last = sact.epoch.Time.fromtimestamp(last).short

        # find index of first char that differs is ``first`` and ``last``
        diff = False
        i = 0
        for i, c in enumerate(first):
            if c != last[i]:
                diff = True
                break
        if not diff:
            raise ValueError("Time frame cannot be equal "
                             "to the second (%d, %d)"
                             % context['timeframe'])

        # uniformize separation char
        last = last.replace("-", " ").replace(":", " ")
        last_tuple = last.split(' ')

        # now get the index of the previous non-digit char
        cpt = 0
        for cpt in range(i):
            char = last[i - 1 - cpt]
            if char == u' ':
                break

        # next char should be our first index
        start_from = i - cpt
        cutlist = last[start_from:].split(' ')
        first_elmt = 6 - len(cutlist)

        # finds the smallest format that contains first_elmt
        candidates = [(lmin, lmax) for lmin, lmax in context['structure']
                      if lmin <= first_elmt <= lmax]

        # take the one having the best precision
        best_lmax = 0
        for lmin, lmax in candidates:
            if lmax > best_lmax:
                best_lmax = lmax

        # filter out candidates that have not lmax = best_lmax
        candidates = [(lmin, lmax) for lmin, lmax in candidates
                      if lmax == best_lmax]

        # get the smallest
        smallest = None
        smallest_size = 7
        for lmin, lmax in candidates:
            if (lmax - lmin) < smallest_size:
                smallest_size = lmax - lmin
                smallest = (lmin, lmax)
        lmin, lmax = smallest
        # get index in iso string of start and end
        if lmin == 0:
            start_from = 0
        else:
            start_from = len(' '.join(last_tuple[0:lmin])) + 1
        end_at = len(' '.join(last_tuple[0:lmax + 1]))

        # final cut !
        return unicode(dt.isoformat(" ")[start_from:end_at])


class FancyNumberFormatter(Formatter):
    """Fancy number formatter factory.

    This Formatter uses a specific structure to format numbers that
    allows differents type of formatting base on variable scales...

    Sample::

    >>> from __future__ import print_function

    >>> formatter = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ...    (10**3,     1, (u'< 1 ms'                , {} )),
    ...    (10**3, 10**3, (u'%(ms)d ms'             , {'ms': 1,} )),
    ...    (60   , 10**3, (u'%(sec).1f s'           , {'sec': 1,} )),
    ...    (60   ,     1, (u'%(min)d m %(sec)d s'   , {'min': 60, 'sec':1,} )),
    ...    (24   ,    60, (u'%(hour)d h %(min)d m'  , {'hour': 60, 'min':1,} )),
    ...    (None ,    60, (u'%(day)d d %(hour)d h'  , {'day': 24, 'hour':1,} )),
    ... ))
    ...

    Build a new Formatter:
    ----------------------

    The given structure must be a list of (limit,base,format) tuples.

    Limit
    ^^^^^

    Each tuple defines a way to display the value. The first value of
    the tuple (called limit) triggers the choice of the tuple used to
    display the value :

    >>> formatter = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ...    (    2,     1, (u'A' ,  {} )),
    ...    (    3,     1, (u'B' ,  {} )),
    ...    ( None,     1, (u'C' ,  {} )),
    ... ))
    ...

    You can see that limit will trigger a particular line depending
    on the limit parameter... each new limit parameter is multiplied
    by the preceding.

    So in our example, the first line applies when the value is below
    '2', the next line will apply between 2 < v <= 2*3. And the third
    line will apply with no limit on 2*3 < v.

    So:

    >>> for i in range(10): print('%d => %s' % (i,formatter(i)))
    0 => A
    1 => A
    2 => B
    3 => B
    4 => B
    5 => B
    6 => C
    7 => C
    8 => C
    9 => C

    Base
    ^^^^

    The second parameter in each tuples defines the base 'resolution'
    accessible through the format :

    >>> formatter = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ...    (   2,     1, (u'%(value)d single'  ,  {'value': 1} )),
    ...    (   2,     2, (u'%(value)d duo'     ,  {'value': 1} )),
    ...    (None,     2, (u'%(value)d quartet' ,  {'value': 1} )),
    ... ))
    ...

    This means, on first couple, that between 0 <= v <= 2, v/1 will
    be sent to the 'format' structure.
    On second tuple, that displays our value between 2 < v <= 2*2, v/2 will
    be sent to the 'format' structure. And at last:
    On last tuple, that displays our value for 2*2 < v , v/(2*2) will
    be sent to the 'format' structure.

    So::

    >>> for i in range(10): print('%d => %s' % (i,formatter(i)))
    0 => 0 single
    1 => 1 single
    2 => 1 duo
    3 => 1 duo
    4 => 1 quartet
    5 => 1 quartet
    6 => 1 quartet
    7 => 1 quartet
    8 => 2 quartet
    9 => 2 quartet

    Format
    ^^^^^^

    format will take care of displaying the value. It only receive the
    the 'based' value !

    >>> formatter = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ...    (   2,     1, (u'%(value)d single'                   , {'value': 1})),
    ...    (   2,     1, (u'%(value_1)d duo %(value_2)d single' , {'value_1': 2, 'value_2': 1})),
    ...    (None,     2, (u'%(value_1)d quartet %(value_2)d duo', {'value_1': 2, 'value_2': 1})),
    ... ))

    the format is a list of couple: each couple contains a formatting string,
    and a reduction value. The reduction value applies to the base.

    So::

    >>> for i in range(10): print('%d => %s' % (i,formatter(i)))
    0 => 0 single
    1 => 1 single
    2 => 1 duo 0 single
    3 => 1 duo 1 single
    4 => 1 quartet 0 duo
    5 => 1 quartet 0 duo
    6 => 1 quartet 1 duo
    7 => 1 quartet 1 duo
    8 => 2 quartet 0 duo
    9 => 2 quartet 0 duo

    Please note that black magic is in action. Let's explicit that: keys in the dict that provides
    the scales (here {'value_1': 2, 'value_2': 1}) does not provide order information ! Order of
    scales is alphabetical by default. If you want another order, you can specify a tuple of ordered
    scale keys as third part of the structure

    >>> formatter = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ...    (   2,     1, (u'%(value)d single'                   , {'value': 1})),
    ...    (   2,     1, (u'%(value_2)d duo %(value_1)d single' , {'value_2': 2, 'value_1': 1}, ('value_2', 'value_1'))),
    ...    (None,     2, (u'%(value_2)d quartet %(value_1)d duo', {'value_2': 2, 'value_1': 1}, ('value_2', 'value_1'))),
    ... ))

    the format is a list of couple: each couple contains a formatting string,
    and a reduction value. The reduction value applies to the base.

    So::

    >>> for i in range(10): print('%d => %s' % (i,formatter(i)))
    0 => 0 single
    1 => 1 single
    2 => 1 duo 0 single
    3 => 1 duo 1 single
    4 => 1 quartet 0 duo
    5 => 1 quartet 0 duo
    6 => 1 quartet 1 duo
    7 => 1 quartet 1 duo
    8 => 2 quartet 0 duo
    9 => 2 quartet 0 duo

    Generic Example
    ---------------

    >>> format_timedelta = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ...    (10**3,     1, (u'< 1 ms'                        , {} )),
    ...    (10**3, 10**3, (u'%(value)d ms'                  , {'value': 1} )),
    ...    (60   , 10**3, (u'%(value).1f s'                 , {'value': 1} )),
    ...    (60   ,     1, (u'%(value_1)d m %(value_2)d s'   , {'value_1': 60, 'value_2': 1})),
    ...    (24   ,    60, (u'%(value_1)d h %(value_2)d m'   , {'value_1': 60, 'value_2': 1})),
    ...    (None ,    60, (u'%(value_1)d d %(value_2)d h'   , {'value_1': 24, 'value_2': 1})),
    ... ))


    >>> assert format_timedelta(2500 * 10**3 * 60 * 60 * 24)      == '2 d 12 h'
    >>> assert format_timedelta(2500 * 10**3 * 60 * 60 * 24 * 10) == '25 d 0 h'
    >>> assert format_timedelta(2500)                   == '2 ms'
    >>> assert format_timedelta(2500 * 10**3)           == '2.5 s'
    >>> assert format_timedelta(2500 * 10**3 * 60)      == '2 m 30 s'
    >>> assert format_timedelta(2500 * 10**3 * 60 * 60) == '2 h 30 m'
    >>> assert format_timedelta(1226929090)             == '20 m 26 s'
    >>> assert format_timedelta(800)                    == '< 1 ms'

    >>> format_timedelta = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ...    (10**3,     1, ('%(value)d microsecs',    {'value': 1})),
    ...    (10**3, 10**3, ('%(value)d ms'      ,     {'value': 1})),
    ...    (60   , 10**3, ('%(value).1f s'     ,     {'value': 1})),
    ...    (60   ,     1, ('%(value_1)d m %(value_2)d s'  , {'value_1': 60, 'value_2': 1})),
    ...    (24   ,    60, ('%(value_1)d h %(value_2)d m'  , {'value_1': 60, 'value_2': 1})),
    ...    (None ,    60, ('%(value_1)d d %(value_2)d h'  , {'value_1': 24, 'value_2': 1})),
    ... ))
    ...
    >>> assert format_timedelta(800) == '800 microsecs'

    Float support
    -------------

    The first base permit to scale up the displayed value: This sample
    allows to display '80 ms' when you provide 0.08

    >>> format_timedelta = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ... (10**3,10**-6, ('%(value)d microseconds'                      , {'value': 1})),
    ... (10**3, 10**3, ('%(value).2f ms'                              , {'value': 1})),
    ... (60   , 10**3, ('%(value).2f s'                               , {'value': 1})),
    ... (60   ,     1, ('%(value_1)d m %(value_2)d s'                 , {'value_1': 60, 'value_2': 1})),
    ... (24   ,    60, ('%(value_1)d h %(value_2)d m'                 , {'value_1': 60, 'value_2': 1})),
    ... (7    ,    60, ('%(value_1)d wk %(value_2)d d %(value_3)d h'  , {'value_1': 7*24, 'value_2': 24, 'value_3': 1})),
    ... (None ,  24*7, ('%(value_1)d y %(value_2)d wk'                , {'value_1': 52, 'value_2': 1})),
    ... ))
    >>> assert format_timedelta(0.08)  == '80.00 ms'
    >>> assert format_timedelta(0.0008)       == '800 microseconds'

    Exception
    ---------

    You must provide a 'None' value as last limit in the formatting
    structure. If you forget it, an exception should raise::

    >>> format_timedelta = FancyNumberFormatter(structure=(
    ... #   limit    base  format
    ... (10**3,10**-6, (u'%(value)d microseconds', {'value': 1})),
    ... (10**3, 10**3, (u'%(value).2f ms'        , {'value': 1})),
    ... ))

    >>> format_timedelta(832)
    Traceback (most recent call last):
    ...
    TypeError: formatting structure is incorrect

    """

    def format(self, value, context=None):
        value = float(value)  ## generates exception if not castable to a float
        base = value

        def _format(base, format):
            if len(format) == 3:
                msg, scales, order = format
            else:
                msg, scales = format
                order = sorted(scales.keys())

            values = {}
            for key in order:
                values[key] = base / scales[key]
                base %= scales[key]

            msg = context['trans'](msg)
            return msg % (values)

        try:
            value /= context['structure'][0][1]

            for limit, factor, fmt in context['structure']:
                base = float(base) / factor
                if not limit or 0 <= value < limit:
                    return _format(base, fmt)
                value = float(value) / limit

            raise TypeError  ## raise error

        except TypeError:
            raise TypeError("formatting structure is incorrect")


class LogNumberFormatter(Formatter):
    """Logarithmic number formatter factory.

    This Formatter uses a specific structure to format numbers on
    a logarithmique basis. Typically, you should use this to suffix
    numbers depending on a fixed scale : (ie: 1000 is a fixed scale
    for lots of units, and 'K' is the common suffix, 'M' the next,
    ...)

    Result of the Formatter will be a couple of unicode strings: the
    value, and the unit.

    Let's show this thru a simple byte formatter::

    >>> format_size = LogNumberFormatter(
    ...   units=(["B", "KiB", "MiB", "GiB", "TiB"], 2**10))

    Notice that 2**10 == 1024 which is the base for the calcul in we
    want true Bytes::

    >>> assert format_size(0)          == ('0', 'B')
    >>> assert format_size(1024)       == ('1.0', 'KiB')
    >>> assert format_size(1024**4)    == ('1.0', 'TiB')
    >>> assert format_size(1024**4)    == ('1.0', 'TiB')
    >>> assert format_size(1024**2.5)  == ('32.0', 'MiB')

    Precision
    ---------

    number after the period and rounding policies (to the nearest)

    >>> assert format_size(1500) == ('1.5', 'KiB')  ## 1500/1024 = 1.46

    Note that :

    >>> assert format_size(2047) == ('2.0', 'KiB')  ## 1.999 KiB

    Even with the default precision of 1, the size should not be
    written with a trailing ".0"

    >>> assert format_size(35) == ('35', 'B')

    >>> format_size = LogNumberFormatter(
    ...   units=([u"B", u"KiB", u"MiB", u"GiB", u"TiB"], 2**10),
    ...   precision=6
    ...   )
    ...

    >>> assert format_size(2366) == ('2.311', 'KiB')

    Number over the scale
    ---------------------

    Big numbers over the scale are written in the last unit specified
    in the scale:

    >>> format_size = LogNumberFormatter(
    ...   units=([u"B", u"KiB", u"MiB", u"GiB", u"TiB"], 2**10))

    >>> assert format_size(1024**6) == ('1048576.0', 'TiB')

    Internationalisation
    --------------------

    We can use the factory to create the international formatting function
    that will use 1000 as scale factor and "KB" instead of "KiB"

    >>> format_size = LogNumberFormatter(
    ...   units=([u"B", u"KB", u"MB", u"GB", u"TB"], 10**3))

    >>> assert format_size(5000) == ('5.0', 'KB')
    >>> assert format_size(234) == ('234', 'B')

    Exceptions
    ----------

    >>> format_size = LogNumberFormatter(
    ...   units=([u"B", u"KB", u"MB", u"GB", u"TB"], 10**3),
    ...   precision='s'
    ... )
    ...
    >>> format_size(234)
    Traceback (most recent call last):
    ...
    ValueError: ...
    >>> format_size = LogNumberFormatter(
    ...   units=([u"B", u"KB", u"MB", u"GB", u"TB"], 10**3))
    ...
    >>> format_size('s')
    Traceback (most recent call last):
    ...
    ValueError: ...
    >>> format_size = LogNumberFormatter(
    ...   units=([u"B", u"KB", u"MB", u"GB", u"TB"], 10**3),
    ...   precision='-5'
    ... )
    ...
    >>> format_size(234)
    Traceback (most recent call last):
    ...
    ValueError: ...


    """

    def format(self, value, context=None):
        precision = int(context.get('precision', 1))

        ## generates exception if not integer
        value = int(value)

        if precision < 0:
            raise ValueError("Negative precision '%d' is not coherent."
                             % precision)

        def _format(value, suffix, precision, auth_prec):
            """Takes care of the final formatting ..."""
            prec = min(auth_prec, precision)
            if prec == 0:
                format_string = u"%i"
            else:
                format_string = u"%." + str(prec) + "f"
            return (format_string % value, suffix)

        suffixes, factor = context['units']

        ## raise error if suffixes is not iterable
        iter(suffixes)

        auth_prec = 0
        suffix = u''  ## default value if suffixes is empty
        for suffix in suffixes:
            if 0 <= value < factor:
                return _format(value, suffix, precision, auth_prec)

            last_value = value  ## keep in case of last loop
            value = float(value) / factor
            auth_prec += int(math.log(factor, 10))

        return _format(last_value, suffix, precision, auth_prec)


class PercentFormatter(Formatter):
    """Percent number formatter

    Convert a number (float or int) in pourcentage. Or what you want if you
    give the precision number. Percent, per thousand ...

        >>> perNumber = PercentFormatter()
        >>> perNumber(0.2)
        20.0
        >>> perNumber(-1)
        -100
        >>> perNumber(5)
        500

    We can specify the precision. For exemple if you want a per thousand value

        >>> perNumber = PercentFormatter(precision=1000)
        >>> perNumber(0.2)
        200.0
        >>> perNumber(-1)
        -1000
        >>> perNumber(5)
        5000

        >>> perNumber('e')
        Traceback (most recent call last):
        ...
        ValueError: Need an integer or float value.

    """

    def format(self, value, context=None):
        precision = int(context.get('precision', 100))
        if isinstance(value, int) or isinstance(value, float):
            return value * precision
        raise ValueError("Need an integer or float value.")


def mk_fmt(fun):


    class _Formatter(Formatter):

        def format(self, value, context=None):
            return fun(value, context)

    return _Formatter

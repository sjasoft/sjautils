from itertools import *
import collections
import operator
import math, functools


def sumprod(it1, it2):
    return sum(math.prod(z) for z in zip(it1, it2))

class take_only_while(object):
  """
  Provides a wrapped iterator for iterative yielding
  of items until predicate is false but leaving underlying iterator
  with the failing item as its next item
  """
  def __init__(self,pred, iterator):
    self._pred = pred
    self._iter = iterator

  def __iter__(self):
    return self

  def next(self):
    item = self._iter.next()
    if self._pred(item):
      return item
    else:
      self._item = chain([item], self._iter)
      raise StopIteration

  def __next__(self):
      return self.next()
  
  @property
  def the_rest(self):
    return self._rest 

def split_true_false(pred, iterable):
    it1, it2 = tee(iterable, 2)
    true = (i for i in it1 if pred(i))
    false = (i for i in it2 if not pred(i))
    return true, false

def cons(x, iterable):
      return chain([x], iterable)

def consing_split(pred, iterable):
      true = chain([])
      false = chain([])
      for i in iterable:
          if pred(i):
                true = cons(i, true)
          else:
                false = cons(i, false)
      return true, false

def take_n(n, iterable):
    return islice(iterable, n)


def take_while(pred, iterable):
    return takewhile(pred, iterable)

def while_satisfying(pred, iterable):
    return takewhile(pred, iterable)

def satisfying(pred, iterable):
    return (p for p in iterable if pred(p))

def all_satisfy(pred, iterable):
      for i in iterable:
            if not pred(i):
                  return False
      return True

def while_le(value, iterable):
      return satisfying(lambda x: x <= value, iterable)

def not_pred(pred):
    return lambda x: not pred(x)

def not_satisfying(pred, iterable):
    return satisfying(not_pred(pred), iterable)

def while_not_satisfying(pred, iterable):
    return while_satisfying(not_pred(pred), iterable)

def test_take_while():
    data = [1] + list(range(2, 12, 2))
    test_odd = lambda x: x % 2
    test_even = lambda x: not (x % 2)
    res_even = list(take_while(test_even, (x for x in data)))
    print(res_even)
    assert res_even == data
    res_odd = list(take_while(test_odd, (x for x in data)))
    assert not res_odd

# The following are formulas from python docs

def take(n, iterable):
    "Return first n items of the iterable as a list."
    return list(islice(iterable, n))

def prepend(value, iterable):
    "Prepend a single value in front of an iterable."
    # prepend(1, [2, 3, 4]) --> 1 2 3 4
    return chain([value], iterable)

def tabulate(function, start=0):
    "Return function(0), function(1), ..."
    return map(function, count(start))

def repeatfunc(func, times=None, *args):
    """Repeat calls to func with specified arguments.

    Example:  repeatfunc(random.random)
    """
    if times is None:
        return starmap(func, repeat(args))
    return starmap(func, repeat(args, times))

def flatten(list_of_lists):
    "Flatten one level of nesting."
    return chain.from_iterable(list_of_lists)

def ncycles(iterable, n):
    "Returns the sequence elements n times."
    return chain.from_iterable(repeat(tuple(iterable), n))

def tail(n, iterable):
    "Return an iterator over the last n items."
    # tail(3, 'ABCDEFG') --> E F G
    return iter(collections.deque(iterable, maxlen=n))

def consume(iterator, n=None):
    "Advance the iterator n-steps ahead. If n is None, consume entirely."
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)

def nth(iterable, n, default=None):
    "Returns the nth item or a default value."
    return next(islice(iterable, n, None), default)

def quantify(iterable, pred=bool):
    "Given a predicate that returns True or False, count the True results."
    return sum(map(pred, iterable))

def all_equal(iterable):
    "Returns True if all the elements are equal to each other."
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def first_true(iterable, default=False, pred=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)

def unique_everseen(iterable, key=None):
    "List unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBcCAD', str.casefold) --> A B c D
    seen = set()
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen.add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen.add(k)
                yield element

def unique_justseen(iterable, key=None):
    "List unique elements, preserving order. Remember only the element just seen."
    # unique_justseen('AAAABBBCCDAABBB') --> A B C D A B
    # unique_justseen('ABBcCAD', str.casefold) --> A B c A D
    if key is None:
        return map(operator.itemgetter(0), groupby(iterable))
    return map(next, map(operator.itemgetter(1), groupby(iterable, key)))

def iter_index(iterable, value, start=0, stop=None):
    "Return indices where a value occurs in a sequence or iterable."
    # iter_index('AABCADEAF', 'A') --> 0 1 4 7
    seq_index = getattr(iterable, 'index', None)
    if seq_index is None:
        # Slow path for general iterables
        it = islice(iterable, start, stop)
        for i, element in enumerate(it, start):
            if element is value or element == value:
                yield i
    else:
        # Fast path for sequences
        stop = len(iterable) if stop is None else stop
        i = start - 1
        try:
            while True:
                yield (i := seq_index(value, i+1, stop))
        except ValueError:
            pass

def sliding_window(iterable, n):
    "Collect data into overlapping fixed-length chunks or blocks."
    # sliding_window('ABCDEFG', 4) --> ABCD BCDE CDEF DEFG
    it = iter(iterable)
    window = collections.deque(islice(it, n-1), maxlen=n)
    for x in it:
        window.append(x)
        yield tuple(window)

def grouper(iterable, n, *, incomplete='fill', fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks."
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    match incomplete:
        case 'fill':
            return zip_longest(*args, fillvalue=fillvalue)
        case 'strict':
            return zip(*args, strict=True)
        case 'ignore':
            return zip(*args)
        case _:
            raise ValueError('Expected fill, strict, or ignore')

def roundrobin(*iterables):
    "Visit input iterables in a cycle until each is exhausted."
    # roundrobin('ABC', 'D', 'EF') --> A D E B F C
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))

def partition(pred, iterable):
    """Partition entries into false entries and true entries.

    If *pred* is slow, consider wrapping it with functools.lru_cache().
    """
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)

def subslices(seq):
    "Return all contiguous non-empty subslices of a sequence."
    # subslices('ABCD') --> A AB ABC ABCD B BC BCD C CD D
    slices = starmap(slice, combinations(range(len(seq) + 1), 2))
    return map(operator.getitem, repeat(seq), slices)

def iter_except(func, exception, first=None):
    """ Call a function repeatedly until an exception is raised.

    Converts a call-until-exception interface to an iterator interface.
    Like builtins.iter(func, sentinel) but uses an exception instead
    of a sentinel to end the loop.

    Priority queue iterator:
        iter_except(functools.partial(heappop, h), IndexError)

    Non-blocking dictionary iterator:
        iter_except(d.popitem, KeyError)

    Non-blocking deque iterator:
        iter_except(d.popleft, IndexError)

    Non-blocking iterator over a producer Queue:
        iter_except(q.get_nowait, Queue.Empty)

    Non-blocking set iterator:
        iter_except(s.pop, KeyError)

    """
    try:
        if first is not None:
            # For database APIs needing an initial call to db.first()
            yield first()
        while True:
            yield func()
    except exception:
        pass

def before_and_after(predicate, it):
    """ Variant of takewhile() that allows complete
        access to the remainder of the iterator.

        >>> it = iter('ABCdEfGhI')
        >>> all_upper, remainder = before_and_after(str.isupper, it)
        >>> ''.join(all_upper)
        'ABC'
        >>> ''.join(remainder)     # takewhile() would lose the 'd'
        'dEfGhI'

        Note that the true iterator must be fully consumed
        before the remainder iterator can generate valid results.
    """
    it = iter(it)
    transition = []

    def true_iterator():
        for elem in it:
            if predicate(elem):
                yield elem
            else:
                transition.append(elem)
                return

    return true_iterator(), chain(transition, it)

#The following recipes have a more mathematical flavor:

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def sum_of_squares(it):
    "Add up the squares of the input values."
    # sum_of_squares([10, 20, 30]) -> 1400
    return math.sumprod(*tee(it))

def reshape(matrix, cols):
    "Reshape a 2-D matrix to have a given number of columns."
    # reshape([(0, 1), (2, 3), (4, 5)], 3) -->  (0, 1, 2), (3, 4, 5)
    return batched(chain.from_iterable(matrix), cols)

def transpose(matrix):
    "Swap the rows and columns of a 2-D matrix."
    # transpose([(1, 2, 3), (11, 22, 33)]) --> (1, 11) (2, 22) (3, 33)
    return zip(*matrix, strict=True)

def matmul(m1, m2):
    "Multiply two matrices."
    # matmul([(7, 5), (3, 5)], [(2, 5), (7, 9)]) --> (49, 80), (41, 60)
    n = len(m2[0])
    return batched(starmap(math.sumprod, product(m1, transpose(m2))), n)

def convolve(signal, kernel):
    """Discrete linear convolution of two iterables.

    The kernel is fully consumed before the calculations begin.
    The signal is consumed lazily and can be infinite.

    Convolutions are mathematically commutative.
    If the signal and kernel are swapped,
    the output will be the same.

    Article:  https://betterexplained.com/articles/intuitive-convolution/
    Video:    https://www.youtube.com/watch?v=KuXjwB4LzSA
    """
    # convolve(data, [0.25, 0.25, 0.25, 0.25]) --> Moving average (blur)
    # convolve(data, [1/2, 0, -1/2]) --> 1st derivative estimate
    # convolve(data, [1, -2, 1]) --> 2nd derivative estimate
    kernel = tuple(kernel)[::-1]
    n = len(kernel)
    padded_signal = chain(repeat(0, n-1), signal, repeat(0, n-1))
    windowed_signal = sliding_window(padded_signal, n)
    return map(math.sumprod, repeat(kernel), windowed_signal)

def polynomial_from_roots(roots):
    """Compute a polynomial's coefficients from its roots.

       (x - 5) (x + 4) (x - 3)  expands to:   x³ -4x² -17x + 60
    """
    # polynomial_from_roots([5, -4, 3]) --> [1, -4, -17, 60]
    factors = zip(repeat(1), map(operator.neg, roots))
    return list(functools.reduce(convolve, factors, [1]))

def polynomial_eval(coefficients, x):
    """Evaluate a polynomial at a specific value.

    Computes with better numeric stability than Horner's method.
    """
    # Evaluate x³ -4x² -17x + 60 at x = 2.5
    # polynomial_eval([1, -4, -17, 60], x=2.5) --> 8.125
    n = len(coefficients)
    if not n:
        return type(x)(0)
    powers = map(pow, repeat(x), reversed(range(n)))
    return sumprod(coefficients, powers)

def polynomial_derivative(coefficients):
    """Compute the first derivative of a polynomial.

       f(x)  =  x³ -4x² -17x + 60
       f'(x) = 3x² -8x  -17
    """
    # polynomial_derivative([1, -4, -17, 60]) -> [3, -8, -17]
    n = len(coefficients)
    powers = reversed(range(1, n))
    return list(map(operator.mul, coefficients, powers))

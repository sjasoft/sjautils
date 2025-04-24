from decimal import Decimal
from functools import reduce, wraps
import logging
from contextlib import contextmanager
import re, time
import os, types
import asyncio
import uuid

def snake_to_camel_case(s, first_cap=False):
    parts = s.split('_')
    first = parts[0].capitalize() if first_cap else parts[0]
    rest = [p.capitalize() for p in parts[1:]]
    parts = [first] + rest
    return ''.join(parts)



def bytesToString(val):
    return val.decode('utf-8') if isinstance(val, bytes) else val


def safe_next(some_generator):
    try:
        return next(some_generator)
    except Exception as e:
        return None


@contextmanager
def in_directory(path):
    '''
    Used with 'with' block executes within the given directory and then returns to original directory.
    Basically a pushd/popd wrapper.
    :param path: path to execute within.
    :return:
    '''
    current = os.path.abspath('.')
    target = os.path.abspath(path)
    changed = target != current
    if changed:
        os.chdir(path)
    yield
    if changed:
        os.chdir(current)


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


# without this next line setLevel will be ignored
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    return logger


logger = get_logger()


def dataframe_sum(df, *fields):
    if fields:
        return df.groupby(fields).agg('sgum').to_dict(orient='records')
    else:
        return df.drop(columns='calendar_day').sum().to_dict()


# many aws functions deliver in chunks with some result indicator of more. next two functions
# are for specifying the key to provide the next indicator with and what the next_indicator
# field is
def symmetric_next(next_name):
    return (next_name, lambda r: r.get(next_name))


def asymmetric_next(next_name, next_indicator_name):
    return (next_name, lambda r: r.get(next_indicator_name))


def get_all(fn, next_chunk_extractor, data_field, **kwargs):
    '''
    Return a generator over all items returned by given function where the function
    may return items in chunks with some next indicator for more data available.
    :param fn: the function to execute repeatedly until no more data
    :param next_churk_extractor: 2-tuple of key for indicating to the function to return next chunk and
      function for getting next chunk value from current chunk
    :param data_field: key in chunk of the payload items return by fun
    :param kwargs: arguments to the function that are repeated per invocation
    :return generator over all items returned by fn
    '''
    next_key, next_val_fn = next_chunk_extractor
    res = fn(**kwargs)
    while True:
        items = res.get(data_field, [])
        for item in items:
            yield item
        next_val = next_val_fn(res)
        if next_val:
            res = fn(**kwargs, **{next_key: next_val})
        else:
            break


def fixed_sleep_wait(fn, success_test, failed_test, seconds):
    '''
    Executes a function retrieving status of something that takes some time and
    retries for fixed number of seconds returning True if success was finally indicated
    and False if failure was finally indicated.  Really just another way of doing a
    promise style pattern but more synchronously.
    :param fn: status checking function to run
    :param success_test: fn to tests for success from status checking function
    :param failed_test: fn to tests for failure from status checking function
    :param seconds: how many seconds to wait before checking again
    :return True,None if success, False,response if failure.

    NOTE: will hang forever if neither success_test or failed_test is ever satisfied or fn hangs.
    '''
    while True:
        res = fn()
        if success_test(res):
            return True, None
        if failed_test(res):
            return False, res
        time.sleep(seconds)


def group_by(size, sequence):
    '''
    Grouping generator from any sequence including another generator
    :param size: max size of returned group.
    :param sequence: sequence to generate sized groups for
    :return: yields groups of the given size until sequence is exhausted or no longer asked for next group
    '''
    group = []
    for item in sequence:
        group.append(item)
        if len(group) == size:
            yield group
            group = []
    if group:
        yield group

def filter_until_failure(sequence, test):
    for item in sequence:
        if test(item):
            yield item
        else:
            break

def gen_filter(sequence, test, stop_on_fail=False):
    """
    Filters a sequence of items to only those that pass a test.
    Optionally short circuits after first failure.  This is good
    in cases of filtering an ordered sequence testing on the ordering
    field[s]
    :param sequence: sequence of items to filter
    :param test: test to filter with
    :param stop_on_fail: whether to stop on first failure
    :return: returns a list if sequence is a list otherwise a generator
    """
    is_list = isinstance(sequence, list)
    if stop_on_fail:
        generator = filter_until_failure(sequence, test)
    else:
        generator = (g for g in sequence if test(g))
    return list(generator) if is_list else generator


def equality_filter(generator, **field_values):
    def test(item):
        return all([(item.get(k) == v) for k, v in field_values.items()])

    return gen_filter(generator, test)


def walkup(start):
    param = start[:-1] if start.endswith('/') else start
    if not param:
        return None
    return os.path.dirname(param)


def get_or_default(src, field, default):
    val = src.get(field)
    if val is None:
        return default
    return val


def walk_up_find(to_find, start='.'):
    start = os.path.abspath(start)
    if not os.path.isdir(start):
        start = os.path.dirname(start)
    while start and not os.path.exists(os.path.join(start, to_find)):
        start = walkup(start)
    return os.path.join(start, to_find) if start else None




def generate_unique_id():
    """
    Use the uuid4 function to generate a unique id. Follows pattern in play before of uuid with '-' separators. Arguably there is 
    no need for those and we could make an even more concise string that might make lookups a tad bit faster 
    for dbs that don't have special GUID handling.  

    :returns: A string which should be considered a unique id
    """

    return str(uuid.uuid4())


def async_wrapper(coro):
    '''
    This decorator allows an asynchronous function wrapped with it to execute synchronously by waiting for
    the event loop to finish with it.  It should be used sparingly and generally only where we are at a logical
    top of a single rooted hierarchy or within a framework that expects non-async functions or methods.
    :param coro: the async or coroutien function being wrapped
    :return: the result of the waited for wrapped function.
    '''

    @wraps(coro)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))

    return wrapper



def value_fixer(value_test, fix):
    '''
    Generalized value fixer
    :param value_test: tests for whether a scalar value needs fixing
    :param fix: function that fixes the value
    :returns: function for fixing the object by these criteria which creats a new fixed object
    '''

    def fix_it(obj):
        if isinstance(obj, dict):
            return {k: fix_it(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [fix_it(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple([fix_it(v) for v in obj])
        elif isinstance(obj, types.GeneratorType):
            return (fix_it(v) for v in obj)
        else:
            return fix(obj) if value_test(obj) else obj

    return fix_it


def value_dropper(drop_test, sentinel=None):
    if sentinel is None:
        sentinel = uuid.uuid4().hex
    to_be_discarded = lambda x: (x == sentinel) or drop_test(x)

    def drop_filtered(obj):
        temp = obj
        if isinstance(obj, dict):
            temp = {k: v for k, v in {k: drop_filtered(v) for k, v in obj.items()}.items() if not to_be_discarded(v)}
        elif isinstance(obj, list) or isinstance(obj, tuple):
            temp = [i for i in [drop_filtered(l) for l in obj] if not to_be_discarded(i)]
            if isinstance(obj, tuple):
                temp = tuple(temp)
        return sentinel if drop_test(temp) else temp

    def drop_bad_values(obj):
        filtered = drop_filtered(obj)
        return None if (filtered == sentinel) else filtered

    return drop_bad_values


def decimal_fix(d):
    return float(d) if (d % 1) else int(d)


def to_decimal(d):
    return Decimal(str(d)) if isinstance(d, float) else d


decimal_fixer = value_fixer(value_test=lambda o: isinstance(o, Decimal), fix=decimal_fix)
decimal_input_fix = value_fixer(value_test=lambda o: isinstance(o, float), fix=to_decimal)
remove_falsey = value_dropper(drop_test=lambda o: o == '')
float_to_int = value_fixer(value_test=lambda o: isinstance(o, float), fix=int)

clear_dict = remove_falsey
remdec = decimal_fixer


def simply_flatten(obj):
    '''
    returns a list of the scalar leaf objects.
    '''
    flat = []

    def flatten(x):
        if isinstance(x, dict):
            for v in x.values():
                flatten(v)
        elif isinstance(x, list) or isinstance(x, tuple):
            for v in x:
                flatten(v)
        else:
            flat.append(x)

    flatten(obj)
    return flat


def drop_word(s, break_fn):
    'drop a word from end of string where break_fn is a tests for word separators'
    index = len(s)
    while break_fn(s[index - 1]):
        index -= 1
    while not break_fn(s[index - 1]):
        index -= 1
    return s[:index]


def word_splitter(s, test):
    in_word = False
    word_start = -1
    res = []
    for i, c in enumerate(s):
        if test(c):
            if in_word:
                res.append(s[word_start: i])
            in_word = False
        else:
            if not in_word:
                in_word = True
                word_start = i
    if in_word:
        res.append(s[word_start:])
    return res


def word_indices(a_string, break_fn):
    words = word_splitter(a_string, break_fn)
    word_locations = []
    begin = 0
    for word in words:
        start = begin + a_string[begin:].index(word)
        end = start + len(word)
        word_locations.append((start, end))
        begin = end
    return word_locations


def max_word_break(a_string, max_length, break_fn):
    '''
    Returns the prefix of a_string less than max_length long preserving whole words as much as
    possible.  Words are considere separated by <space>. if no <space> in a_string return the
    truncated string
    '''

    word_locs = word_indices(a_string, break_fn)
    last = 0
    for _, end in word_locs:
        if end <= max_length:
            last = end
        else:
            break
    return a_string[:last] if last else a_string[:max_length]


def truncate_text(text, length=100, strict=False, elipses=False, quotes=False, removeurls=True, word_break=None):
    word_break = word_break or (lambda c: not c.isalnum())
    if removeurls:
        text = re.sub(r'^https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
    add_elipses = lambda s: s + '...'
    add_quotes = lambda s: '"%s"' % s
    decorations = []
    if elipses:
        decorations.append(add_elipses)
        length -= 3
    if quotes:
        decorations.append(add_quotes)
        length -= 2

    decorated = lambda s: reduce(lambda a, d: d(a), decorations, s)

    if strict:
        return decorated(text[:length])
    else:
        return decorated(max_word_break(text, length, word_break))


def adder_if(target, is_valid=None):
    '''
    Creates and returns a closure which will add a value (at key if target is dict) to target if it is
    valid.
    :param target: the dict, list or set to optionally add to
    :param is_valid: value validity check defaults to not None
    :return: function accepting a value for list and set or a key and value for dict
    '''
    is_valid = is_valid or (lambda v: v is not None)
    dict_add = lambda k, v: target.update({k: v}) if is_valid(v) else None
    list_add = lambda v: target.append(v) if is_valid(v) else None
    set_add = lambda v: target.add(v) if is_valid(v) else None

    if isinstance(target, dict):
        return dict_add
    elif isinstance(target, list):
        return list_add
    elif isinstance(target, set):
        return set_add


def up_dir(n, path):
    res = path
    for _ in range(n):
        res = os.path.dirname(res)
    return res



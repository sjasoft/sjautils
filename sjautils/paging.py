from collections import deque
from sjautils.utils import get_logger
from functools import wraps
import time

logger = get_logger()


def do_all(operation, paging_key, result_key, argument_key=None, **kwargs):
    '''
    Performs some AWS or other paging operation returning successive results
    :param operation: operation function to call
    :param kwargs: general arguments to operation.  Paging information will be added when needed.
    :param paging_key: key of operation result signifying more data
    :param result_key: part of operation response to return as result to caller.
    :param argument_key: optional key to pass to operation for paging if different from paging_key
    :return: generator of items returned
    '''
    if not argument_key:
        argument_key = paging_key
    done = False
    args = dict(kwargs)
    more_data = None
    while not done:
        response = operation(**args)
        for item in response.get(result_key, []):
            yield item
        old_more = more_data
        more_data = response.get(paging_key)
        if more_data and (old_more == more_data):
            raise Exception('paging not working!')
        if more_data:
            args[argument_key] = more_data
        else:
            done = True


def handling_too_many_requests(operation, sleep_amount=1.0):
    """
    Decorator for a fn that will retry if the TooManyRequestsException is thrown
    executing the function
    @param operation: the function wrapped
    @param sleep_amount: number of seconds to sleep
    @return the wrapped operation
    """

    @wraps(operation)
    def retry(*args, **kwargs):
        while True:
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if e.__class__.__name__ == 'TooManyRequestsException':
                    time.sleep(sleep_amount)
                else:
                    raise e

    return retry


def throttled_multi_op(operation, arg_items, always_retry='TooManyRequestsException', retry_exceptions=None,
                       sleep_some=1.0):
    """
    Performs an operation on each of a set of items in the face of possible throttling
    on number of requests in a time period. The most common one in this contexts is the
    TooManyRequestsExceptions thrown by many AWS apis. But others can be specified as well.
    This loops as long as there are items not successfully completed due to a named retriable
    exception being thrown.
    @param operation: the function of one argument to perform
    @param param arg_items: list of items to preform it over
    @param always_retry: error name to always retry
    @param retry_exceptions: names of other exceptions ot always_retry
    @param sleep_some: seconds between retries
    @return None
    """
    retriable_exceptions = [always_retry]
    if retry_exceptions:
        retriable_exceptions += list(retry_exceptions)
    remaining = deque(list(arg_items))
    print('remaining', remaining, len(remaining))
    while remaining:
        item = remaining.pop()
        logger.info('doing %s', item)
        try:
            yield operation(item)
        except Exception as e:
            logger.exception(e)
            if e.__class__.__name__ in retriable_exceptions:
                remaining.append(item)
                if sleep_some:
                    time.sleep(sleep_some)
            else:
                raise e


def composed_filter(gen, *filters):
    '''
    composition of filters in terms of generators although gen argument can all be any sequence.
    composes use of filter functions by refining generator vs af function composition.
    :param gen: generaror or other iternable
    :param filters: set of filter functions
    :return: generator with only items that pass all filters
    '''
    for f in filters:
        gen = (g for g in gen if f(g))
    return gen

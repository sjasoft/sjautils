from om_int_common.web.utils import json_or_error, split_special
import httpx, asyncio
from functools import wraps, partial
from httpx import ConnectError

def connection_retry(fn):
    @wraps(fn)
    async def inner(*args, **kwargs):
        reset_count = [0]
        path = '/'.join([str(a) for a in args[1:]])

        def note_reset():
            reset_count[0] += 1
            print(f'got reset #{reset_count[0]} for {path}')
            return reset_count[0]

        while True:
            try:
                return await fn(*args, **kwargs)
            except ConnectError as _:
                if note_reset() < 3:
                    continue
                raise Exception(f'more than 3 consecutive connection errors on {path}')
    return inner


def throttle_retry(fn):
    throttle_wait = 5
    @wraps(fn)
    async def inner(*args, **kwargs):
        throttle_time = 0
        path = '/'.join([str(a) for a in args[1:]])
        res = await fn(*args, **kwargs)
        while (res is not None) and (res.status_code == 429):
            print(f'throttling {fn.__name__} {path}; throttle:{throttle_wait}, previous: {throttle_time}')
            await asyncio.sleep(throttle_wait)
            throttle_time += throttle_wait
            res = await fn(*args, **kwargs)
        return res
    return inner


def request_call(remainder='json'):
    splitter = partial(split_special, remainder=remainder)
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            response_only, kwargs = splitter(kwargs)
            func = throttle_retry(connection_retry(fn))
            res = await func(*args, **kwargs)
            return res if response_only else json_or_error(res)
        return wrapper
    return decorator

class GenericWebClient:
    def __init__(self, url=None, host='localhost', port='8080', use_session=True, **headers):
        self._client = httpx.AsyncClient()
        self._handler = self._client if use_session else httpx
        self._headers = headers
        if headers:
            self._client.headers = headers
        # self._session.headers.update({'pkm-client': self._client_id, 'content_type': 'application/json'})
        if url:
            self._url_head = '%s/' % url if (not url.endswith('/')) else url
        elif host and port:
            self._url_head = 'http://%s:%s/' % (host, port)
        else:
            raise Exception('either an url or host and port must be specified')

    def make_url(self, *parts):
        return self._url_head + '/'.join(list(parts))

    @request_call('params')
    async def get(self, *path, **params):
        return await self._handler.get(self.make_url(*path), **params)

    @request_call()
    async def post(self, *path, **data):
        return await self._handler.post(self.make_url(*path), **data)

    @request_call()
    async def patch(self, *path, **data):
        return await self._handler.patch(self.make_url(*path), **data)

    @request_call()
    async def put(self, *path, **data):
        return await self._handler.put(self.make_url(*path), **data)

    @request_call()
    async def delete(self, *path, response_only=False, headers=None):
        args = {}
        if response_only:
            args['response_only'] = response_only
        if headers:
            args['headers'] = headers
        print('path', path)
        return await self._handler.delete(self.make_url(*path), **args)

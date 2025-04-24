from zmq.asyncio import Context, ZMQEventLoop
import zmq
from sjautils.string import before,after, split_once
import json

class JSONMessage:
    def decode(self, json_str: str):
        return json.loads(json_str)

    def encode(self, msg, *args, **kwargs):
        return json.dumps(msg)

class PubSubJSON(JSONMessage):
    def decode_label(self, label):
        kind = before(label, ':')
        kind_id = after(label, ':')
        return [kind, kind_id]

    def encode(self, data, kind, kind_id=None):
        label = self.encode_label(kind, kind_id)
        msg = super().encode(data)
        return f'{label}::{msg}'

    def encode_label(self, kind, kind_id=''):
        return f'{kind}:{kind_id}' if kind_id else f'{kind}'

    def decode(self, json_str:str):
        label, data = split_once(json_str, '::')
        kind, kind_id = self.decode_label(label)
        msg = super().decode(data)
        return kind, kind_id, msg

class Publish:
    def __init__(self, port, type, context=None, multi=False):
        self._multi = multi
        self._socket_type = zmq.XPUB if multi else zmq.PUB
        self._addr = f'{type}://*:{port}'
        self._context = context or Context()
        self._socket = None
        self._protocol = PubSubJSON()

    @property
    def socket(self):
        if not self._socket:
            self._socket = self._context.socket(self._socket_type)
            self._socket.connect(self._addr)
        return self._socket

    def publish(self, kind, data, kind_id=None):
        # TODO add proper multi handling if different
        msg = self._protocol.encode(data, kind, kind_id=kind_id)
        self.socket.send(msg)

class Subscribe:
    def __init__(self, port, type, *filters, ip=None, context=None, multi=False):
        self._multi = multi
        self._filters = filters
        if not multi:
            assert ip, f'IP address of pub required if not multi-published'
        self._socket_type = zmq.XSUB if multi else zmq.SUB
        self._addr = f'{type}://*:{port}' if multi else f'{type}://{ip}:{port}'
        self._context = context or Context()
        self._socket = None
        self._protocol = PubSubJSON()

    @property
    def socket(self):
        if not self._socket:
            self._socket = self._context.socket(self._socket_type)
            for filter in self._filters: \
                    self._socket.setsockopt(zmq.SUBSCRIBE, filter)

            self._socket.connect(self._addr)
        return self._socket

    async def receive(self):
        msg = await self._socket.recv()
        return self._protocol.decode(msg)

    async def subscription_loop(self, process_fn):
        while True:
            kind, kind_id, data = await self.receive()
            await process_fn(kind, kind_id, data)

class Server:
    def __init__(self, port, context=None, type='tcp'):
        self._context = context or Context()
        self._addr = f'{type}://*:{port}'
        self._socket = None
        self._protocol = JSONMessage()

    @property
    def socket(self):
        if not self._socket:
            self._socket = self._context.socket(zmq.REP)
            self._socket.bind(self._addr)
        return self._socket

    def reply(self, data):
        self.socket.send_string(self._protocol.encode(data))

    def return_exception(self, exception):
        data = dict(
            exceptions = [str(exception)]
        )
        self.reply(data)

    async def receive(self):
        msg = await(self.socket.recv())
        return self._protocol.decode(msg)

class ServerLoop(Server):
    pass

class Client:
    def __init__(self, port, ip='localhost', context=None, type='tcp'):
        self._context = context or Context()
        self._addr = f'{type}://{ip}:{port}'
        self._socket = None
        self._protocol = JSONMessage()

    @property
    def socket(self):
        if not self._socket:
            self._socket = self._context.socket(zmq.REQ)
            self._socket.connect(self._addr)
        return self._socket

    async def call(self, fn_name, *args, **kwargs):
        self.send(dict(function=fn_name, args=args,
                       kwargs=kwargs))
        return await self.receive()

    def send(self, data):
        self.socket.send_string(self._protocol.encode(data))

    async def receive(self):
        msg = await(self.socket.recv())
        return self._protocol.decode(msg)

class RPCServer(Server):
    def __init__(self, port, target, ip='localhost'):
        super().__init__(port, ip=ip)
        self._target = target

    def __call__(self, fn_name, *args, **kwargs):
        fn = (getattr(self, fn_name, None) or
              getattr(self._target, fn_name, None))
        if not fn:
            raise Exception(f'unknown function {fn_name}')
        try:
            result = fn(*args, **kwargs)
            self.reply(result)
        except Exception as e:
            self.return_exception(e)

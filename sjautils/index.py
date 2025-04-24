import random
from sjautils import radix

def make_id(nbits):
    num = random.getrandbits(nbits)
    attempt = radix.to_str(num, 62)
    return ('z' + attempt) if attempt[0].isdigit() else attempt

def decode_id(an_id):
    return radix.decode_id(an_id, 62)

class Index:
    """This class generates base 64 encoded strings from a random number of bits."""

    by_name = {}

    @classmethod
    def named(cls, name):
        cls.by_name.get(name)

    def __init__(self, name, bits=32):
        self._name = name
        self._bit_count = bits
        self.__class__.by_name[name] = self

    def next(self):
        return make_id(self._bit_count)


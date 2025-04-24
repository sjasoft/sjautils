from collections import defaultdict
import random, re, os
import validators
import subprocess as sub
from functools import reduce

def pass_fail(items, test):
  passed = [], failed = []
  for item in items:
    ctx = passed if test(item) else failed
    ctx.append(item)
  return passed, failed

def to_list(aDict):
  '''
  Convert nested dict with list and dict values to nested list.  Originally used as alternate
  parsing of a UOP query dict representation. 
  '''
  raw = list(aDict.items())
  res = []
  for k,v in raw:
    res.append(k)
    if isinstance(v, list):
      res.append([to_list(item) for item in v])
    elif isinstance(v, dict):
      res.append(to_list(v))
    else:
      res.append(v)
  return res

class ByNameId:
  '''
  Provides by name and by id maps for dict like items that have both 'name' and '_id' fields
  '''
  def __init__(self, uses_name=True):
    self._id_map = {}
    self._name_map = {}
    self._uses_name = uses_name

  def id_map(self):
    return dict(self._id_map)

  def name_map(self):
    return dict(self._name_map)

  def values(self):
    return self._id_map.values()

  def add_item(self, item):
    self._id_map[item['_id']] = item
    if self._uses_name:
      self._name_map[item['name']] = item

  def with_id(self, an_id):
    return self._id_map.get(an_id)

  def with_name(self, name):
    return self._name_map.get(name)

  def random_instance(self):
    vals = list(self._id_map.values())
    index = random.randint(0, len(vals)-1)
    return vals[index] if vals else None


def as_list(fn, *args, **kwargs):
  """because python3 made way two many things generators and/or special objects"""
  return list(fn(*args, **kwargs))

def lmap(fn, *iterables):
  return as_list(map, fn, *iterables)


def set_and(fn, values):
  res = fn(values[0])
  for v in values[1:]:
    res_v = fn(v)
    res = res & res_v
    if not res:
      break
  return res

def set_or(fn, values):
  return reduce(lambda a, b: a | b, map(fn, values), set())


def match_fields(pat, aString, *fields):


    match = re.search(pat, aString)
    data = match.groupdict() if match else None
    return [data.get(f, None) for f in fields] if data else [None for _ in fields]

def sub_pipes(*pipes):
    return {p: sub.PIPE for p in pipes}
    
standard_pipes = sub_pipes('stdin', 'stdout', 'stderr')

def bytesToString(val):
  return val.decode('utf-8') if isinstance(val, bytes) else val

def without_output(cmd):
  with open(os.devnull, 'a') as out:
    sub.Popen(cmd, shell=True, stdout=out, stderr=out)

def with_output_to(path, cmd):
  with open(path, 'a') as out:
    sub.Popen(cmd, shell=True, stdout=out, stderr=out)

def command_output(command):
  standard_pipes = dict(
    stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE)
  get_output = lambda stuff: [l.strip() for l in stuff.split('\n') if l]
  p = sub.Popen(command, shell=True, **standard_pipes)
  out, err = p.communicate()
  
  res =  get_output(bytesToString(out)) or get_output(bytesToString(err))
  return res[0] if (len(res) == 1) else res

def writable_files_in(path):
    data = command_output('ls -lR %s' % path)
    switch_path = False
    res = []
    for d in data:
        ds = d.split()
        if not d:
            switch_path = True
            continue
        if switch_path:
            path = ds[0]
            switch_path=False
            continue
        if d.startswith('total'):
            continue
        base = ds[-1]
        #print 'base:', base
        res.append(os.path.join(path, ds[-1]))
    return res


def gensym(object):
  """generate and return a symbol (att ribute name typically) unique to the object's attributes and method names"""
  trial = 'hash_%X' % random.getrandbits(16)
  while hasattr(object, trial):
    trial = 'hash_%X' % random.getrandbits(16)
  return trial


def force_unicode(x):
  return x.decode('utf-8') if isinstance(x, str) else x


identity_function = lambda x: x


def n_defaultdict(n, a_type):
  maker = lambda t: lambda: defaultdict(t)
  for _ in range(n):
    a_type = maker(a_type)
  return a_type()


def tree_order(hierarchy, sequence, h_extractor=identity_function, s_extractor=identity_function):
  """
  A generator returning items of sequence in the order they appear traversing the
  hierarchy (depth-first pre-order).
  """
  data = dict([(s_extractor(x), x) for x in sequence])
  for value in hierarchy.pre_order(h_extractor):
    if value in data:
      yield data[value]


def not_empty(seq):
  """returns None if sequence is empty else a generator on the sequence. Good for checking generator
  contains anything at all. Of course you would hang waiting on a generator that waits.."""

  def list_gen(first, rest):
    yield first
    for x in rest:
      yield x


def pruning_tree_collect(root, children_function, test_function, result_function=None):
  """
  returns the nodes closest to the root nodes of the tree that satisfy the test_function.
  The value returned for a satisfying node is determined by the result_function which
  defaults to the node itself.
  """
  if result_function is None: 
    result_function = identity_function
  results = []

  def do_node(node):
    # print 'evaluating node %s' % node
    if test_function(node):
      # print 'node %s satisfied test' % node
      results.append(result_function(node))
    else:
      # print 'node %s did not satisfy test so examining children %s' % (node, children_function(node))
      for child in children_function(node):
        do_node(child)

  do_node(root)
  return results


def all_satisfy(func, sequence):
  """
  Returns (True, None) if all elements satisfy func else (False, element) of the first element that
  does not satisfy func
  """
  for s in sequence:
    if not func(s):
      return False, s
  return True, None


def one_satisfies(func, sequence):
  "the any builtin unfortunately does not return the element that satisfied the func"
  for s in sequence:
    if func(s):
      return True, s
  return False, None


def identity(x): return x




def unique(sequence, hash_converter=None):
  """returns the unique elements in the sequence. Note that the raw form
  would only work if elements in the sequence are all hashable.  Passing a
  hash_converter that can map elements that are the "same" to the
  same hashable gets around this issue for many cases"""

  seen = set()
  convert = hash_converter is not None
  for s in sequence:
    hashable = hash_converter(s) if convert else s
    if not hashable in seen:
      seen.add(hashable)
      yield s
  del seen


def hexord2str(ho):
  h = [ho[i:i + 2] for i in range(0, len(ho), 2)]
  ints = [int(x, 16) for x in h]
  return ''.join([chr(i) for i in ints])


def str2hexord(s):
  def hex2(n):
    res = hex(n)[2:]
    return res if len(res) == 2 else '0' + res

  return ''.join([hex2(ord(x)) for x in s])


def encrypt(key, val):
  def ith(x, i):
    return ord(x[i]) if i < len(x) else 0

  def mod_len(x, i):
    return ord(x[i % len(x)])

  l = max(len(key), len(val))
  k = [mod_len(key, i) for i in range(l)]
  v = [ith(val, i) for i in range(l)]
  tangled = [chr(k[i] ^ v[i]) for i in range(l)]
  return ''.join(tangled)


def decrypt(key, code):
  l = max(len(key), len(code))

  def mod_len(x, i):
    return ord(x[i % len(x)])

  k = [mod_len(key, i) for i in range(l)]
  c = [ord(x) for x in code]
  ut = [chr(k[i] ^ c[i]) for i in range(l) if k[i] != c[i]]
  return ''.join(ut)


def plain2cipher(key, plain):
  return str2hexord(encrypt(key, plain))


def cipher2plain(key, cipher):
  return decrypt(key, hexord2str(cipher))

def splitter(lst):
  sz = len(lst)
  if sz == 0:
    return [], []
  if sz == 1:
    return lst, []
  if sz == 2:
    return lst[:-1], lst[-1:]
  return lst[:sz / 2], lst[sz / 2:]


def random_pick(lst):
  return lst[random.randint(0, len(lst) - 1)]



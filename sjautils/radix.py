## {{{ http://code.activestate.com/recipes/222109/ (r1)
# radix.py

"""
Defines str(number,radix) -- reverse function to int(str,radix) and long(str,radix)

number -- signed int or long,
radix  -- 2 to 36

Usage:
import radix
str_repr = radix.str( number, radix )

print radix.str( 10, 16 ), radix.str( 1570137287, 36 ) # a python

"""


import string, random, os

alphabet = string.digits + string.ascii_letters + '?$'

def to_str( number, radix ):
   """to_str( number, radix ) -- reverse function to int(str,radix) and long(str,radix)"""

   abc = string.digits + string.ascii_letters + '?$'
   maxr = len(abc)
   if not 2 <= radix <= maxr:
       raise ValueError("radix must be in 2..%d" % maxr)

   result = ''

   if number < 0:
      number = -number
      sign = '-'
   else:
      sign = ''

   while True:
      number, rdigit = divmod( number, radix )
      result = abc[rdigit] + result
      if number == 0:
         return sign + result

   # never here because number >= 0, radix > 0, we repeat (number /= radix)

def random_id(id_bit_size, alphabet_size=len(alphabet)):
   return to_str(random.getrandbits(id_bit_size), alphabet_size)

def decode_id(an_id, alphabet_size = 62):
   rev = an_id[::-1]
   ans = 0
   factor = 1
   for c in rev:
      ans = ans + factor * alphabet.find(c)
      factor = factor * alphabet_size
   return ans

if __name__ == '__main__':
   src = 'qwertyuioplkjhgfdsazxcvbnm0987654321'
   dst = 79495849566202193863718934176854772085778985434624775545

   num = int( src, 36 )
   assert num == dst
   res = str( num, 36 )
   assert res == src
   print ("%s radix 36 is\n%d decimal" % (src, dst))


path = os.path.dirname(__file__) 

import random
word_key = lambda:  ''.join([to_str(random.randint(1,6),10) for _ in range(5)])
def n_words(n=3, sep=''):
   with open(os.path.join(path, 'eff_large_wordlist.txt')) as f:
      words = dict([line.split() for line in f])
   return sep.join([words[word_key()] for _ in range(n)])


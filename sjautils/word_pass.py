#/bin/env python3

import radix
import argparse
import sys

parser = argparse.ArgumentParser(description='foobar')
parser.add_argument('-n', '--num', type=int, default=3)
parser.add_argument('-s', '--sep', default='')

if __name__ == '__main__':
  args = parser.parse_args(sys.argv[1:])
  print(args)
  print(radix.n_words(args.num, args.sep))

from itertools import chain

def flatmap(func, seq):
  return chain.from_iterable(map(func, seq))

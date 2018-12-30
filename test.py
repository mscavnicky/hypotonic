import logging
from hypotonic import Hypotonic

logger = logging.getLogger('hypotonic')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

print(
  list(
    Hypotonic()
      .get('https://www.bergfex.com/slovakia/top10/')
      .find('.section-left div:nth-child(1) a:nth-child(1)')
      .set('resort')
      .follow('@href')
      .set({'size': '.big'})
      .data()))

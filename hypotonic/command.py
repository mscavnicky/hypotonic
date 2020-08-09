import re
import sys
import logging
import asyncio
import textwrap

from hypotonic import request
from hypotonic.context import HtmlContext

logger = logging.getLogger('hypotonic')


async def get(session, _, data, url, params=None):
  response = await request.get(session, url, params)
  yield HtmlContext(url, response), data


async def post(session, _, data, url, payload=None):
  response = await request.post(session, url, payload)
  yield HtmlContext(url, response), data


async def find(_, context, data, selector):
  for result in context.select(selector):
    yield result, data


async def set(_, context, data, descriptor):
  if isinstance(descriptor, str):
    data = {**data, descriptor: context.text()}
  else:
    for key, selector in descriptor.items():
      if isinstance(selector, str):
        results = context.select(selector)
        data = {**data, key: results[0].text()}
      elif isinstance(selector, list):
        results = context.select(selector[0])
        values = [result.text() for result in results]
        data = {**data, key: values}
  yield context, data


async def follow(session, context, data, selector):
  for result in context.select(selector):
    url = result.text()
    response = await request.get(session, url)
    yield HtmlContext(url, response), data


async def paginate(session, context, data, selector, limit=sys.maxsize):
  while True:
    yield context, data
    limit -= 1
    results = context.select(selector)
    if limit <= 0 or len(results) == 0:
      break
    url = results[0].text()
    response = await request.get(session, url)
    context = HtmlContext(url, response)


async def filter(_, context, data, selector):
  if len(context.select(selector)) > 0:
    yield context, data


async def match(_, context, data, regex, flags=0):
  if re.search(regex, context.text(), flags=flags):
    yield context, data


async def delay(_, context, data, secs):
  await asyncio.sleep(secs)
  yield context, data


async def log(_, context, data, level=logging.INFO):
  logger.log(level, f"{len(data)}:{textwrap.shorten(str(context), width=72)}")
  yield context, data

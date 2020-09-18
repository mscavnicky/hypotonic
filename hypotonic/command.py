import re
import sys
import logging
import asyncio
import textwrap

import validators
from more_itertools import always_iterable

from hypotonic import request
from hypotonic.context import Context

logger = logging.getLogger('hypotonic')


async def get(session, _, data, urls, params=None):
  for url in always_iterable(urls):
    context = Context.create(*await request.get(session, url, params))
    yield context, data


async def post(session, _, data, urls, payload=None):
  for url in always_iterable(urls):
    context = Context.create(*await request.post(session, url, payload))
    yield context, data


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


async def then(_, context, data, func):
  context, data = func(context, data)
  yield context, data


async def follow(session, context, data, selector):
  for result in context.select(selector):
    url = result.text()
    context = Context.create(*await request.get(session, url))
    yield context, data


async def paginate(session, context, data, selector, limit=sys.maxsize, param=None):
  page = 1
  while True:
    yield context, data

    page += 1
    results = context.select(selector)
    if page > limit or len(results) == 0:
      break

    result = results[0].text()
    if isinstance(result, str) and validators.url(result):
      url = result
    else:
      url = str(context.url % {param: page})

    context = Context.create(*await request.get(session, url))


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

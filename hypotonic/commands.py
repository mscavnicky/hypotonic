import re
import sys
import logging
import asyncio
import textwrap

from . import html
from . import request

logger = logging.getLogger(__name__)


async def get(session, _, data, url, params=None):
  response = await request.get(session, url, params)
  yield html.parse(url, response), data


async def post(session, _, data, url, payload=None):
  response = await request.post(session, url, payload)
  yield html.parse(url, response), data


async def find(_, context, data, selector):
  for result in context.xpath(html.to_xpath(selector)):
    yield result, data


async def set(_, context, data, descriptor):
  if isinstance(descriptor, str):
    data = {**data, descriptor: html.text_content(context)}
  else:
    for key, selector in descriptor.items():
      if isinstance(selector, str):
        results = context.xpath(html.to_xpath(selector))
        data = {**data, key: html.text_content(results[0])}
      elif isinstance(selector, list):
        results = context.xpath(html.to_xpath(selector[0]))
        values = [html.text_content(result) for result in results]
        data = {**data, key: values}
  yield context, data


async def follow(session, context, data, selector):
  for result in context.xpath(html.to_xpath(selector)):
    response = await request.get(session, result)
    yield html.parse(result, response), data


async def paginate(session, context, data, selector, limit=sys.maxsize):
  selector = html.to_xpath(selector)
  while True:
    yield context, data
    limit -= 1
    results = context.xpath(selector)
    if limit <= 0 or len(results) == 0:
      break
    url = results[0]
    response = await request.get(session, url)
    context = html.parse(url, response)


async def filter(_, context, data, selector):
  if len(context.xpath(html.to_xpath(selector))) > 0:
    yield context, data


async def match(_, context, data, regex, flags=0):
  if re.search(regex, context.text_content(), flags=flags):
    yield context, data


async def delay(_, context, data, secs):
  await asyncio.sleep(secs)
  yield context, data


async def log(_, context, data):
  logger.debug((
    textwrap.shorten(html.to_string(context), width=72),
    textwrap.shorten(str(data), width=72)))
  yield context, data

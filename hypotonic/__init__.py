import re
import sys
import time
import logging
import textwrap
import itertools
import unicodedata

import asyncio
import aiohttp

from lxml import html
from cssselect import GenericTranslator, SelectorError

logger = logging.getLogger(__name__)


class Html:
  @staticmethod
  async def get(session, url, params=None):
    async with session.get(url, params=params) as response:
      return await response.text()

  @staticmethod
  async def post(session, url, payload=None):
    async with session.post(url, data=payload) as response:
      return await response.text()

  @staticmethod
  def parse(url, html_string):
    doc = html.fromstring(html_string)
    # Making links absolute is required to allow following.
    doc.make_links_absolute(url)
    # Replacing <br> tags with \n, prevents text contatenating.
    for br in doc.xpath('*//br'):
      br.tail = '\n' + br.tail if br.tail else '\n'
    return doc

  @staticmethod
  def text_content(element):
    """Convenience method to extract text from HTML element tree. Performs
    stripping and canonicalization of UTF-8 characters (e.g. '/xa0' to ' ')."""
    return unicodedata.normalize('NFKC', element.text_content().strip())

  @staticmethod
  def to_xpath(selector):
    """Attempt to convert CSS selector to XPath."""
    try:
      return GenericTranslator().css_to_xpath(selector)
    except SelectorError:
      return selector


class Commands:
  @staticmethod
  async def get(session, _, data, url, params=None):
    response = await Html.get(session, url, params)
    yield Html.parse(url, response), data

  @staticmethod
  async def post(session, _, data, url, payload=None):
    response = await Html.post(session, url, payload)
    yield Html.parse(url, response), data

  @staticmethod
  async def find(_, context, data, selector):
    for result in context.xpath(Html.to_xpath(selector)):
      yield result, data

  @staticmethod
  async def set(_, context, data, descriptor):
    if isinstance(descriptor, str):
      data = {**data, descriptor: Html.text_content(context)}
    else:
      for key, selector in descriptor.items():
        if isinstance(selector, str):
          results = context.xpath(Html.to_xpath(selector))
          data = {**data, key: Html.text_content(results[0])}
        elif isinstance(selector, list):
          results = context.xpath(Html.to_xpath(selector[0]))
          values = [Html.text_content(result) for result in results]
          data = {**data, key: values}
    yield context, data

  @staticmethod
  async def follow(session, context, data, selector):
    for result in context.xpath(Html.to_xpath(selector)):
      response = await Html.get(session, result)
      yield Html.parse(result, response), data

  @staticmethod
  async def paginate(session, context, data, selector, limit=sys.maxsize):
    selector = Html.to_xpath(selector)
    while True:
      yield context, data
      limit -= 1
      results = context.xpath(selector)
      if limit <= 0 or len(results) == 0:
        break
      url = results[0].attrib['href']
      response = await Html.get(session, url)
      context = Html.parse(url, response)

  @staticmethod
  async def filter(_, context, data, selector):
    if len(context.xpath(Html.to_xpath(selector))) > 0:
      yield context, data

  @staticmethod
  async def match(_, context, data, regex, flags=0):
    if re.search(regex, context.text_content(), flags=flags):
      yield context, data

  @staticmethod
  async def delay(_, context, data, secs):
    time.sleep(secs)
    yield context, data

  @staticmethod
  async def log(_, context, data):
    logger.debug((
      textwrap.shorten(html.tostring(context).decode('utf-8'), width=72),
      textwrap.shorten(str(data), width=72)))
    yield context, data


class Hypotonic:
  def __init__(self, url=None):
    self.commands = []
    self.results = []
    self.errors = []

    if url:
      self.commands.append(('get', (url,), {}))

  async def worker(self, i, session, queue):
    logger.debug(f"Worker {i} starting.")
    while True:
      commands, context, data = await queue.get()

      try:
        command, args, kwargs = next(commands)
        logger.debug(("Start", i, command, args, kwargs))

        func = getattr(Commands, command)
        async for result in func(session, context, data, *args, **kwargs):
          _, commands_copy = itertools.tee(commands)
          queue.put_nowait((commands_copy, *result))

        logger.debug(("Stop", i, command, args, kwargs))
      except StopIteration:
        self.results.append(data)
      except:
        self.errors.append(((command, args, kwargs, context), sys.exc_info()))
        logger.debug(f"Unexpected exception {sys.exc_info()}.")
      finally:
        queue.task_done()

  async def run(self):
    session = aiohttp.ClientSession()
    queue = asyncio.Queue()

    tasks = []
    for i in range(4):
      tasks.append(asyncio.create_task(self.worker(i, session, queue)))

    queue.put_nowait((iter(self.commands), None, {}))
    await queue.join()

    for task in tasks:
      task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    await session.close()

  def data(self):
    """Return all the scraped data as a list of dicts."""
    asyncio.run(self.run())
    return self.results, self.errors

  def __getattr__(self, attr):
    def apply(*args, **kwargs):
      self.commands.append((attr, args, kwargs))
      return self

    return apply

import re
import time

import requests
from lxml import html
from cssselect import GenericTranslator, SelectorError

from utils import flatmap


class Document:
  @staticmethod
  def parse(url, html_string):
    doc = html.fromstring(html_string)
    # Making links absolute is required to allow following.
    doc.make_links_absolute(url)
    return doc

  @staticmethod
  def to_xpath(selector):
    """Attempt to convert CSS selector to XPath."""
    try:
      return GenericTranslator().css_to_xpath(selector)
    except SelectorError:
      return selector


class Commands:
  @staticmethod
  def get(_, data, url):
    yield Document.parse(url, requests.get(url).text), data

  @staticmethod
  def find(context, data, selector):
    for result in context.xpath(Document.to_xpath(selector)):
      yield result, data

  @staticmethod
  def set(context, data, descriptor):
    if isinstance(descriptor, str):
      data = {**data, descriptor: context.text}
    else:
      for key, selector in descriptor.items():
        results = context.xpath(Document.to_xpath(selector))
        data = {**data, key: results[0].text}
    yield context, data

  @staticmethod
  def follow(context, data, selector):
    for result in context.xpath(Document.to_xpath(selector)):
      response = requests.get(result)
      yield Document.parse(result, response.text), data

  @staticmethod
  def filter(context, data, selector):
    if len(context.xpath(Document.to_xpath(selector))) > 0:
      yield context, data

  @staticmethod
  def match(context, data, regex):
    if re.match(regex, context.text):
      yield context, data

  @staticmethod
  def delay(context, data, secs):
    time.sleep(secs)
    yield context, data

  @staticmethod
  def debug(context, data):
    print(context, data)
    yield context, data


class Hypotonic:
  def __init__(self):
    self.commands = []
    # List of (context, data) tuples.
    self.queue = [(None, {})]

  def data(self):
    """Return all the currently scraped data as a list of dicts."""
    for command, args in self.commands:
      print(command, args)
      func = getattr(Commands, command)
      self.queue = list(flatmap(lambda item: func(*item, *args), self.queue))
    return (data for _, data in self.queue)

  def __getattr__(self, attr):
    def apply(*args):
      self.commands.append((attr, args))
      return self

    return apply

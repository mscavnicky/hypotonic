import unicodedata
from lxml import html
from cssselect import GenericTranslator, SelectorError


def parse(url, html_string):
  doc = html.fromstring(html_string)
  # Making links absolute is required to allow following.
  doc.make_links_absolute(url)
  # Replacing <br> tags with \n, prevents text contatenating.
  for br in doc.xpath('*//br'):
    br.tail = '\n' + br.tail if br.tail else '\n'
  return doc


def text_content(element):
  """Convenience method to extract text from HTML element tree. Performs
  stripping and canonicalization of UTF-8 characters (e.g. '/xa0' to ' ')."""
  return unicodedata.normalize('NFKC', element.text_content().strip())


def to_xpath(selector):
  """Attempt to convert CSS selector to XPath."""
  try:
    return GenericTranslator().css_to_xpath(selector)
  except SelectorError:
    return selector


def to_string(element):
  """Convert HTML element to raw html string including element tags."""
  return html.tostring(element).decode('utf-8')

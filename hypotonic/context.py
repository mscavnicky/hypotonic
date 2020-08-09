import unicodedata
from lxml import html
from parsel import csstranslator
from cssselect import SelectorError


class StringContext:
  def __init__(self, url, str):
    self.url = url
    self.str = str

  def select(self, selector):
    raise TypeError('Cannot run selector on a StringContext.')

  def text(self):
    return self.str

  def __str__(self):
    return self.str


class HtmlContext:
  def __init__(self, url, str_or_element):
    self.url = url
    self.element = str_or_element

    if isinstance(str_or_element, str):
      self.element = self.parse(self.url, self.element)

  def select(self, selector):
    selected = []
    for element in self.element.xpath(self.to_xpath(selector)):
      # XPath query can return both element, or lxml.etree._ElementUnicodeResult.
      if isinstance(element, str):
        selected.append(StringContext(self.url, element))
      else:
        selected.append(HtmlContext(self.url, element))
    return selected

  def text(self):
    """Convenience method to extract text from HTML element tree. Performs
      stripping and canonicalization of UTF-8 characters (e.g. '/xa0' to ' ')."""
    return unicodedata.normalize('NFKC', self.element.text_content().strip())

  def __str__(self):
    """Convert HTML element to raw html string including element tags."""
    return html.tostring(self.element).decode('utf-8')

  @staticmethod
  def to_xpath(selector):
    """Attempt to convert CSS selector to XPath."""
    try:
      return csstranslator.css2xpath(selector)
    except SelectorError:
      return selector

  @staticmethod
  def parse(url, html_string):
    doc = html.fromstring(html_string)
    # Making links absolute is required to allow following.
    doc.make_links_absolute(url)
    # Replacing <br> tags with \n, prevents text contatenating.
    for br in doc.xpath('*//br'):
      br.tail = '\n' + br.tail if br.tail else '\n'
    return doc

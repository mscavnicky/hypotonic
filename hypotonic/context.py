import unicodedata
import urllib.parse
import bs4


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
    # Determine whether selector is using ::attr or ::text pseudo-attribute.
    selector_type = None
    if selector.endswith('::text'):
      selector_type = 'text'
      selector = selector.rstrip('::text')
    elif selector.find('::attr') > 0:
      # Use attribute as a selector type.
      selector_type = selector[selector.find('::attr') + 7:-1]
      selector = selector[:selector.find('::attr')]

    selected = []
    for element in self.element.select(selector):
      if selector_type is None:
        selected.append(HtmlContext(self.url, element))
      elif selector_type == 'text':
        selected.append(
          StringContext(self.url, HtmlContext(self.url, element).text()))
      else:
        selected.append(StringContext(self.url, element[selector_type]))
    return selected

  def text(self):
    """Convenience method to extract text from HTML element tree. Performs
      stripping and canonicalization of UTF-8 characters (e.g. '/xa0' to ' ')."""
    return unicodedata.normalize('NFKC', self.element.text.strip())

  def __str__(self):
    """Convert HTML element to raw html string including element tags."""
    return str(self.element)

  @staticmethod
  def parse(url, html_string):
    doc = bs4.BeautifulSoup(html_string, features='html5lib')
    # Making links absolute is required to allow following.
    for tag in doc.findAll('a', href=True):
      tag['href'] = urllib.parse.urljoin(url, tag['href'])
    # Replacing <br> tags with \n, prevents text concatenating.
    for br in doc.findAll('br'):
      br.replace_with("\n")
    return doc

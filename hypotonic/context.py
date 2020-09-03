import json
import unicodedata
import urllib.parse
import bs4
import jsonpath_ng as jsonpath


def make_context(url, content_type, content):
  """Choose the right context based on the content type."""
  if content_type == 'application/json':
    return JsonContext(url, JsonContext.parse(url, content))
  else:
    return HtmlContext(url, HtmlContext.parse(url, content))


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
  def __init__(self, url, element):
    self.url = url
    self.element = element

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


class JsonContext:
  def __init__(self, url, json):
    self.url = url
    self.json = json

  def select(self, selector):
    selected = []
    for match in jsonpath.parse(selector).find(self.json):
      if isinstance(match.value, str):
        selected.append(StringContext(self.url, match.value))
      else:
        selected.append(JsonContext(self.url, match.value))
    return selected

  def text(self):
    return JsonContext.extract_values(self.json)

  @staticmethod
  def extract_values(json):
    if isinstance(json, list):
      return ' '.join(map(JsonContext.extract_values, json))
    elif isinstance(json, dict):
      return ' '.join(map(JsonContext.extract_values, json.values()))
    else:
      return json

  def __str__(self):
    return json.dumps(self.json)

  @staticmethod
  def parse(_url, json_string):
    return json.loads(json_string)

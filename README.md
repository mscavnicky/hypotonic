# Hypotonic

Fast asynchronous web scraper with minimalist API inspired by awesome [node-osmosis](https://github.com/rchipka/node-osmosis).

Hypotonic provides SQLAlchemy-like command chaining DSL to define HTML scrapers. Everything is executed asynchronously via `asyncio` and all dependencies are pure Python. Supports querying by CSS selectors with Scrapy's pseudo-attributes. XPath is not supported due to `libxml` requirement.

Hypotonic does not natively execute JavaScript on websites and it is recommended to use [prerender](https://prerender.com).

## Installing

Hypotonic requires Python 3.6+.

`pip install hypotonic`

## Example

```python
from hypotonic import Hypotonic

data, errors = (
  Hypotonic()
    .get('http://books.toscrape.com/')
    .paginate('.next a::attr(href)', 5)
    .find('.product_pod h3')
    .set('title')
    .follow('a::attr(href)')
    .set({'price': '.price_color',
          'availability': 'p.availability'})
    .data()
)
```

# Hypotonic

Fast asynchronous web scraper with minimalist API inspired by awesome [node-osmosis](https://github.com/rchipka/node-osmosis).

Hypotonic provides SQLAlchemy-like command chaining DSL to define HTML scrapers. Everything is executed asynchronously via `asyncio` and is ultra-fast thanks to `lxml` parser. Supports querying by XPath or CSS selectors.

Hypotonic does not natively execute JavaScript on websites and it is recommended to use [prerender](https://prerender.com).

## Installing

Hypotonic requires Python 3.6+ and `libxml2` C library.

`pip install hypotonic`

## Example

```python
from hypotonic import Hypotonic

data, errors = (
  Hypotonic()
    .get('http://books.toscrape.com/')
    .paginate('.next a', 5)
    .find('.product_pod h3 a')
    .follow('@href')
    .set({'title': 'h3 a',
          'price': '.price_color',
          'availability': 'p.availability'})
    .data()
)
```

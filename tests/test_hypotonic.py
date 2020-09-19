import logging
import aiohttp
import unittest
import aiounittest

from vcr import VCR
from hypotonic import Hypotonic

logger = logging.getLogger('hypotonic')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

vcr = VCR(cassette_library_dir='./tests/cassettes')


class TestHypotonic(aiounittest.AsyncTestCase):
  def test_synchronous_run(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.nav-list ul a')
        .set('category')
        .data())

    self.assertFalse(errors)
    self.assertEqual(50, len(data))

  async def test_get_unreachable_url(self):
    data, errors = await (
      Hypotonic()
        .get('https://non-existing-url.com')
        .run()
    )

    self.assertEqual(0, len(data))
    self.assertEqual(1, len(errors))
    self.assertIsInstance(errors[0][2], aiohttp.ClientConnectorError)

  async def test_get_redirect(self):
    data, errors = await (
      Hypotonic()
        .get('https://httpstat.us/301')
        .find('h1')
        .set('title')
        .run()
    )

    self.assertEqual(0, len(errors))
    self.assertEqual([{'title': 'httpstat.us'}], data)

  async def test_get_not_found(self):
    data, errors = await (
      Hypotonic()
        .get('https://httpstat.us/404')
        .run()
    )

    self.assertEqual(0, len(data))
    self.assertEqual(1, len(errors))
    self.assertIsInstance(errors[0][2], aiohttp.ClientResponseError)

  async def test_get_internal_server_error(self):
    data, errors = await (
      Hypotonic()
        .get('https://httpstat.us/500')
        .run()
    )

    self.assertEqual(0, len(data))
    self.assertEqual(1, len(errors))
    self.assertIsInstance(errors[0][2], aiohttp.ClientResponseError)


  async def test_get_with_params(self):
    data, errors = await (
      Hypotonic()
        .get('http://testing-ground.scraping.pro/textlist', {'ver': '3'})
        .find('h1')
        .set('title')
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertIn({'title': 'TEXT LIST (version 3)'}, data)

  async def test_get_multiple_urls(self):
    data, errors = await (
      Hypotonic()
        .get([f"http://quotes.toscrape.com/page/{page}/" for page in range(1, 11)])
        .find('.quote .text')
        .set('quote')
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual(100, len(data))

  async def test_post(self):
    data, errors = await (
      Hypotonic()
        .post('http://quotes.toscrape.com/login',
              {'username': 'admin', 'password': 'admin'})
        .find('.header-box .col-md-4 a')
        .set('label')
        .run())

    self.assertFalse(errors)
    self.assertEqual([{'label': 'Logout'}], data)

  async def test_find_missing_element(self):
    data, errors = await (
      Hypotonic()
        .get('http://books.toscrape.com/')
        .find('h11 fake-class')
        .set('title')
        .run()
    )

    self.assertFalse(errors)
    self.assertFalse(data)

  async def test_find_with_invalid_selector(self):
    data, errors = await (
      Hypotonic()
        .get('http://books.toscrape.com/')
        .find('.#./')
        .set('title')
        .run()
    )

    self.assertFalse(data)
    self.assertEqual(1, len(errors))

  async def test_find_with_css(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('.nav-list ul a')
        .set('category')
        .run())

    self.assertFalse(errors)
    self.assertEqual(50, len(data))
    self.assertIn({'category': 'Romance'}, data)

  async def test_set_with_str(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('.h1 a')
        .set('title')
        .run())

    self.assertFalse(errors)
    self.assertEqual([{'title': 'Books to Scrape'}], data)

  async def test_set_with_array(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .set({'title': '.h1 a',
              'categories': ['.nav-list ul a']})
        .run())

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertEqual(50, len(data[0]['categories']))
    self.assertIn('Romance', data[0]['categories'])

  async def test_set_with_dict(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('li article')
        .set({'title': 'h3 a',
              'price': '.price_color',
              'availability': 'p.availability'})
        .run())

    self.assertFalse(errors)
    self.assertEqual(20, len(data))
    self.assertIn({'title': 'Sharp Objects',
                   'price': '£47.82',
                   'availability': 'In stock'}, data)

  async def test_set_attr(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('.product_pod h3')
        .set({'url': 'a::attr(href)',
              'title': 'a::text'})
        .run())

    self.assertFalse(errors)
    self.assertEqual(20, len(data))
    self.assertIn({'title': 'Sharp Objects',
                   'url': 'http://books.toscrape.com/catalogue/sharp-objects_997/index.html'},
                  data)

  async def test_then(self):
    data, errors = await (
      Hypotonic()
        .get('http://testing-ground.scraping.pro/textlist', {'ver': '3'})
        .find('h1')
        .set('title')
        .then(lambda context, data: (
            context,
            {**data, 'version': context.url.query['ver']}
        ))
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertIn({'title': 'TEXT LIST (version 3)', 'version': '3'}, data)

  async def test_follow(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .follow('.product_pod h3 a::attr(href)')
        .find('h1')
        .set('title')
        .run())

    self.assertFalse(errors)
    self.assertEqual(20, len(data))
    self.assertIn({'title': 'Sharp Objects'}, data)

  async def test_paginate(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .paginate('.next a::attr(href)', 3)
        .find('li article')
        .set({'title': 'h3 a'})
        .run())

    self.assertFalse(errors)
    self.assertEqual(60, len(data))
    self.assertIn({'title': 'Sharp Objects'}, data)
    self.assertIn({'title': 'In Her Wake'}, data)
    self.assertIn({'title': 'Thirst'}, data)

  async def test_filter(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('li article')
        .filter('.Five')
        .set({'title': 'h3 a'})
        .run())

    self.assertFalse(errors)
    self.assertEqual(4, len(data))
    self.assertIn({'title': 'Set Me Free'}, data)
    self.assertNotIn({'title': 'Sharp Objects'}, data)

  async def test_match(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('.product_pod h3 a')
        .match('[tT]he')
        .set('title')
        .run())

    self.assertFalse(errors)
    self.assertEqual(9, len(data))
    self.assertIn({'title': 'Tipping the Velvet'}, data)
    self.assertNotIn({'title': 'Sharp Objects'}, data)

  async def test_match_case_insensitive(self):
    import re

    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('.product_pod h3 a')
        .match('THE', flags=re.IGNORECASE)
        .set('title')
        .run())

    self.assertFalse(errors)
    self.assertEqual(9, len(data))
    self.assertIn({'title': 'Tipping the Velvet'}, data)
    self.assertNotIn({'title': 'Sharp Objects'}, data)

  async def test_log(self):
    with self.assertLogs(logger, level='INFO') as context:
      data, errors = await (
        Hypotonic('http://books.toscrape.com/')
          .find('.h1 a')
          .set('title')
          .log()
          .run())

    self.assertFalse(errors)
    self.assertIn(
      'INFO:hypotonic:1:<a href="http://books.toscrape.com/index.html">Books to Scrape</a>',
      context.output)

  async def test_extracted_text_is_stripped(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('.nav-list a')
        .set('category')
        .run())

    self.assertFalse(errors)
    self.assertEqual(51, len(data))
    for item in data:
      self.assertEqual(item['category'], item['category'].strip())

  @vcr.use_cassette()
  async def test_br_tags_become_newlines(self):
    data, errors = await (
      Hypotonic('http://testing-ground.scraping.pro/blocks')
        .find('.best')
        .set('text')
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual(6, len(data))
    self.assertNotIn({'text': 'BESTPRICE!'}, data)
    self.assertIn({'text': 'BEST\nPRICE!'}, data)

  @vcr.use_cassette()
  async def test_utf_8_is_canonicalized(self):
    data, errors = await (
      Hypotonic('https://dennikn.sk/kontakt/')
        .find('main article div p:nth-child(2)')
        .set('text')
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertEqual(data[0]['text'],
                     'Ak nájdete chybu v článkoch, budeme vďační, ak nám napíšete na editori@dennikn.sk.')

  async def test_get_json(self):
    data, errors = await (
      Hypotonic('https://jsonplaceholder.typicode.com/users')
        .find('$[*]')
        .set({'id': '$.id',
              'name': '$.name'})
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual(10, len(data))
    self.assertIn({'id': 2, 'name': 'Ervin Howell'}, data)

  async def test_set_json_value(self):
    data, errors = await (
      Hypotonic('https://jsonplaceholder.typicode.com/users')
        .find('$[*]')
        .find('$.address.geo')
        .set('coords')
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual(10, len(data))
    self.assertIn({'coords': {'lat': '-37.3159', 'lng': '81.1496'}}, data)

  @vcr.use_cassette()
  async def test_non_standard_json_content_type(self):
    data, errors = await (
      Hypotonic()
        .get('https://www.sreality.cz/api/cs/v2/estates/count',
             {'category_main_cb': 1,
              'category_type_cb': 1,
              'locality_country_id': 112,
              'locality_district_id': 5006,
              'locality_region_id': 10})
        .set({'size': '$.result_size'})
        .run()
    )

    self.assertFalse(errors)
    self.assertEqual([{'size': 310}], data)


if __name__ == '__main__':
  unittest.main()

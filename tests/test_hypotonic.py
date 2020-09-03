import unittest
import aiounittest
from unittest import mock
import logging
from vcr import VCR
from hypotonic import Hypotonic

logger = logging.getLogger('hypotonic')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

vcr = VCR(cassette_library_dir='./tests/cassettes')


class TestHypotonic(aiounittest.AsyncTestCase):
  async def test_async_run(self):
    data, errors = await (
      Hypotonic('http://books.toscrape.com/')
        .find('.nav-list ul a')
        .set('category')
        .run())

    self.assertFalse(errors)
    self.assertEqual(50, len(data))

  @mock.patch('logging.Logger._log')
  def test_get_invalid_url(self, _):
    data, errors = (
      Hypotonic()
        .get('https://non-existing-url.com')
        .data()
    )

    self.assertFalse(data)
    self.assertEqual(1, len(errors))

  @vcr.use_cassette()
  def test_get_with_params(self):
    data, errors = (
      Hypotonic()
        .get('http://testing-ground.scraping.pro/textlist', {'ver': '3'})
        .find('h1')
        .set('title')
        .data()
    )

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertIn({'title': 'TEXT LIST (version 3)'}, data)

  def test_get_multiple_urls(self):
    data, errors = (
      Hypotonic()
        .get([f"http://quotes.toscrape.com/page/{page}/" for page in range(1, 11)])
        .find('.quote .text')
        .set('quote')
        .data()
    )

    self.assertFalse(errors)
    self.assertEqual(100, len(data))

  def test_post(self):
    data, errors = (
      Hypotonic()
        .post('http://quotes.toscrape.com/login',
              {'username': 'admin', 'password': 'admin'})
        .find('.header-box .col-md-4 a')
        .set('label')
        .data())

    self.assertFalse(errors)
    self.assertEqual([{'label': 'Logout'}], data)

  @mock.patch('logging.Logger._log')
  def test_find_missing_element(self, _):
    data, errors = (
      Hypotonic()
        .get('http://books.toscrape.com/')
        .find('h11 fake-class')
        .set('title')
        .data()
    )

    self.assertFalse(errors)
    self.assertFalse(data)

  @mock.patch('logging.Logger._log')
  def test_find_with_invalid_selector(self, _):
    data, errors = (
      Hypotonic()
        .get('http://books.toscrape.com/')
        .find('.#./')
        .set('title')
        .data()
    )

    self.assertFalse(data)
    self.assertEqual(1, len(errors))

  def test_find_with_css(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.nav-list ul a')
        .set('category')
        .data())

    self.assertFalse(errors)
    self.assertEqual(50, len(data))
    self.assertIn({'category': 'Romance'}, data)

  def test_set_with_str(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.h1 a')
        .set('title')
        .data())

    self.assertFalse(errors)
    self.assertEqual([{'title': 'Books to Scrape'}], data)

  def test_set_with_array(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .set({'title': '.h1 a',
              'categories': ['.nav-list ul a']})
        .data())

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertEqual(50, len(data[0]['categories']))
    self.assertIn('Romance', data[0]['categories'])

  def test_set_with_dict(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('li article')
        .set({'title': 'h3 a',
              'price': '.price_color',
              'availability': 'p.availability'})
        .data())

    self.assertFalse(errors)
    self.assertEqual(20, len(data))
    self.assertIn({'title': 'Sharp Objects',
                   'price': '£47.82',
                   'availability': 'In stock'}, data)

  def test_set_attr(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.product_pod h3')
        .set({'url': 'a::attr(href)',
              'title': 'a::text'})
        .data())

    self.assertFalse(errors)
    self.assertEqual(20, len(data))
    self.assertIn({'title': 'Sharp Objects',
                   'url': 'http://books.toscrape.com/catalogue/sharp-objects_997/index.html'},
                  data)

  def test_follow(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .follow('.product_pod h3 a::attr(href)')
        .find('h1')
        .set('title')
        .data())

    self.assertFalse(errors)
    self.assertEqual(20, len(data))
    self.assertIn({'title': 'Sharp Objects'}, data)

  def test_paginate(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .paginate('.next a::attr(href)', 3)
        .find('li article')
        .set({'title': 'h3 a'})
        .data())

    self.assertFalse(errors)
    self.assertEqual(60, len(data))
    self.assertIn({'title': 'Sharp Objects'}, data)
    self.assertIn({'title': 'In Her Wake'}, data)
    self.assertIn({'title': 'Thirst'}, data)

  def test_filter(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('li article')
        .filter('.Five')
        .set({'title': 'h3 a'})
        .data())

    self.assertFalse(errors)
    self.assertEqual(4, len(data))
    self.assertIn({'title': 'Set Me Free'}, data)
    self.assertNotIn({'title': 'Sharp Objects'}, data)

  def test_match(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.product_pod h3 a')
        .match('[tT]he')
        .set('title')
        .data())

    self.assertFalse(errors)
    self.assertEqual(9, len(data))
    self.assertIn({'title': 'Tipping the Velvet'}, data)
    self.assertNotIn({'title': 'Sharp Objects'}, data)

  def test_match_case_insensitive(self):
    import re

    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.product_pod h3 a')
        .match('THE', flags=re.IGNORECASE)
        .set('title')
        .data())

    self.assertFalse(errors)
    self.assertEqual(9, len(data))
    self.assertIn({'title': 'Tipping the Velvet'}, data)
    self.assertNotIn({'title': 'Sharp Objects'}, data)

  def test_log(self):
    with self.assertLogs(logger, level='INFO') as context:
      data, errors = (
        Hypotonic('http://books.toscrape.com/')
          .find('.h1 a')
          .set('title')
          .log()
          .data())

    self.assertFalse(errors)
    self.assertIn(
      'INFO:hypotonic:1:<a href="http://books.toscrape.com/index.html">Books to Scrape</a>',
      context.output)

  def test_extracted_text_is_stripped(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.nav-list a')
        .set('category')
        .data())

    self.assertFalse(errors)
    self.assertEqual(51, len(data))
    for item in data:
      self.assertEqual(item['category'], item['category'].strip())

  @vcr.use_cassette()
  def test_br_tags_become_newlines(self):
    data, errors = (
      Hypotonic('http://testing-ground.scraping.pro/blocks')
        .find('.best')
        .set('text')
        .data()
    )

    self.assertFalse(errors)
    self.assertEqual(6, len(data))
    self.assertNotIn({'text': 'BESTPRICE!'}, data)
    self.assertIn({'text': 'BEST\nPRICE!'}, data)

  @vcr.use_cassette()
  def test_utf_8_is_canonicalized(self):
    data, errors = (
      Hypotonic('https://dennikn.sk/kontakt/')
        .find('main article div p:nth-child(2)')
        .set('text')
        .data()
    )

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertEqual(data[0]['text'],
                     'Ak nájdete chybu v článkoch, budeme vďační, ak nám napíšete na editori@dennikn.sk.')

  def test_get_json(self):
    data, errors = (
      Hypotonic('https://jsonplaceholder.typicode.com/users')
        .find('$[*]')
        .set({'id': '$.id',
              'name': '$.name'})
        .data()
    )

    self.assertFalse(errors)
    self.assertEqual(10, len(data))
    self.assertIn({'id': 2, 'name': 'Ervin Howell'}, data)

  def test_set_json_value(self):
    data, errors = (
      Hypotonic('https://jsonplaceholder.typicode.com/users')
        .find('$[*]')
        .find('$.address.geo')
        .set('coords')
        .data()
    )

    self.assertFalse(errors)
    self.assertEqual(10, len(data))
    self.assertIn({'coords': '-37.3159 81.1496'}, data)

if __name__ == '__main__':
  unittest.main()

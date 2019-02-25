import unittest
import logging
from vcr import VCR
from hypotonic import Hypotonic

logger = logging.getLogger('hypotonic')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

vcr = VCR(cassette_library_dir='./cassettes')


class TestHypotonic(unittest.TestCase):
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

  def test_find_with_xpath(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find(
        '//*[contains(concat( " ", @class, " " ), concat( " ", "nav-list", " " ))]//ul//a')
        .set('category')
        .data())

    self.assertFalse(errors)
    self.assertEqual(50, len(data))
    self.assertTrue({'category': 'Romance'} in data)

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

  def test_follow(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .find('.product_pod h3 a')
        .follow('@href')
        .find('h1')
        .set('title')
        .data())

    self.assertFalse(errors)
    self.assertEqual(20, len(data))
    self.assertIn({'title': 'Sharp Objects'}, data)

  def test_paginate(self):
    data, errors = (
      Hypotonic('http://books.toscrape.com/')
        .paginate('.next a', 3)
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

  @vcr.use_cassette()
  def test_br_tags_become_newlines(self):
    data, errors = (
      Hypotonic('https://www.justetf.com/en/etf-profile.html?tab=listing&isin=IE00B44CND37')
        .find('.tab-container .container tbody tr')
        .set({'ticker': 'td:nth-child(5)'})
        .data()
    )

    self.assertFalse(errors)
    self.assertEqual(7, len(data))
    self.assertNotIn({'ticker': 'TSYE.PAINSYBTE.ivOQ'}, data)
    self.assertIn({'ticker': 'TRSY.MI\nINSYBTE.ivOQ'}, data)


if __name__ == '__main__':
  unittest.main()
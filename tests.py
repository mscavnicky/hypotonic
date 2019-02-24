import unittest
import logging
from hypotonic import Hypotonic

logger = logging.getLogger('hypotonic')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class TestHypotonic(unittest.TestCase):
  def setUp(self):
    self.hypotonic = Hypotonic()
    self.hypotonic.get('http://books.toscrape.com/')

  def test_post(self):
    data, errors = (
      self.hypotonic
        .post('http://quotes.toscrape.com/login',
              {'username': 'admin', 'password': 'admin'})
        .find('.header-box .col-md-4 a')
        .set('label')
        .data())

    self.assertFalse(errors)
    self.assertEqual([{'label': 'Logout'}], data)

  def test_find_with_xpath(self):
    data, errors = (
      self.hypotonic
        .find(
        '//*[contains(concat( " ", @class, " " ), concat( " ", "nav-list", " " ))]//ul//a')
        .set('category')
        .data())

    self.assertFalse(errors)
    self.assertEqual(50, len(data))
    self.assertTrue({'category': 'Romance'} in data)

  def test_find_with_css(self):
    data, errors = (
      self.hypotonic
        .find('.nav-list ul a')
        .set('category')
        .data())

    self.assertFalse(errors)
    self.assertEqual(50, len(data))
    self.assertIn({'category': 'Romance'}, data)

  def test_set_with_str(self):
    data, errors = (
      self.hypotonic
        .find('.h1 a')
        .set('title')
        .data())

    self.assertFalse(errors)
    self.assertEqual([{'title': 'Books to Scrape'}], data)

  def test_set_with_array(self):
    data, errors = (
      self.hypotonic
        .set({'title': '.h1 a',
              'categories': ['.nav-list ul a']})
        .data())

    self.assertFalse(errors)
    self.assertEqual(1, len(data))
    self.assertEqual(50, len(data[0]['categories']))
    self.assertIn('Romance', data[0]['categories'])

  def test_set_with_dict(self):
    data, errors = (
      self.hypotonic
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
      self.hypotonic
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
      self.hypotonic
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
      self.hypotonic
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
      self.hypotonic
        .find('.product_pod h3 a')
        .match('[tT]he')
        .set('title')
        .data())

    self.assertFalse(errors)
    self.assertEqual(9, len(data))
    self.assertIn({'title': 'Tipping the Velvet'}, data)
    self.assertNotIn({'title': 'Sharp Objects'}, data)


if __name__ == '__main__':
  unittest.main()

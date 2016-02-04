import unittest

import comparators
from loaders import parse_value, BaseLoader


class TestComparators(unittest.TestCase):

    def test_base(self):
        comp = comparators.BaseComparator
        self.assertFalse(comp().compare('123', '456'))
        self.assertTrue(comp().compare('123', '123'))

    def test_dict(self):
        comp = comparators.DictComparator
        self.assertFalse(comp().compare({1: 1}, {0: 1}))
        self.assertFalse(comp().compare({1: 1}, {1: 0}))
        self.assertTrue(comp().compare({1: 1}, {1: 1}))
        self.assertFalse(comp(True).compare({1: 1}, {0: 1}))
        self.assertTrue(comp(True).compare({1: 1}, {1: 0}))
        self.assertTrue(comp(True, 1).compare({1: {1: 1}}, {1: {0: 1}}))
        self.assertFalse(comp(True, 2).compare({1: {1: 1}}, {1: {0: 1}}))
        self.assertTrue(comp(True, 2).compare({1: {1: {1: 1}}}, {1: {1: {0: 1}}}))
        self.assertFalse(comp(True, 3).compare({1: {1: {1: 1}}}, {1: {1: {0: 1}}}))

    def test_list(self):
        comp = comparators.ListComparator
        self.assertFalse(comp().compare([1, 2, 3], [1, 2, 4]))
        self.assertFalse(comp().compare([1, 2, 3], [1, 3, 2]))
        self.assertFalse(comp().compare([1, 2, 3], [1, 2, 3, 4]))
        self.assertTrue(comp().compare([1, 2, 3], [1, 2, 3]))
        self.assertTrue(comp(True).compare([1, 2, 3], [1, 3, 2]))
        self.assertTrue(comp(True).compare([1, 2, 3], [2, 1, 3]))



class TestLoaders(unittest.TestCase):

    def test_parse_value_bool(self):
        self.assertTrue(parse_value('y', bool))
        self.assertTrue(parse_value('yes', bool))
        self.assertTrue(parse_value('t', bool))
        self.assertTrue(parse_value('true', bool))
        self.assertTrue(parse_value('True', bool))
        self.assertTrue(parse_value('on', bool))
        self.assertTrue(parse_value('1', bool))
        self.assertFalse(parse_value('n', bool))
        self.assertFalse(parse_value('no', bool))
        self.assertFalse(parse_value('f', bool))
        self.assertFalse(parse_value('false', bool))
        self.assertFalse(parse_value('False', bool))
        self.assertFalse(parse_value('off', bool))
        self.assertFalse(parse_value('0', bool))
        with self.assertRaises(ValueError):
            parse_value('ok', bool)

    def test_parse_value_int(self):
        self.assertEqual(parse_value('1', int), 1)
        self.assertEqual(parse_value(1.9, int), 1)
        self.assertEqual(parse_value(None, int), None)
        with self.assertRaises(ValueError):
            parse_value('1g', int)

    def test_parse_value_float(self):
        self.assertEqual(parse_value('1.5', float), 1.5)
        self.assertEqual(parse_value(1, float), 1.0)
        self.assertEqual(parse_value(None, float), None)
        with self.assertRaises(ValueError):
            parse_value('1g', float)

    def test_BaseLoader_get_comparator(self):
        func = BaseLoader({}).get_comparator
        # default dict
        comp = func('dict')
        self.assertIsInstance(comp, comparators.DictComparator)
        self.assertFalse(comp.only_keys)
        self.assertIsNone(comp.level)
        # dict with params
        comp = func('dict(only_keys=True, level=3)')
        self.assertIsInstance(comp, comparators.DictComparator)
        self.assertTrue(comp.only_keys)
        self.assertEqual(comp.level, 3)
        # dict with wrong params
        with self.assertRaises(KeyError):
            func('dict(only_k=True)')
        # default list
        comp = func('list')
        self.assertIsInstance(comp, comparators.ListComparator)
        self.assertFalse(comp.any_order)
        # list with params
        comp = func('list(any_order=t)')
        self.assertIsInstance(comp, comparators.ListComparator)
        self.assertTrue(comp.any_order)

    def test_BaseLoader_get_block(self):
        # default block
        expect = {
            'url': '',
            'method': 'get',
            'data': {},
            'code': 200,
            'result': None,
            'handler': None,
            'skip_errors': False,
        }
        self.assertEqual(BaseLoader({}).get_block({}), expect)
        # inherited block 1
        block = dict(url='index.html', method='post', code=404)
        params = dict(url='http://test.com/site/', method='get', code=301)
        expect = {
            'url': 'http://test.com/site/index.html',
            'method': 'post',
            'data': {},
            'code': 404,
            'result': None,
            'handler': None,
            'skip_errors': False,
        }
        self.assertEqual(BaseLoader({}).get_block(block, **params), expect)
        # inherited block 2
        block = dict(url='/index.html', method='post')
        params = dict(url='http://test.com/site/', method='get', code=301)
        expect = {
            'url': 'http://test.com/index.html',
            'method': 'post',
            'data': {},
            'code': 301,
            'result': None,
            'handler': None,
            'skip_errors': False,
        }
        self.assertEqual(BaseLoader({}).get_block(block, **params), expect)

#    def test_BaseLoader_get_steps(self):
#        get_steps(

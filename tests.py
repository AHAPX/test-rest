import unittest
from unittest.mock import patch

import comparators
from loaders import parse_value, BaseLoader, YAMLLoader, get_loader
from actions import Step, Action, Actions


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
        # base
        comp = func('base')
        self.assertIsInstance(comp, comparators.BaseComparator)
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
            'handler': 'base',
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
            'handler': 'base',
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
            'handler': 'base',
            'skip_errors': False,
        }
        self.assertEqual(BaseLoader({}).get_block(block, **params), expect)

    @patch('loaders.BaseLoader.get_comparator')
    @patch('loaders.Step.__init__')
    def test_BaseLoader_get_steps_1(self, init, get_comparator):
        init.return_value = None
        get_comparator.return_value = '_comp'
        data = {
            'url': 'http://test.com/',
            'method': 'post',
            'data': '_data',
            'code': 404,
            'result': '_result',
            'handler': 'base',
            'skip_errors': False,
        }
        self.assertIsInstance(BaseLoader({}).get_steps([data], {})[0], Step)
        init.assert_called_once_with(
            url='http://test.com/',
            method='post',
            data='_data',
            expected_code=404,
            expected_data='_result',
            comparator='_comp',
            skip_errors=False,
            name=None,
        )

    @patch('loaders.BaseLoader.get_comparator')
    @patch('loaders.Step.__init__')
    def test_BaseLoader_get_steps_2(self, init, get_comparator):
        init.return_value = None
        get_comparator.return_value = '_comp'
        data = {
            'step1': {
                'url': 'http://test.com/',
                'method': 'post',
                'data': '_data',
                'code': 404,
                'result': '_result',
                'handler': 'base',
                'skip_errors': False,
            }
        }
        self.assertIsInstance(BaseLoader({}).get_steps([data], {})[0], Step)
        init.assert_called_once_with(
            url='http://test.com/',
            method='post',
            data='_data',
            expected_code=404,
            expected_data='_result',
            comparator='_comp',
            skip_errors=False,
            name='step1',
        )

    @patch('loaders.BaseLoader.get_steps')
    def test_BaseLoader_get_actions_1(self, get_steps):
        get_steps.return_value = []
        data = {
            'action1': {'steps': []}
        }
        self.assertIsInstance(BaseLoader({}).get_actions([data], {}), Actions)
        get_steps.assert_called_once_with([], BaseLoader({}).get_block({}))

    def test_BaseLoader_get_actions_2(self):
        data = {'steps': []}
        with self.assertRaises(AttributeError):
            BaseLoader({}).get_actions([data], {})

    @patch('loaders.BaseLoader.get_actions')
    def test_BaseLoader_load(self, get_actions):
        get_actions.return_value = []
        data = {'actions': []}
        loader = BaseLoader(data)
        self.assertEqual(loader.load(), [])
        get_actions.assert_called_once_with([], loader.get_block({}))
        get_actions.reset_mock()
        self.assertEqual(loader.load(), [])
        self.assertFalse(get_actions.called)
        with self.assertRaises(KeyError):
            BaseLoader({}).load()

    def test_YAMLLoader(self):
        actions = YAMLLoader('test.yaml').load()
        self.assertIsInstance(actions, Actions)
        self.assertEqual(len(actions.actions), 1)
        action = actions.actions[0]
        self.assertIsInstance(action, Action)
        self.assertEqual(action.name, 'main')
        self.assertEqual(len(action.steps), 1)
        step = action.steps[0]
        self.assertEqual(step.url, 'http://test.com/')
        self.assertEqual(step.method, 'post')
        self.assertEqual(step.expected_code, 200)
        self.assertEqual(step.expected_data, {'rc': True})
        self.assertIsInstance(step.comparator, comparators.DictComparator)

    def test_get_loader(self):
        self.assertEqual(get_loader('yaml'), YAMLLoader)
        self.assertEqual(get_loader('yml'), YAMLLoader)
        self.assertIsNone(get_loader('xml'))


class TestActions(unittest.TestCase):

    def test_Step_init(self):
        params = dict(
            url='_url', method='_method', data='_data', expected_code='_code',
            expected_data='_result', comparator='_comp', skip_errors=True,
            name='_name'
        )
        step = Step(**params)
        self.assertEqual(step.url, '_url')
        self.assertEqual(step.method, '_method')
        self.assertEqual(step.expected_code, '_code')
        self.assertEqual(step.expected_data, '_result')
        self.assertEqual(step.comparator, '_comp')
        self.assertTrue(step.skip_errors)
        self.assertEqual(step.name, '_name')

    def test_Step_name(self):
        step = Step(url='http://test.com', name='step1')
        self.assertEqual(step.name, 'step1')
        Action([step], name='action1')
        self.assertEqual(step.name, 'action1.step1')

    def test_Step_get_variable(self):
        # add step1
        step1 = Step(url='http://test.com', name='step1')
        step1.results = {'rc': '_rc1'}
        # should not be found withoud connection with action
        self.assertEqual(step1.get_variable('action1.step1.rc'), 'None')
        action1 = Action([step1], 'action1')
        # should be found after connection
        self.assertEqual(step1.get_variable('action1.step1.rc'), '_rc1')
        # add step2
        step2 = Step(url='http://test.com/auth', name='step1')
        step2.results = {'rc': '_rc2'}
        action2 = Action([step2], 'action2')
        # should not be found for step1 and found for step2
        self.assertEqual(step1.get_variable('action2.step1.rc'), 'None')
        self.assertEqual(step2.get_variable('action2.step1.rc'), '_rc2')
        Actions([action1, action2])
        # should be found for step1 after connect action with parent
        self.assertEqual(step1.get_variable('action2.step1.rc'), '_rc2')

    def test_Step_get_value(self):
        step = Step(url='http://test.com')
        step.results = {
            'key1': 'value1',
            'key2': {
                'key3': 'value3',
                'key4': {
                    'key5': 'value5'
                }
            }
        }
        self.assertEqual(step.get_value('key1'.split('.')), 'value1')
        self.assertEqual(step.get_value('key2.key3'.split('.')), 'value3')
        self.assertEqual(step.get_value('key2.key4'.split('.')), {'key5': 'value5'})
        self.assertEqual(step.get_value('key2.key4.key5'.split('.')), 'value5')
        self.assertIsNone(step.get_value('key6'.split('.')))

    def test_Step_url(self):
        step = Step(url='http://test.com?token=%action1.step1.token%', name='step1')
        step.results = {'token': '1234'}
        Action([step], 'action1')
        self.assertEqual(step.url, 'http://test.com?token=1234')

    def test_Step_data(self):
        data = {
            'token': '%action1.step1.token%',
            'action': '%action2.step1.action%',
            'control': True,
        }
        expect = {
            'token': '1234',
            'action': 'add',
            'control': True,
        }
        step1 = Step(url='http://test.com', data=data, name='step1')
        step1.results = {'token': '1234'}
        action1 = Action([step1], 'action1')
        step2 = Step(url='/', name='step1')
        step2.results = {'action': 'add'}
        action2 = Action([step2], 'action2')
        Actions([action1, action2])
        self.assertEqual(step1.data, expect)

    @patch('actions.requests.get')
    def test_Step_run_get(self, get):
        class ResponseX():
            status_code = 200
            content = b'ok'

        resp = ResponseX()
        get.return_value = resp
        step = Step(url='http://test.com', method='get')
        # check only status code
        with self.assertLogs('actions', level='INFO'):
            step.run()
        # set expected_data and test
        resp.content = b'{"test": true}'
        step.expected_data = {'test': True}
        with self.assertLogs('actions', level='INFO'):
            step.run()
        # empty content
        resp.content = b''
        with self.assertLogs('actions') as cm:
            step.run()
            self.assertEqual(cm.output, [
                'ERROR:actions:response data "None" is not equal "{\'test\': True}"',
                'WARNING:actions:None GET http://test.com'
            ])
        # set wrong params and test
        resp.status_code = 404
        resp.content = b'{"test": false}'
        with self.assertLogs('actions') as cm:
            step.run()
            self.assertEqual(cm.output, [
                'ERROR:actions:status code 404 not equal 200',
                'ERROR:actions:response data "{\'test\': False}" is not equal "{\'test\': True}"',
                'WARNING:actions:None GET http://test.com'
            ])
        # skip errors
        step.skip_erros = True
        with self.assertLogs('actions', level='WARNING'):
            step.run()

    @patch('actions.requests.post')
    def test_Step_run_post(self, post):
        class ResponseX():
            status_code = 200
            content = b'ok'

        resp = ResponseX()
        post.return_value = resp
        step = Step(url='http://test.com', method='post')
        with self.assertLogs('actions', level='INFO'):
            step.run()

    @patch('actions.Step.run')
    def test_Action_run(self, run):
        action = Action([Step('url1'), Step('url2')])
        action.run()
        self.assertEqual(run.call_count, 2)

    @patch('actions.Action.run')
    def test_Actions_run(self, run):
        actions = Actions([Action(), Action()])
        actions.run()
        self.assertEqual(run.call_count, 2)

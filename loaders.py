from distutils.util import strtobool
from urllib.parse import urljoin
import re

import yaml

import expectators
from actions import Step, Action, Actions


EXPECTATORS = {
    'base': {
        'class': expectators.BaseExpectator,
    },
    'dict': {
        'class': expectators.DictExpectator,
        'args': {
            'only_keys': bool,
            'level': int,
        }
    },
    'list': {
        'class': expectators.ListExpectator,
        'args': {
            'any_order': bool,
        }
    }
}


TYPES = {
    bool: lambda a: bool(strtobool(a)),
    int: lambda a: int(a) if a else None,
    float: lambda a: float(a) if a else None,
}


def parse_value(value, type):
    return TYPES.get(type, lambda a: a)(value)


class BaseLoader(object):

    def __init__(self, data):
        self.data = data
        self.actions = None

    def load(self):
        if self.actions is None:
            self.actions = self.get_actions(self.data['actions'], self.get_block(self.data))
        return self.actions

    def get_block(
        self, block, url='', method='get', data={}, code=200, result=None,
        handler=None, skip_errors=False
    ):
        return {
            'url': urljoin(url, block.get('url', '')),
            'method': block.get('method', method),
            'data': block.get('data', data),
            'code': block.get('code', code),
            'result': block.get('result', result),
            'handler': block.get('handler', handler),
            'skip_errors': block.get('skip_errors', skip_errors),
        }

    def get_actions(self, actions, params):
        result = Actions()
        for action in actions:
            name, data = action.popitem()
            steps = self.get_steps(data.get('steps'), self.get_block(data, **params))
            result.add_action(Action(steps, name))
        return result

    def get_steps(self, steps, params):
        result = []
        for step in steps:
            if len(step) > 1 or not isinstance(step[list(step.keys())[0]], dict):
                name, data = None, step
            else:
                name, data = step.popitem()
            step_params = self.get_block(data, **params)
            step_params['handler'] = self.get_expectator(step_params['handler'])
            result.append(Step(
                url=step_params.get('url'),
                method=step_params.get('method'),
                data=step_params.get('data'),
                expected_code=step_params.get('code'),
                expected_data=step_params.get('result'),
                expectator=step_params.get('handler'),
                skip_errors=step_params.get('skip_errors'),
                name=name,
            ))
        return result

    def get_expectator(self, text):
        exp = re.search('(?P<name>\w+)(?:\((?P<args>.+)\))?', text)
        name, args = exp.group('name'), exp.group('args')
        if args:
            args = dict((a.strip().split('=') for a in args.split(',')))
        else:
            args = {}
        exp = EXPECTATORS[name]
        kwargs = {}
        for key, value in args.items():
            kwargs[key] = parse_value(value, exp['args'][key])
        return exp['class'](**kwargs)


class YAMLLoader(BaseLoader):

    def __init__(self, filename):
        super(YAMLLoader, self).__init__(yaml.load(open(filename)))



LOADERS = {
    'yaml': YAMLLoader,
    'yml': YAMLLoader,
}


def get_loader(format):
    return LOADERS.get(format)

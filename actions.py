import json
from logging import StreamHandler
import re

import requests
import colorlog

from comparators import BaseComparator


logger = colorlog.logging.getLogger(__name__)
handler = StreamHandler()
handler.setLevel('INFO')
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)
logger.setLevel('INFO')


class Step(object):

    def __init__(
        self, url, method='get', data={}, expected_code=200, expected_data=None,
        comparator=BaseComparator(), skip_errors=False, name=None
    ):
        self._parent = None
        self._url = url
        self.method = method
        self._data = data
        self.expected_code = expected_code
        self.expected_data = expected_data
        self.comparator = comparator
        self.skip_errors = skip_errors
        self._name = name
        self.results = {}
        super(Step, self).__init__()

    def __str__(self):
        return '{}: {} {} = {}'.format(
            self.name, self.method.upper(),
            self.url, self.expected_code
        )

    def run(self):
        logger_method = logger.info
        if self.method == 'get':
            resp = requests.get(self.url)
        elif self.method == 'post':
            resp = requests.post(self.url, data=self.data)
        if not BaseComparator().compare(resp.status_code, self.expected_code):
            if not self.skip_errors:
                logger.error('status code %d not equal %d', resp.status_code, self.expected_code)
            logger_method = logger.warning
        if self.expected_data is not None:
            try:
                self.results = json.loads(resp.content.decode())
            except ValueError:
                self.results = None
            if not self.comparator.compare(data=self.results, expect=self.expected_data):
                if not self.skip_errors:
                    logger.error('response data "%s" is not equal "%s"', self.results, self.expected_data)
                logger_method = logger.warning
        logger_method('%s %s %s', self.name, self.method.upper(), self.url)

    @property
    def name(self):
        if self._parent and self._parent.name:
            return '{}.{}'.format(self._parent.name, self._name if self._name else '_')
        return self._name

    @property
    def url(self):
        variables = re.compile('%(?P<variable>[\w\.]+)%').findall(self._url)
        if variables:
            url = self._url
            for var in variables:
                url = url.replace('%{}%'.format(var), self.get_variable(var))
            return url
        return self._url

    @property
    def data(self):
        data = {}
        for key, value in self._data.items():
            if isinstance(value, str):
                variable = re.compile('%(?P<variable>[\w\.]+)%').match(value)
                if variable:
                    value = self.get_variable(variable.group('variable'))
            data[key] = value
        return data

    def connect(self, parent):
        self._parent = parent

    def get_variable(self, variable):
        return str(self._parent.get_variable(variable) if self._parent else None)

    def get_value(self, path):
        data = self.results
        for level in path:
            data = data.get(level, {})
        return data if data != {} else None


class Action(object):

    def __init__(self, steps=[], name=None):
        self._parent = None
        self.name = name
        self.steps = []
        for step in steps:
            self.add_step(step)

    def __str__(self):
        return '{}: [{}]'.format(self.name, ' | '.join(map(str, self.steps)))

    def add_step(self, step):
        self.steps.append(step)
        step.connect(self)

    def run(self):
        for step in self.steps:
            step.run()

    def connect(self, parent):
        self._parent = parent

    def get_variable(self, variable):
        path = variable.split('.')
        if path[0] == self.name:
            for step in self.steps:
                if step.name == '.'.join(path[:2]):
                    return step.get_value(path[2:])
        else:
            return self._parent.get_variable(variable) if self._parent else None
        return None


class Actions(object):

    def __init__(self, actions=[]):
        self.actions = []
        for action in actions:
            self.add_action(action)

    def __str__(self):
        return '\n'.join(map(str, self.actions))

    def add_action(self, action):
        self.actions.append(action)
        action.connect(self)

    def run(self):
        for action in self.actions:
            action.run()

    def get_variable(self, variable):
        path = variable.split('.')
        for action in self.actions:
            if action.name == path[0]:
                return action.get_variable(variable)

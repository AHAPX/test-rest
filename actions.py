import json
import logging
import logging.handlers

import requests

from comparators import BaseComparator
from expectators import BaseExpectator

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class Step(object):

    _parent = None

    def __init__(
        self, url, method='get', data={}, expected_code=200, expected_data=None,
        expectator=BaseExpectator(), name=None
    ):
        self.url = url
        self.method = method
        self.data = data
        self.expected_code = expected_code
        self.expected_data = expected_data
        self.expectator = expectator
        self._name = name
        super(Step, self).__init__()

    def run(self):
        errors = False
        if self.method == 'get':
            resp = requests.get(self.url)
        elif self.method == 'post':
            resp = requests.post(self.url, data=self.data)
        if not BaseComparator().compare(resp.status_code, self.expected_code):
            logger.warning('status code %d not equal %d', resp.status_code, self.expected_code)
            errors = True
        if self.expected_data is not None:
            data = json.loads(resp.content.decode())
            if not self.expectator.compare(data=data, expect=self.expected_data):
                logger.warning('response data "%s" is not equal "%s"', data, self.expected_data)
                errors = True
        logger.info(
            '%s %s %s %s', self.name, self.method.upper(), self.url,
            'FAIL' if errors else 'ok'
        )

    @property
    def name(self):
        if self._parent and self._parent.name:
            return '{}.{}'.format(self._parent.name, self._name if self._name else '_')
        return self._name

    def connect(self, parent):
        self._parent = parent

    def __str__(self):
        return '{}: {} {} = {}'.format(
            self.name, self.method.upper(),
            self.url, self.expected_code
        )


class Action(object):

    def __init__(self, steps=[], name=None):
        self.name = name
        self.steps = steps
        for step in self.steps:
            step.connect(self)

    def add_step(self, step):
        self.steps.append(step)
        step.connect(self)

    def run(self):
        for step in self.steps:
            step.run()

    def __str__(self):
        return '{}: [{}]'.format(self.name, ' | '.join(map(str, self.steps)))

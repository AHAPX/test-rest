import json
import logging

import requests

from comparators import BaseComparator
from expectators import BaseExpectator, DictExp, ListExp


logger = logging.getLogger(__name__)


class Step(object):

    def __init__(
        self, url, method='get', data={}, expected_code=200, expected_data=None,
        expectator=BaseExpectator()
    ):
        self.url = url
        self.method = method
        self.data = data
        self.expected_code = expected_code
        self.expected_data = expected_data
        self.expectator = expectator
        super(Step, self).__init__()

    def run(self):
        if self.method == 'get':
            resp = requests.get(self.url)
        elif self.method == 'post':
            resp = requests.post(self.url, data=self.data)
        if not BaseComparator().compare(resp.status_code, self.expected_code):
            logging.warning('status code %d not equal %d',
                resp.status_code, self.expected_code
            )
        if self.expected_data is not None:
            data = json.loads(resp.content.decode())
            if not self.expectator.compare(data=data, expect=self.expected_data):
                logging.warning('response data "%s" is not equal "%s"', data, self.expected_data)


class Action(object):

    def __init__(self, steps=[]):
        self.steps = steps

    def run(self):
        for step in self.steps:
            step.run()

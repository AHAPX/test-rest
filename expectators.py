from comparators import BaseComparator, DictComp, ListComp


class BaseExpectator(object):

    def __init__(self, comparator=BaseComparator()):
        self.comparator = comparator

    def compare(self, data, expect):
        return self.comparator.compare(data, expect)


class DictExp(BaseExpectator):

    def __init__(self, only_keys=False, level=None):
        super(DictExp, self).__init__(DictComp(only_keys, level))


class ListExp(BaseExpectator):

    def __init__(self, any_order=False):
        super(ListExp, self).__init__(ListComp(any_order))


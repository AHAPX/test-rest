from comparators import BaseComparator, DictComparator, ListComparator


class BaseExpectator(object):

    def __init__(self, comparator=BaseComparator()):
        self.comparator = comparator

    def compare(self, data, expect):
        return self.comparator.compare(data, expect)


class DictExpectator(BaseExpectator):

    def __init__(self, only_keys=False, level=4):
        super(DictExpectator, self).__init__(DictComparator(only_keys, level))


class ListExpectator(BaseExpectator):

    def __init__(self, any_order=False):
        super(ListExpectator, self).__init__(ListComparator(any_order))

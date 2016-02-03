class BaseComparator(object):

    def compare(self, data, expect):
        return data == expect


class DictComparator(BaseComparator):

    def __init__(self, only_keys=False, level=None):
        self.only_keys = only_keys
        self.level = level

    def __compare_keys(self, data, expect, level):
        if level is None or level > 0:
            result = data.keys() == expect.keys()
            if not result:
                return False
            for key, exp in expect.items():
                if isinstance(exp, dict):
                    value = data.get(key)
                    if not isinstance(value, dict):
                        return False
                    if not self.__compare_keys(value, exp, level - 1 if level else None):
                        return False
        return True

    def compare(self, data, expect):
        if self.only_keys:
            return self.__compare_keys(data, expect, self.level)
        return data == expect


class ListComparator(BaseComparator):

    def __init__(self, any_order=False):
        self.any_order = any_order

    def compare(self, data, expect):
        if self.any_order:
            return sorted(map(str, data)) == sorted(map(str, data))
        return data == expect

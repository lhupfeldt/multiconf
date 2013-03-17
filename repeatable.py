from collections import OrderedDict


class Repeatable(OrderedDict):
    _frozen = False

    def freeze(self):
        for item in self.itervalues():
            if not item._frozen:
                item.freeze()

    def _user_validate_recursively(self):
        for dict_entry in self.values():
            dict_entry._user_validate_recursively()

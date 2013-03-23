from collections import OrderedDict


class Repeatable(OrderedDict):
    _mc_frozen = False

    def _mc_freeze(self):
        for item in self.itervalues():
            if not item._mc_frozen:
                item._mc_freeze()

    def _user_validate_recursively(self):
        for dict_entry in self.values():
            dict_entry._user_validate_recursively()


    def _mc_value(self, env):
        return self

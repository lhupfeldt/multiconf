from collections import OrderedDict
from attribute import Attribute

class Repeatable(OrderedDict):
    _mc_frozen = False

    def _mc_freeze(self):
        self._mc_frozen = True
        for item in self.itervalues():
            self._mc_frozen &= item._mc_freeze()
        return self._mc_frozen

    def _user_validate_recursively(self):
        for dict_entry in self.values():
            dict_entry._user_validate_recursively()

    def setdefault(self, key, other):
        if isinstance(other, Attribute) and key in self:
            attr = self[key]
            if attr._mc_frozen:
                return attr
            return attr.merge(other)
        return super(Repeatable, self).setdefault(key, other)

    def _mc_value(self, env):
        return self

from abc import ABCMeta
from abc import abstractmethod

# ------------------------------------------------------------

class Interface(metaclass=ABCMeta):
    @abstractmethod
    def exec(self, shared_vars):
        pass

    @abstractmethod
    def to_str(self):
        pass

class AbstractFormula(Interface):
    def print(self):
        print(self.to_str())

class Prop(Interface):
    def __init__(self, label, func):
        self.label = label
        self.func = func

    def exec(self, shared_vars):
        return self.func(shared_vars)

    def to_str(self):
        return self.label

    def print(self):
        print(self.to_str())

class Or(AbstractFormula):
    def __init__(self, g, h):
        self.g = g
        self.h = h

    def exec(self, shared_vars):
        res_g = self.g.exec(shared_vars)
        res_h = self.h.exec(shared_vars)
        assert (type(res_g) == bool) and (type(res_h) == bool)
        return res_g or res_h

    def to_str(self):
        return 'or ({0}, {1})'.format(self.g.to_str(), self.h.to_str())

class And(AbstractFormula):
    def __init__(self, g, h):
        self.g = g
        self.h = h

    def exec(self, shared_vars):
        res_g = self.g.exec(shared_vars)
        res_h = self.h.exec(shared_vars)
        assert (type(res_g) == bool) and (type(res_h) == bool)
        return res_g and res_h

    def to_str(self):
        return 'and ({0}, {1})'.format(self.g.to_str(), self.h.to_str())

class Not(AbstractFormula):
    def __init__(self, g):
        self.g = g

    def exec(self, shared_vars):
        res_g = self.g.exec(shared_vars)
        assert type(res_g) == bool
        return not res_g

    def to_str(self):
        return 'not ({0})'.format(self.g.to_str())

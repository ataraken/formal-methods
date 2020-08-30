import os
import sys
import pygraphviz as pgv
from abc import ABCMeta
from abc import abstractmethod

sys.path.append('../../../ddsv/src/python')

import ddsv

# ------------------------------------------------------------

class Interface(metaclass=ABCMeta):
    @abstractmethod
    def exec(self, shared_vars, out_list):
        pass

    @abstractmethod
    def to_str(self):
        pass

    @abstractmethod
    def to_graph_str(self):
        pass

class AbstractFormula(Interface):
    def exec(self, shared_vars, out_list):
        res_list = [ f.exec(shared_vars, out_list) for f in self._f_list ]
        is_true = self._is_true(res_list)

        if is_true:
            out_list.append(self.to_str())

        return is_true

    @abstractmethod
    def _is_true(self, list):
        pass

    def to_graph_str(self, list):
        return '\\n'.join(list)

    def print(self, shared_vars):
        print(self.to_str())

class Prop(Interface):
    def __init__(self, label, func):
        self.label = label
        self.func = func
        self.str = None

    def exec(self, shared_vars, out_list):
        res = self.func(shared_vars)
        if res:
            out_list.append(self.to_str())
        return res

    def to_str(self):
        return self.label

    def to_graph_str(self):
        return self.str

class Or(AbstractFormula):
    def __init__(self, g, h):
        self._f_list = [ g, h ]
        self.str = None

    def _is_true(self, list):
        assert 2 <= len(list)
        return any(list)

    def to_str(self):
        str = ', '.join([ f.to_str() for f in self._f_list ])
        str = 'or ({0})'.format(str)
        return str

class And(AbstractFormula):
    def __init__(self, g, h):
        self._f_list = [ g, h ]
        self.str = None

    def _is_true(self, list):
        assert 2 <= len(list)
        return all(list)

    def to_str(self):
        str = ', '.join([ f.to_str() for f in self._f_list ])
        str = 'and ({0})'.format(str)
        return str

class Not(AbstractFormula):
    def __init__(self, g):
        self._f_list = [ g ]
        self.str = None

    def _is_true(self, list):
        assert len(list) == 1
        return not list[0]

    def to_str(self):
        assert len(self._f_list) == 1
        return 'not ({0})'.format(self._f_list[0].to_str())

class LtsTblMarker:
    def __init__(self, lts_tbl, formula):
        self._idx_of_prev_state = lts_tbl._idx_of_prev_state
        self._idx_of_who        = lts_tbl._idx_of_who
        self._idx_of_tran       = lts_tbl._idx_of_tran
        self._idx_of_direction  = lts_tbl._idx_of_direction
        self._tbl               = lts_tbl._tbl
        self._key_to_id         = lts_tbl._key_to_id

        self._dir_name = 'img'

        self._formula = formula

    def save_graph(self, name):
        G = pgv.AGraph(directed=True, strict=False)

        for i, k in enumerate(self._tbl):
            list = []
            is_true = self._formula.exec(k.shared_vars, list)
            label = '{0}\\n{1}'.format(k.to_graph_str(self._key_to_id[k]), self._formula.to_graph_str(list))

            if is_true:
                G.add_node(label, style='filled', fillcolor='palegreen')
            else:
                G.add_node(label)

        for k, pair in [(k, pair) for k in (self._tbl) for pair in self._tbl[k] if pair != (None, None, None, None)]:
            if pair[self._idx_of_direction] == 'foward':
                list = []
                self._formula.exec(pair[self._idx_of_prev_state].shared_vars, list)
                src = '{0}\\n{1}'.format( \
                    pair[self._idx_of_prev_state].to_graph_str(self._key_to_id[pair[self._idx_of_prev_state]]), \
                    self._formula.to_graph_str(list))

                list = []
                self._formula.exec(k.shared_vars, list)
                dst = '{0}\\n{1}'.format(k.to_graph_str(self._key_to_id[k]), self._formula.to_graph_str(list))
            elif pair[self._idx_of_direction] == 'reverse':
                list = []
                self._formula.exec(k.shared_vars, list)
                src = '{0}\\n{1}'.format(k.to_graph_str(self._key_to_id[k]), self._formula.to_graph_str(list))

                list = []
                self._formula.exec(pair[self._idx_of_prev_state].shared_vars, list)
                dst = '{0}\\n{1}'.format( \
                    pair[self._idx_of_prev_state].to_graph_str(self._key_to_id[pair[self._idx_of_prev_state]]), \
                    self._formula.to_graph_str(list))

            action = '{0}.{1}'.format(pair[self._idx_of_who].name, pair[self._idx_of_tran].label)
            G.add_edge(src, dst, label=action)

        sorted(G.edges(keys=True))
        if not os.path.isdir(self._dir_name):
            os.mkdir(self._dir_name)

        G.layout(prog='dot')
        G.draw(os.path.join(self._dir_name, '{0}.png'.format(name)))

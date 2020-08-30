import copy
import os

import pygraphviz as pgv

from abc import ABCMeta
from abc import abstractmethod

class SharedVarsInterface(metaclass=ABCMeta):
    @abstractmethod
    def clone(self):
        pass

    @abstractmethod
    def equal(self, target):
        pass

    @abstractmethod
    def to_str(self):
        pass

    @abstractmethod
    def to_graph_str(self):
        pass

class Action(metaclass=ABCMeta):
    @abstractmethod
    def exec(self, process, dest, src):
        pass

class Guard(metaclass=ABCMeta):
    @abstractmethod
    def exec(self, process, state):
        pass

class GuardTrue(Guard):
    def exec(self, process, state):
        return True

class ActionNop(Action):
    def exec(self, process, dest, src):
        pass

class StateTransition:
    def __init__(self, location, trans_list):
        self.location = location
        self.transitions = trans_list

class Transition:
    def __init__(self, label, location, guard, action):
        self.label = label
        self.location = location
        self.guard = guard
        self.action = action

    def to_str(self):
        return '{0} {1}'.format(self.label, self.location)

class Process:
    _dir_name = 'img'

    def __init__(self, name, state_trans):
        self.name = name
        self.state_trans = state_trans

    def next_trans(self, location):
        for t in self.state_trans:
            if t.location == location:
                return t.transitions

    def save_graph(self, name):
        G = pgv.AGraph(directed=True, strict=False)

        for st in self.state_trans:
            G.add_node('{0}{1}'.format(self.name, st.location))

        for st in self.state_trans:
            src_location = '{0}{1}'.format(self.name, st.location)
            for t in st.transitions:
                G.add_edge(src_location, '{0}{1}'.format(self.name, t.location), label=t.label)

        sorted(G.edges(keys=True))
        if not os.path.isdir(self._dir_name):
            os.mkdir(self._dir_name)

        G.layout(prog='dot')
        G.draw(os.path.join(self._dir_name, '{0}.png'.format(name)))

class State:
    def __init__(self, r0=None, p_list=None):
        if r0 != None and p_list != None:
            self.p_list = p_list
            self.location = { p:p.state_trans[0].location for p in self.p_list }
            self.shared_vars = r0
            self._is_deadlock = True

    def clone(self):
        dst = State()
        dst.location = copy.copy(self.location)
        dst.shared_vars = self.shared_vars.clone()
        dst.p_list = self.p_list
        dst._is_deadlock = True
        return dst

    def check_deadlock(self):
        self._is_deadlock = False

    def is_deadlock(self):
        return self._is_deadlock

    def equal(self, target):
        return self._is_same_location(target) and self._is_same_shared_vars(target)

    def name(self):
        return ' '.join(['{0}{1}'.format(p.name, self.location[p]) for p in self.p_list])

    def to_str(self):
        return '{0:8} {1}'.format(self.name(), self.shared_vars.to_str())

    def to_graph_str(self, idx):
        return '{0}\n{1:8}\n{2}'.format(idx, self.name(), self.shared_vars.to_graph_str())

    def _is_same_location(self, target):
        l0 = ' '.join([self.location[p] for p in self.p_list])
        l1 = ' '.join([target.location[p] for p in self.p_list])
        return l0 == l1

    def _is_same_shared_vars(self, target):
        return self.shared_vars.equal(target.shared_vars)

class Path:
    def create(path, state, tran, process):
        new_path = copy.deepcopy(path)
        new_path._add(state, tran, process)
        return new_path

    def __init__(self, s0):
        self.list = [ {'s':s0, 't':None, 'p':None} ]

    def _add(self, s, t, p):
        self.list.insert(0, {'s':s, 't':t, 'p':p})

    def get_state(self):
        return (self.list[0])['s']

    def print(self):
        print('--------------------')
        for idx, i in enumerate(reversed(self.list)):
            if i['t'] == None:
                str_tran = '{0:4} {1:10}'.format('---', '---')
            else:
                str_tran = '{0:4} {1:10}'.format(i['p'].name, i['t'].label)
            print('{0:4} {1:14} {2:32}'.format(idx, str_tran, i['s'].to_str()))

class LtsTbl:
    _dir_name = 'img'

    def __init__(self, key):
        self._idx_of_prev_state = 0
        self._idx_of_who = 1
        self._idx_of_tran = 2
        self._idx_of_direction = 3
        self._tbl = { key: [ (None, None, None, None) ] }
        self._key_to_id = { key:0 }

    def add(self, key, prev_state, who, tran):
        ret = False
        keys = [ k for k in self._tbl.keys() if k.equal(key) ]
        if not keys:
            self._tbl[key] = [ (prev_state, who, tran, 'foward') ]
            self._key_to_id[key] = len(self._key_to_id)
            ret = True
        elif keys and [ k for k in self._tbl.keys() if k.equal(prev_state) ]:
            self._tbl[prev_state].append((keys[0], who, tran, 'reverse'))
        return ret

    def save_graph(self, name):
        G = pgv.AGraph(directed=True, strict=False)

        for i, k in enumerate(self._tbl):
            if self._tbl[k][self._idx_of_prev_state] == (None, None, None, None):
                G.add_node(k.to_graph_str(self._key_to_id[k]), style='filled', fillcolor='cyan')
            elif k.is_deadlock():
                G.add_node(k.to_graph_str(self._key_to_id[k]), style='filled', fillcolor='pink')
            else:
                G.add_node(k.to_graph_str(self._key_to_id[k]))

        for k, pair in [(k, pair) for k in (self._tbl) for pair in self._tbl[k] if pair != (None, None, None, None)]:
            if pair[self._idx_of_direction] == 'foward':
                src = pair[self._idx_of_prev_state].to_graph_str(self._key_to_id[pair[self._idx_of_prev_state]])
                dst = k.to_graph_str(self._key_to_id[k])
            elif pair[self._idx_of_direction] == 'reverse':
                src = k.to_graph_str(self._key_to_id[k])
                dst = pair[self._idx_of_prev_state].to_graph_str(self._key_to_id[pair[self._idx_of_prev_state]])

            action = '{0}.{1}'.format(pair[self._idx_of_who].name, pair[self._idx_of_tran].label)
            G.add_edge(src, dst, label=action)

        sorted(G.edges(keys=True))
        if not os.path.isdir(self._dir_name):
            os.mkdir(self._dir_name)

        G.layout(prog='dot')
        G.draw(os.path.join(self._dir_name, '{0}.png'.format(name)))

def concurrent_composition(process_list, r0, name):
    s0 = State(r0, process_list)
    lts_tbl = bfs(process_list, s0)
    return lts_tbl

def bfs(process_list, s0):
    lts_tb = LtsTbl(s0)
    path = Path(s0)
    queue = [ path ]

    while queue:
        path = queue.pop(0)
        s = path.get_state()
        for p, tran in [ (p, tran) for p in process_list for tran in p.next_trans(s.location[p]) if tran.guard.exec(p, s)]:
            t = s.clone()
            t.location[p] = tran.location

            tran.action.exec(p, t, s)
            s.check_deadlock()

            if lts_tb.add(t, s, p, tran):
                queue.append(Path.create(path, t, tran, p))

        if s.is_deadlock():
            path.print()

    return lts_tb

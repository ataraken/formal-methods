import copy
from abc import ABCMeta
from abc import abstractmethod

import ddsv

class SharedVars(ddsv.SharedVarsInterface):
    _len_of_queue = 3

    def __init__(self, process_list):
        self._p_list = process_list
        self.c = [ 0 for p in process_list ]

    def clone(self):
        return copy.deepcopy(self)

    def equal(self, target):
        res = True
        for s, t in zip(self.c, target.c):
            if s != t:
                res = False
                break
        return res

    def to_str(self):
        str = ''
        for i, v in enumerate(self.c):
            str += 'c[{0}]={1} '.format(i, v)
        return str[:-1]

    def to_graph_str(self):
        return self.to_str()

class GuardQueNotEmpty(ddsv.Guard):
    def exec(self, process, state):
        idx = state.p_list.index(process)
        return (0 < state.shared_vars.c[idx])

class GuardQueNotFull(ddsv.Guard):
    def exec(self, process, state):
        idx = (state.p_list.index(process) + 1) % len(state.p_list)
        return state.shared_vars.c[idx] < state.shared_vars._len_of_queue

class ActionDeque(ddsv.Action):
    def exec(self, process, dest, src):
        idx = dest.p_list.index(process)
        dest.shared_vars.c[idx] = src.shared_vars.c[idx] - 1

class ActionEnque(ddsv.Action):
    def exec(self, process, dest, src):
        idx = (dest.p_list.index(process) + 1) % len(dest.p_list)
        dest.shared_vars.c[idx] = src.shared_vars.c[idx] + 1

state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('deque', '1', GuardQueNotEmpty(), ActionDeque())]),
    ddsv.StateTransition('1', [ddsv.Transition('enque', '0', GuardQueNotFull(), ActionEnque())])
]

P = ddsv.Process('P', state_trans_list)
Q = ddsv.Process('Q', state_trans_list)

process_list = [P, Q]
shared_vars = SharedVars(process_list)
shared_vars.c[process_list.index(P)] = 2

lts_tbl = ddsv.concurrent_composition(process_list, shared_vars, 'm_que1')
lts_tbl.save_graph('m_que1')

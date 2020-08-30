import copy
from abc import ABCMeta
from abc import abstractmethod

import ddsv

class SharedVars(ddsv.SharedVarsInterface):
    def __init__(self):
        self.mutex = False
        self.x = 0
        self.t1 = 0
        self.t2 = 0

    def clone(self):
        return copy.deepcopy(self)

    def equal(self, target):
        return (self.mutex == target.mutex) and (self.x == target.x) and (self.t1 == target.t1) and (self.t2 == target.t2)

    def to_str(self):
        return 'm={0:2} x={1:2} t1={2:2} t2={3:2}'.format(self.mutex, self.x, self.t1, self.t2)

    def to_graph_str(self):
        return 'm={0:1} x={1} t1={2} t2={3}'.format(self.mutex, self.x, self.t1, self.t2)

class ActionPRead(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.t1 = src.shared_vars.x

class ActionPInc(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.t1 = src.shared_vars.t1 + 1

class ActionPWrite(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.x = src.shared_vars.t1

p_state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('read',   '1', ddsv.GuardTrue(), ActionPRead())]),
    ddsv.StateTransition('1', [ddsv.Transition('inc',    '2', ddsv.GuardTrue(), ActionPInc())]),
    ddsv.StateTransition('2', [ddsv.Transition('write',  '3', ddsv.GuardTrue(), ActionPWrite())]),
    ddsv.StateTransition('3', [])
]

class ActionQRead(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.t2 = src.shared_vars.x

class ActionQInc(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.t2 = src.shared_vars.t2 + 1

class ActionQWrite(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.x = src.shared_vars.t2

q_state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('read',   '1', ddsv.GuardTrue(), ActionQRead())]),
    ddsv.StateTransition('1', [ddsv.Transition('inc',    '2', ddsv.GuardTrue(), ActionQInc())]),
    ddsv.StateTransition('2', [ddsv.Transition('write',  '3', ddsv.GuardTrue(), ActionQWrite())]),
    ddsv.StateTransition('3', [])
]

P = ddsv.Process('P', p_state_trans_list)
Q = ddsv.Process('Q', q_state_trans_list)

P.save_graph('m_inc2_P')
Q.save_graph('m_inc2_Q')

lts_tbl = ddsv.concurrent_composition([P, Q], SharedVars(), 'm_inc2')
lts_tbl.save_graph('m_inc2')

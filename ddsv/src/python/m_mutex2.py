import copy
from abc import ABCMeta
from abc import abstractmethod

import ddsv

class SharedVars(ddsv.SharedVarsInterface):
    def __init__(self):
        self.m0 = False
        self.m1 = False

    def clone(self):
        return copy.deepcopy(self)

    def equal(self, target):
        return (self.m0 == target.m0) and (self.m1 == target.m1)

    def to_str(self):
        return 'm0={0:1} m1={1:1}'.format(self.m0, self.m1)

    def to_graph_str(self):
        return 'm0={0:1} m1={1:1}'.format(self.m0, self.m1)

class GuardLock0(ddsv.Guard):
    def exec(self, process, state):
        return not state.shared_vars.m0

class GuardLock1(ddsv.Guard):
    def exec(self, process, state):
        return not state.shared_vars.m1

class ActionLock0(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.m0 = True

class ActionLock1(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.m1 = True

class ActionUnlock0(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.m0 = False

class ActionUnlock1(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.m1 = False

p_state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('lock0',    '1', GuardLock0(), ActionLock0())]),
    ddsv.StateTransition('1', [ddsv.Transition('lock1',    '2', GuardLock1(), ActionLock1())]),
    ddsv.StateTransition('2', [ddsv.Transition('unlock1',  '3', ddsv.GuardTrue(), ActionUnlock1())]),
    ddsv.StateTransition('3', [ddsv.Transition('unlock0',  '0', ddsv.GuardTrue(), ActionUnlock0())])
]

q_state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('lock1',    '1', GuardLock1(), ActionLock1())]),
    ddsv.StateTransition('1', [ddsv.Transition('lock0',    '2', GuardLock0(), ActionLock0())]),
    ddsv.StateTransition('2', [ddsv.Transition('unlock0',  '3', ddsv.GuardTrue(), ActionUnlock0())]),
    ddsv.StateTransition('3', [ddsv.Transition('unlock1',  '0', ddsv.GuardTrue(), ActionUnlock1())])
]

P = ddsv.Process('P', p_state_trans_list)
Q = ddsv.Process('Q', q_state_trans_list)
lts_tbl = ddsv.concurrent_composition([P, Q], SharedVars(), 'm_mute2')
lts_tbl.save_graph('m_mute2')

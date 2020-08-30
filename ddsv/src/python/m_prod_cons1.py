from abc import ABCMeta
from abc import abstractmethod

import ddsv

class SharedVars(ddsv.SharedVarsInterface):
    _cnt_of_max = 2

    def __init__(self, process_list):
        self.mutex = False
        self.cond = { p:False for p in process_list }
        self.count = 0

    def clone(self):
        p_list = self.cond.keys()
        dst = SharedVars(p_list)
        dst.mutex = self.mutex
        for p in self.cond.keys():
            dst.cond[p] = self.cond[p]
        dst.count = self.count
        return dst

    def equal(self, target):
        return target.mutex == self.mutex and target.cond == self.cond and target.count == self.count

    def to_str(self):
        m = 1 if self.mutex else 0
        cv = sum([ 2 ** i for i, key in enumerate(self.cond.keys()) if self.cond[key] ])
        return 'm={0} cv={1} c={2}'.format(m, cv, self.count)

    def to_graph_str(self):
        return self.to_str()

#----------

class GuardLock(ddsv.Guard):
    def exec(self, process, state):
        return not state.shared_vars.mutex

class ActionLock(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.mutex = True

class ActionUnlock(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.mutex = False

#----------

class GuardNotEmpty(ddsv.Guard):
    def exec(self, process, state):
        return 0 < state.shared_vars.count

class GuardNotFull(ddsv.Guard):
    def exec(self, process, state):
        return state.shared_vars.count < SharedVars._cnt_of_max

class GuardEmpty(ddsv.Guard):
    def exec(self, process, state):
        return state.shared_vars.count == 0

class GuardFull(ddsv.Guard):
    def exec(self, process, state):
        return state.shared_vars.count == SharedVars._cnt_of_max

class GuardReady(ddsv.Guard):
    def exec(self, process, state):
        return not state.shared_vars.cond[process]

class ActionWait(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.mutex = False
        dest.shared_vars.cond[process] = True

class ActionSignal(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.cond[process] = False

class ActionInc(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.count = src.shared_vars.count + 1

class ActionDec(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.count = src.shared_vars.count - 1

#----------

p_state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('lock', '1', GuardLock(), ActionLock())]),
    ddsv.StateTransition('1', [ddsv.Transition('wait', '2', GuardFull(), ActionWait()),
                                ddsv.Transition('produce', '3', GuardNotFull(), ActionInc())]),
    ddsv.StateTransition('2', [ddsv.Transition('wakeup', '0', GuardReady(), ddsv.ActionNop())]),
    ddsv.StateTransition('3', [ddsv.Transition('signal', '4', ddsv.GuardTrue(), ActionSignal())]),
    ddsv.StateTransition('4', [ddsv.Transition('unlock', '0', ddsv.GuardTrue(), ActionUnlock())])
]

q_state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('lock', '1', GuardLock(), ActionLock())]),
    ddsv.StateTransition('1', [ddsv.Transition('wait', '2', GuardEmpty(), ActionWait()),
                                ddsv.Transition('consume', '3', GuardNotEmpty(), ActionDec())]),
    ddsv.StateTransition('2', [ddsv.Transition('wakeup', '0', GuardReady(), ddsv.ActionNop())]),
    ddsv.StateTransition('3', [ddsv.Transition('signal', '4', ddsv.GuardTrue(), ActionSignal())]),
    ddsv.StateTransition('4', [ddsv.Transition('unlock', '0', ddsv.GuardTrue(), ActionUnlock())])
]

P = ddsv.Process('P', p_state_trans_list)
Q = ddsv.Process('Q', q_state_trans_list)

P.save_graph('m_prod_cons1_P')
Q.save_graph('m_prod_cons1_Q')

process_list = [P, Q]
shared_vars = SharedVars(process_list)
lts_tbl = ddsv.concurrent_composition(process_list, shared_vars, 'm_prod_cons1')
lts_tbl.save_graph('m_prod_cons1')

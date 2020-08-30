import sys
import copy
import mcctl

sys.path.append('../../../ddsv/src/python')

import ddsv

class SharedVars(ddsv.SharedVarsInterface):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def clone(self):
        return copy.deepcopy(self)

    def equal(self, target):
        return (self.x == target.x) and (self.y == target.y) and (self.z == target.z)

    def to_str(self):
        return 'x={0} y={1} z={2}'.format(self.x, self.y, self.z)

    def to_graph_str(self):
        return self.to_str()

class ActionX1(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.x = 1

class ActionY0(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.y = 0

class ActionY1(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.y = 1

class ActionZ1(ddsv.Action):
    def exec(self, process, dest, src):
        dest.shared_vars.z = 1

state_trans_list = [
    ddsv.StateTransition('0', [ddsv.Transition('x=1', '1', ddsv.GuardTrue(), ActionX1())]),
    ddsv.StateTransition('1', [ddsv.Transition('y=1', '2', ddsv.GuardTrue(), ActionY1())]),
    ddsv.StateTransition('2', [ddsv.Transition('z=1', '3', ddsv.GuardTrue(), ActionZ1())]),
    ddsv.StateTransition('3', [ddsv.Transition('y=0', '4', ddsv.GuardTrue(), ActionY0())]),
    ddsv.StateTransition('4', [])
]

def func0(shared_vars):
    return shared_vars.x == 1

def func1(shared_vars):
    return shared_vars.y > 0

def func2(shared_vars):
    return shared_vars.z == 0

P = ddsv.Process('P', state_trans_list)
process_list = [P]

lts_tbl = ddsv.concurrent_composition(process_list, SharedVars(), 'm_test1')
lts_tbl.save_graph('m_test1')

f = mcctl.Or(mcctl.And(mcctl.Prop('x=1', func0), mcctl.Prop('y>0', func1)), mcctl.Not(mcctl.Prop('z=0', func2)))

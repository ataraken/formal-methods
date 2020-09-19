import ddmp

class ProcessContext(ddmp.ProcessContextInterface):
    def __init__(self, name, event_list):
        self._loc = 0
        self._event_list = event_list

        self.name = name

    def next_loc(self):
        self._loc += 1
        return self._loc

    def loc(self):
        return '{0}{1}'.format(self.name, self._loc)

    def transition(self, state):
        res = []
        if state.is_initial_state():
            res = [ ddmp.ProcessState.create_next(self.next_loc(), self.loc(), e) for e in self._event_list ]
        return res

file_name = 'composition0'

A = ddmp.Event('a')
B = ddmp.Event('b')
C = ddmp.Event('c')
D = ddmp.Event('d')
E = ddmp.Event('e')

sync = ddmp.SyncEventSet([A, B])

P = ddmp.SingleProcess(ProcessContext('P', [A, B, C, E]))
Q = ddmp.SingleProcess(ProcessContext('Q', [A, C, D]))

lts_p = P.unfold()
lts_q = Q.unfold()

lts_p.save_graph('{0}_P.png'.format(file_name))
lts_q.save_graph('{0}_Q.png'.format(file_name))

cp = ddmp.CompositeProcess(sync, lts_p, lts_q)
lts = cp.concurrent_composition()
lts.save_graph('{0}.png'.format(file_name))

import ddmp

class ProcessContext(ddmp.ProcessContextInterface):
    def __init__(self, name, event, cnt):
        self._loc = 0
        self._event = event
        self._cnt = cnt

        self.name = name

    def next_loc(self):
        self._loc += 1
        return self._loc

    def loc(self):
        return '{0}{1}'.format(self.name, self._loc)

    def transition(self, state):
        res = []
        if state.is_initial_state():
            res = [ ddmp.ProcessState.create_next(self.next_loc(), self.loc(), self._event) for i in range(self._cnt) ]
        return res

file_name = 'composition2'

A = ddmp.Event('a')

sync = ddmp.SyncEventSet([A])

P = ddmp.SingleProcess(ProcessContext('P', A, 2))
Q = ddmp.SingleProcess(ProcessContext('Q', A, 3))

lts_p = P.unfold()
lts_q = Q.unfold()

lts_p.save_graph('{0}_P.png'.format(file_name))
lts_q.save_graph('{0}_Q.png'.format(file_name))

cp = ddmp.CompositeProcess(sync, lts_p, lts_q)
lts = cp.concurrent_composition()
lts.save_graph('{0}.png'.format(file_name))

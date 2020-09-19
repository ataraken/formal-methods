import os
import copy
import pygraphviz as pgv

from abc import ABCMeta
from abc import abstractmethod

class Event:
    def __init__(self, label):
        self._label = label

    def equal(self, target):
        return self._label == target._label

    def to_str(self):
        return self._label

    def print(self):
        print(self.to_str())

class SyncEventSet:
    def __init__(self, event_list):
        self._list = event_list

    def is_included(self, event_list):
        return (set(event_list) <= set(self._list))

class ProcessContextInterface(metaclass=ABCMeta):
    @abstractmethod
    def next_loc(self):
        pass

    @abstractmethod
    def loc(self):
        pass

    @abstractmethod
    def transition(self, state):
        pass

class Process:
    def _bfs(self, s0, trans_func):
        hash_tbl = { s0: [ Path(s0) ] }
        que = [ s0 ]

        while que:
            s = que.pop(0)
            next_state = [ t for t in trans_func(s) ]
            for t in next_state:
                if not t in hash_tbl.keys():
                    que.append(t)
                    hash_tbl[t] = [ Path.create(hash_tbl[s], t) ]
                else:
                    tmp_path = Path.create(hash_tbl[s], t)
                    if len([ p for p in hash_tbl[t] if p.equal(tmp_path) ]) == 0:
                        hash_tbl[t].append(tmp_path)

        return hash_tbl

class SingleProcess(Process):
    def __init__(self, context):
        self._ctx = context

    def to_str(self):
        return self._ctx.to_str()

    def location(self):
        return self._ctx.loc()

    def unfold(self):
        s0 = ProcessState.create_initial(self.location())
        hash_tbl = self._bfs(s0, self._ctx.transition)
        return Lts(hash_tbl)

class CompositeProcess(Process):
    def __init__(self, sync, lts_p, lts_q):
        self._sync = sync
        self._lts_p = lts_p
        self._lts_q = lts_q
        self._location_list  = [0]
        self._location_pair = { 0: (lts_p.initial_state().id(), lts_q.initial_state().id()) }
        self._state_id = 1

    def location(self):
        return self._ctx.loc()

    def concurrent_composition(self):
        s0 = CompositeState.create_initial((self._lts_p.initial_state().id(), self._lts_q.initial_state().id()), self._lts_p.initial_state(), self._lts_q.initial_state())
        trans_func = self.make_transition(s0)
        hash_tbl = self._bfs(s0, trans_func)
        return Lts(hash_tbl)

    def make_transition(self, s0):
        state_id_to_location = { s0.id(): (self._lts_p.initial_state().id(), self._lts_q.initial_state().id(), None) }
        state_id_to_object = { s0.id(): s0 }

        def transition(s):
            src_p = s.p
            src_q = s.q

            sync_ht_p = {}
            sync_ht_q = {}

            next_state = []

            for next_p in self._lts_p.next_states(src_p):
                event = next_p.event()
                if self._sync.is_included([event]):
                    if not event in sync_ht_p.keys():
                        sync_ht_p[event] = []
                    sync_ht_p[event].append(next_p)
                else:
                    location = ( next_p.id(), src_q.id() )
                    id_list = [ id for id in state_id_to_location.keys() if state_id_to_location[id] == location ]
                    if not id_list:
                        next_s = CompositeState.create_next(self._state_id, location, event, next_p, src_q)
                        state_id_to_location[self._state_id] = ( next_p.id(), src_q.id() )
                        state_id_to_object[self._state_id] = next_s
                        self._state_id += 1
                    else:
                        assert len(id_list) == 1
                        next_s = state_id_to_object[id_list[0]]
                    next_state.append(next_s)

            for next_q in self._lts_q.next_states(src_q):
                event = next_q.event()
                if self._sync.is_included([event]):
                    if not event in sync_ht_q.keys():
                        sync_ht_q[event] = []
                    sync_ht_q[event].append(next_q)
                else:
                    location = ( src_p.id(), next_q.id() )
                    id_list = [ id for id in state_id_to_location.keys() if state_id_to_location[id] == location ]
                    if not id_list:
                        next_s = CompositeState.create_next(self._state_id, location, event, src_p, next_q)
                        state_id_to_location[self._state_id] = ( src_p.id(), next_q.id() )
                        state_id_to_object[self._state_id] = next_s
                        self._state_id += 1
                    else:
                        assert len(id_list) == 1
                        next_s = state_id_to_object[id_list[0]]
                    next_state.append(next_s)

            for event_p in sync_ht_p:
                for event_q in sync_ht_q:
                    if event_p.equal(event_q):
                        for next_p in sync_ht_p[event_p]:
                            for next_q in sync_ht_q[event_q]:
                                id_list = [ id for id in state_id_to_location.keys() if ((state_id_to_location[id][0] == next_p.id()) and (state_id_to_location[id][1] == next_q.id())) ]
                                location = ( next_p.id(), next_q.id() )
                                if not id_list:
                                    next_s = CompositeState.create_next(self._state_id, location, event_p, next_p, next_q)
                                    state_id_to_location[self._state_id] = ( next_p.id(), next_q.id() )
                                    state_id_to_object[self._state_id] = next_s
                                    self._state_id += 1
                                else:
                                    assert len(id_list) == 1
                                    next_s = state_id_to_object[id_list[0]]
                                next_state.append(next_s)
            return next_state
        return transition

class Path:
    def create(paths, state):
        assert paths

        base_path = paths[0]
        min_len = paths[0].length()
        for path in paths:
            if path.length() < min_len:
                min_len = path.length()
                base_path = path

        new_path = Path(None, base_path._trans)
        new_path._add(state)
        return new_path

    def __init__(self, s0, trans=None):
        if trans == None:
            self._trans = [ { 's': s0, 'e': None } ]
        else:
            self._trans = [ { 's': tran['s'], 'e': tran['e'] } for tran in trans ]

    def _add(self, s):
        self._trans.append({ 's': s, 'e': None })

    def length(self):
        return len(self._trans)

    def equal(self, target):
        res = False
        if target.length() == self.length():
            res = len([ True for t0, t1 in zip(self._trans, target._trans) if not (t0['s'].equal2(t1['s'])) ]) == 0
        return res

    def states(self):
        return [ tran['s'] for tran in self._trans ]

    def search_tran(self, s):
        is_target_found = False
        for tran in self._trans:
            if is_target_found:
                return tran['s']
            if (tran['s']).equal(s):
                is_target_found = True
        return None

    def last_tran(self):
        if len(self._trans) == 1:
            return (None, self._trans[0]['s'])
        else:
            return (self._trans[-2]['s'], self._trans[-1]['s'])

    def to_str(self):
        return 'path'

    def print(self):
        print('--------------------')
        for idx, i in enumerate(self._trans):
            print('[{0}] {1}'.format(idx, i['s'].to_str()))

# Labelled Transition System
class Lts:
    _dir_name = 'img'

    def __init__(self, hash_tbl):
        self._paths = hash_tbl

    def initial_state(self):
        return (self.all_states())[0]

    def all_states(self):
        return list(self._paths.keys())

    def path(self, s):
        return self._paths[s]

    def next_states(self, target):
        res = []
        for s in self._paths:
            for path in self._paths[s]:
                tran = path.search_tran(target)
                if tran != None:
                    res.append(tran)
        return res

    def save_graph(self, name):
        G = pgv.AGraph(directed=True, strict=False)

        for i, s in enumerate(self._paths):
            if i == 0:
                G.add_node(s.id(), label=s.to_str(), style='filled', fillcolor='cyan')
            else:
                G.add_node(s.id(), label=s.to_str())

        for s in self._paths:
            print('state s {0} {1}'.format(s.id(), len(self._paths[s])))
            for path in self._paths[s]:
                tran = path.last_tran()
                if tran[0] != None:
                    assert s.id() == tran[1].id(), '{0} {1}'.format(s.id(), tran[1].id())
                    print('{0} -> {1}'.format(tran[0].id(), s.id()))
                    G.add_edge(tran[0].id(), s.id(), label=s.event().to_str())

        sorted(G.edges(keys=True))

        if not os.path.isdir(self._dir_name):
            os.mkdir(self._dir_name)

        G.layout(prog='dot')
        G.draw(os.path.join(self._dir_name, '{0}.png'.format(name)))

class StateInterface(metaclass=ABCMeta):
    @abstractmethod
    def id(self):
        pass

    @abstractmethod
    def event(self):
        pass

    @abstractmethod
    def is_initial_state(self):
        pass

    @abstractmethod
    def equal(self, target):
        pass

    @abstractmethod
    def label(self):
        pass

    @abstractmethod
    def to_str(self):
        pass

class AbstractState(StateInterface):
    _initial_id = 0

    def __init__(self, id, event):
        self._id = id
        self._event = event

    def id(self):
        return self._id

    def event(self):
        return self._event

    def is_initial_state(self):
        return ProcessState._initial_id == self._id

    def equal(self, target):
        return self._id == target._id

class ProcessState(AbstractState):
    def create_initial(location):
        return ProcessState(ProcessState._initial_id, location, None)

    def create_next(id, location, event):
        return ProcessState(id, location, event)

    def __init__(self, id, location, event):
        super(ProcessState, self).__init__(id, event)
        self._loc = location

    def label(self):
        return self._loc

    def to_str(self):
        return '{0}\n{1}'.format(self._id, self.label())

class CompositeState(AbstractState):
    def create_initial(location, p, q):
        return CompositeState(CompositeState._initial_id, location, None, p, q)

    def create_next(id, location, event, p, q):
        return CompositeState(id, location, event, p, q)

    def __init__(self, id, location, event, p, q):
        super(CompositeState, self).__init__(id, event)
        self._loc = location
        self.p = p
        self.q = q

    def equal(self, p, q):
        return (self.p.id() == p.id()) and (self.q.id() == q.id())

    def equal2(self, target):
        return target.equal(self.p, self.q)

    def label(self):
        print('---', self.p.label(), self.q.label())
        return '{0}\n{1}'.format(self.p.label(), self.q.label())

    def to_str(self):
        return '{0}\n{1}'.format(self._id, self.label())

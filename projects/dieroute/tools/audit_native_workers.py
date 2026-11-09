"""Verify worker ownership, boundary observations and per-attempt work sums.
The verifier replays authority, not search. It cannot independently reconstruct
all queue operations from aggregate counters; differential C++ tests cover that.
"""
import csv
from collections import defaultdict
from audit_native_label_transport import LabelTransportAudit

class WorkerAudit:
    def __init__(self,route,command):
        self.enabled=int(command[20]) if len(command)>=21 else 0
        assert self.enabled in (0,1)
        if self.enabled:assert int(command[19])==int(command[17])==1 and int(command[12])==0
        def grouped(name,fields):
            path=route/name
            if not path.exists():assert not self.enabled;return {}
            with path.open() as f:rows=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(f)]
            assert self.enabled or not rows
            for rep in range(1,int(command[11])):
                assert [{k:v for k,v in r.items() if k!='repeat'} for r in rows if r['repeat']==rep]==[{k:v for k,v in r.items() if k!='repeat'} for r in rows if r['repeat']==0]
            result=defaultdict(list)
            for row in rows:
                assert all(v>=0 for v in row.values());result[tuple(row[k] for k in fields)].append(row)
            return dict(result)
        self.queues=grouped('worker_queues.csv',('repeat','search','replay','attempt'))
        self.reads=grouped('worker_reads.csv',('repeat','search','replay'))
        self.access=grouped('worker_access.csv',('repeat','search','replay'))
        self.total=defaultdict(int);self.observed={};self.per_die=defaultdict(lambda:defaultdict(int))
        self.limit=int(command[8])
        self.transport=LabelTransportAudit(route,command,self.enabled)
    def call(self,key,call,dies,member,now,tree,allowed):
        self.observed={}
        if not self.enabled:return
        reads=self.reads.pop(key,[]);access=self.access.pop(key)
        assert [r['worker'] for r in access]==list(range(dies))
        assert [(r['worker'],r['node']) for r in reads]==sorted(set((r['worker'],r['node']) for r in reads))
        count=defaultdict(int)
        for r in reads:
            d,n,o=r['worker'],r['node'],r['owner'];mask=member(n)
            assert d<dies and 0<mask<1<<dies and mask&(1<<d) and o==(mask&-mask).bit_length()-1 and o!=d
            assert allowed(n) and n not in tree
            assert (r['occupancy'],r['history'],r['version'])==now(n),'boundary observation differs from authority at request'
            self.observed[d,n]=r;count[d]+=1
        for r in access:
            d=r['worker'];assert r['requests']==r['validations']==count[d] and r['valid']==1
            assert r['cache_hits']==0 or r['requests']>0
            for field in ('owned_reads','requests','cache_hits','validations'):
                self.total[field]+=r[field];self.per_die[d][field]+=r[field]
        assert sum(r['owned_reads']+r['requests']+r['cache_hits'] for r in access)<=call['joint_edge_visits']
        self.total['calls']+=1
    def edge(self,die,node,member):
        if self.enabled:
            mask=member(node);owner=(mask&-mask).bit_length()-1
            if die!=owner:assert (die,node) in self.observed,'selected/candidate boundary read missing from worker journal'
    def plan(self,key,first,plan,dies,path,member,tree,sink,arc_ok,allowed,step_cost):
        if not self.enabled:return
        queues=self.queues.pop(key);assert [r['die'] for r in queues]==list(range(dies))
        assert sum(r['expanded'] for r in queues)==first['expanded']
        assert sum(r['edge_visits'] for r in queues)==first['edge_visits']
        assert sum(r['labels'] for r in queues)<=self.limit
        active={p['die'] for p in plan}
        for r in queues:
            assert r['expanded']<=r['labels']<=r['pushes'] and r['transfers']<=r['pushes']
            if r['die'] not in active:assert all(r[k]==0 for k in ('expanded','edge_visits','pushes','transfers','labels'))
            for field in ('expanded','edge_visits','pushes','transfers','labels'):
                self.total[field]+=r[field];self.per_die[r['die']][field]+=r[field]
        self.total['attempts']+=1
        self.transport.plan(key,first,plan,dies,queues,path,member,tree,sink,arc_ok,allowed,step_cost)
    def finish(self):
        assert not self.queues and not self.reads and not self.access
        return dict(label_transport=self.transport.finish(),enabled=bool(self.enabled),recorded_protocol_verified=bool(self.enabled),totals=dict(self.total),per_die={str(d):dict(v) for d,v in sorted(self.per_die.items())},
                    logical_boundary_messages=2*(self.total['requests']+self.total['validations']),
                    limits='Fresh demand summaries within serial search/validate/commit phases. Counter consistency and recorded read values checked; not a second search execution, concurrent protocol, wire-format traffic or HBM measurement.')

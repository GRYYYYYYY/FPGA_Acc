"""Full archived SHA1 candidate replay and adversarial native-state checks.
No new searches, budgets, model decisions, or speedup claims.
"""
import ctypes as C,hashlib,json,subprocess,time,xml.etree.ElementTree as ET
from array import array
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'experiments/native_net_union_ledger_replay_v1_2026-10-17'
D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,d):
 with (D/name).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
source=R/'tools/soft_demand_cpp/net_union_ledger_v1_2026_10_17.cpp'
base=R/'experiments/sha_resident_work_profile_seed_complete_workflow_v1_2026-10-10'
m=base/'seed/model/sha1';ep=base/'seed/demand/sha1/endpoints.json'
inputs=[source,Path(__file__).resolve(),m/'initial.json',m/'receipt.json',m/'round0.json',m/'round1.json',ep,base/'verification.json']
bindings={str(p):sha(p) for p in inputs}
proof=json.loads((base/'verification.json').read_text());assert proof['all_cases_both_complete_arms_authenticated']
for k,h in proof['bindings'].items():assert sha(k)==h
receipt=json.loads((m/'receipt.json').read_text())
for k,h in receipt['files'].items():assert sha(k)==h
endpoint=json.loads(ep.read_text());graph=Path(endpoint['inputs']['graph']['path'])
assert sha(graph)==endpoint['inputs']['graph']['sha256'];bindings[str(graph)]=sha(graph)
command=['g++','-std=c++17','-O2','-fPIC','-shared','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',str(source),'-o',str(D/'ledger.so')]
write('protocol.json',dict(bindings=bindings,command=command,scope='All archived two-round SHA1 candidate unions, independent full ledger/epoch checks at round boundaries. Search/budget/path validation and fallback remain external. No measured acceleration or full native-state ownership.'))
with (D/'compile.log').open('x') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
lib=C.CDLL(str(D/'ledger.so'));U=C.c_uint64;P=C.POINTER(U)
lib.rc_ledger_create.argtypes=[P,U];lib.rc_ledger_create.restype=C.c_void_p
lib.rc_ledger_free.argtypes=[C.c_void_p]
lib.rc_ledger_add.argtypes=[C.c_void_p,U,U,P,U]
lib.rc_ledger_replace.argtypes=[C.c_void_p,U,U,P,U,C.POINTER(C.c_int64)]
lib.rc_ledger_export.argtypes=[C.c_void_p,P,U]
lib.rc_ledger_epoch.argtypes=[C.c_void_p,U];lib.rc_ledger_epoch.restype=U
def arr(xs):return (U*len(xs))(*xs)
class Ledger:
 def __init__(self,cap):
  self.n=len(cap);self.p=lib.rc_ledger_create(arr(cap),self.n);assert self.p
 def close(self):lib.rc_ledger_free(self.p);self.p=None
 def add(self,net,epoch,nodes):return lib.rc_ledger_add(self.p,net,epoch,arr(nodes),len(nodes))
 def replace(self,net,epoch,nodes):
  delta=C.c_int64(-987654321);status=lib.rc_ledger_replace(self.p,net,epoch,arr(nodes),len(nodes),C.byref(delta));return status,delta.value
 def export(self):
  a=(U*self.n)();assert lib.rc_ledger_export(self.p,a,self.n)==0
  return {i:v for i,v in enumerate(a) if v}
 def epoch(self,net):return lib.rc_ledger_epoch(self.p,net)
# Independent tiny state: shared resource counted once per NET, not per branch.
l=Ledger([1,1,1,0]);assert l.add(10,1,[0,1])==0;assert l.add(11,1,[1,2])==0
before=l.export();assert before=={0:1,1:2,2:1}
neg=[]
for name,net,epoch,nodes,expected in [('stale',10,2,[0],2),('unknown',99,1,[0],2),('duplicates',10,1,[0,0],1),('unsorted',10,1,[1,0],1),('out_of_range',10,1,[4],1),('empty',10,1,[],1),('overflow',10,1,[0,1,3],3)]:
 status,delta=l.replace(net,epoch,nodes);assert status==expected and l.export()==before and l.epoch(10)==1
 if status in (1,2):assert delta==-987654321
 neg.append(name)
assert l.add(10,1,[0])==1 and l.export()==before
assert l.replace(10,1,[0])==(0,-1) and l.epoch(10)==2
assert l.replace(10,1,[0])[0]==2
l.close()
l=Ledger([1]);assert l.add(1,2**64-1,[0])==0;assert l.replace(1,2**64-1,[0])[0]==1 and l.export()=={0:1};l.close();neg+=['duplicate_initial_net','epoch_exhaustion','postcommit_stale']
# Streaming independent XML topology. IDs are original rr_edges enumeration.
cap=array('Q');src=array('Q');dst=array('Q');parents=[]
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':parents.append(e.tag);continue
 if e.tag=='node' and len(parents)>1 and parents[-2]=='rr_nodes':
  assert int(e.get('id'))==len(cap);cap.append(int(e.get('capacity')));e.clear()
 elif e.tag=='edge' and len(parents)>1 and parents[-2]=='rr_edges':
  src.append(int(e.get('src_node')));dst.append(int(e.get('sink_node')));e.clear()
 parents.pop()
assert cap and src
queries={q['connection_id']:q for q in endpoint['connections']}
def union(records):
 own=set()
 for r in records:
  q=queries[r['connection_id']];assert all(r[k]==q[k] for k in ['net_id','source','sink'])
  u=r['source'];seen={u};own.add(u)
  for edge in r['answer']['physical_edge_ids']:
   assert src[edge]==u;u=dst[edge];assert u not in seen;seen.add(u);own.add(u)
  assert u==r['sink']
 return sorted(own)
initial=json.loads((m/'initial.json').read_text());groups=defaultdict(list)
for r in initial['records']:groups[r['net_id']].append(r)
assert len(initial['records'])==len(queries)==6273
l=Ledger(cap);owned={};epochs={}
for net,recs in groups.items():
 owned[net]=union(recs);epochs[net]=1;assert l.add(net,1,owned[net])==0
expected=Counter(n for nodes in owned.values() for n in nodes)
assert l.export()==dict(expected)=={int(k):v for k,v in initial['ledger'].items()}
counts=Counter();rounds=[];start=time.perf_counter()
for rd in receipt['rounds']:
 assert [e['net_id'] for e in rd['events']]==rd['affected_nets']
 for e in rd['events']:
  net=e['net_id'];assert epochs[net]==e['old_epoch']==l.epoch(net)
  assert e['status'] in ['COMMITTED','RETAIN_OVERFLOW_INCREASE']
  recs=e['records'] if e['status']=='COMMITTED' else e['rejected_records']
  assert sorted(r['connection_id'] for r in recs)==sorted(r['connection_id'] for r in groups[net])
  candidate=union(recs);old=set(owned[net]);new=set(candidate)
  delta=sum(max(0,expected[n]+1-cap[n])-max(0,expected[n]-cap[n]) for n in new-old)
  delta+=sum(max(0,expected[n]-1-cap[n])-max(0,expected[n]-cap[n]) for n in old-new)
  assert delta==e['prospective_overflow_delta']
  status,actual=l.replace(net,epochs[net],candidate)
  assert actual==delta and status==(0 if delta<=0 else 3)
  assert (status==0)==(e['status']=='COMMITTED')
  if status==0:
   expected.subtract(old-new);expected.update(new-old);expected=+expected
   owned[net]=candidate;epochs[net]+=1
  assert epochs[net]==e['new_epoch']==l.epoch(net);counts[e['status']]+=1
 state=json.loads((m/f"round{rd['round_index']}.json").read_text())
 actual=l.export();assert actual==dict(expected)=={int(k):v for k,v in state['ledger'].items()}
 assert epochs=={int(k):v for k,v in state['epochs'].items()}
 overflow=sum(max(0,v-cap[k]) for k,v in actual.items());assert overflow==rd['overflow_after']
 rounds.append(dict(round_index=rd['round_index'],events=len(rd['events']),overflow=overflow,full_ledger_and_all_epochs_equal=True))
l.close()
assert all(sha(k)==h for k,h in bindings.items())
write('verification.json',dict(bindings=bindings,library_sha256=sha(D/'ledger.so'),all4498_candidates_native_decisions_deltas_and_epochs_equal=sum(counts.values())==4498,statuses=dict(counts),negative_cases=neg,rounds=rounds,replay_seconds=time.perf_counter()-start,scope='Complete archived candidate-union replay only. Native owns union occupancy and per-NET epoch; Python reconstructs and validates candidates and reference state. Not fresh full model, budget/fallback migration, original independent audits, end-to-end gain, heldout or hardware proof.'))
print(json.dumps(dict(statuses=dict(counts),negative_cases=len(neg),rounds=rounds),indent=2),flush=True)

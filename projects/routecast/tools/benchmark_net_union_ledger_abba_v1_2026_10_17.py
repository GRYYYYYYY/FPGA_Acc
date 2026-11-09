"""Fresh-state ABBA component comparison; all ctypes crossings included.
Archived candidate unions, no fresh search or end-to-end speed claim.
"""
import ctypes as C,hashlib,json,time,xml.etree.ElementTree as ET
from array import array
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/net_union_ledger_abba_v1_2026-10-17'
D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
B=R/'experiments/native_net_union_ledger_replay_v1_2026-10-17';Q=R/'experiments/native_net_union_ledger_random_v1_2026-10-17/verification.json'
proof=json.loads((B/'verification.json').read_text());random=json.loads(Q.read_text())
assert proof['all4498_candidates_native_decisions_deltas_and_epochs_equal'] and random['all_operations_full_occupancy_and_all_epochs_equal']
for k,h in proof['bindings'].items():assert sha(k)==h
assert sha(B/'ledger.so')==proof['library_sha256']
bindings={str(p):sha(p) for p in [Path(__file__).resolve(),B/'verification.json',Q,B/'ledger.so']}
base=R/'experiments/sha_resident_work_profile_seed_complete_workflow_v1_2026-10-10/seed';m=base/'model/sha1'
for n in ['initial.json','receipt.json','round0.json','round1.json']:bindings[str(m/n)]=sha(m/n)
write('protocol.json',dict(bindings=bindings,order=['python','native','native','python'],policy='Fresh states per arm; complete4498 archived candidates. Component clock includes initial state, per-candidate conversion, decision/delta/epoch assertions, all three full-state exports/validations, destruction. Common graph parsing/path union materialization and provenance hashing separately accounted; excluded identically from both arms. ctypes shared object resident across native arms. No profiler, no warmup, no process isolation, n=2 per mode; no OS-cache or host-load control.',gate='Both adjacent order-reversed native arms must be faster before any integration proposal. Gate only local component; no end-to-end promotion.'))
prep=time.perf_counter();ep=json.loads((base/'demand/sha1/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['inputs']['graph']['sha256']
cap=array('Q');src=array('Q');dst=array('Q');parents=[]
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':parents.append(e.tag);continue
 if e.tag=='node' and len(parents)>1 and parents[-2]=='rr_nodes':
  assert int(e.get('id'))==len(cap);cap.append(int(e.get('capacity')));e.clear()
 elif e.tag=='edge' and len(parents)>1 and parents[-2]=='rr_edges':
  src.append(int(e.get('src_node')));dst.append(int(e.get('sink_node')));e.clear()
 parents.pop()
def union(records):
 nodes=set()
 for r in records:
  u=r['source'];nodes.add(u);seen={u}
  for edge in r['answer']['physical_edge_ids']:
   assert src[edge]==u;u=dst[edge];assert u not in seen;seen.add(u);nodes.add(u)
  assert u==r['sink']
 return tuple(sorted(nodes))
initial=json.loads((m/'initial.json').read_text());groups=defaultdict(list)
for r in initial['records']:groups[r['net_id']].append(r)
initial_unions={n:union(rs) for n,rs in groups.items()};initial_ledger={int(k):v for k,v in initial['ledger'].items()}
receipt=json.loads((m/'receipt.json').read_text());rounds=[]
for rd in receipt['rounds']:
 events=[]
 for e in rd['events']:
  assert e['status'] in ['COMMITTED','RETAIN_OVERFLOW_INCREASE']
  rs=e['records'] if e['status']=='COMMITTED' else e['rejected_records']
  events.append((e['net_id'],e['old_epoch'],e['new_epoch'],union(rs),e['prospective_overflow_delta'],0 if e['status']=='COMMITTED' else 3))
 state=json.loads((m/f"round{rd['round_index']}.json").read_text());rounds.append((events,{int(k):v for k,v in state['ledger'].items()},{int(k):v for k,v in state['epochs'].items()}))
assert sum(len(x[0]) for x in rounds)==4498
prep_seconds=time.perf_counter()-prep
lib=C.CDLL(str(B/'ledger.so'));U=C.c_uint64;P=C.POINTER(U)
lib.rc_ledger_create.argtypes=[P,U];lib.rc_ledger_create.restype=C.c_void_p
lib.rc_ledger_add.argtypes=[C.c_void_p,U,U,P,U]
lib.rc_ledger_replace.argtypes=[C.c_void_p,U,U,P,U,C.POINTER(C.c_int64)]
lib.rc_ledger_export.argtypes=[C.c_void_p,P,U]
lib.rc_ledger_epoch.argtypes=[C.c_void_p,U];lib.rc_ledger_epoch.restype=U
lib.rc_ledger_free.argtypes=[C.c_void_p];lib.rc_ledger_free.restype=None
def arr(xs):return (U*len(xs))(*xs)
def run(mode):
 begin=time.perf_counter();p=None
 if mode=='python':
  owned={k:set(v) for k,v in initial_unions.items()};epochs={k:1 for k in owned};ledger=Counter(n for ns in owned.values() for n in ns)
  def export():return dict(ledger)
  def getepoch(n):return epochs[n]
 else:
  p=lib.rc_ledger_create(arr(cap),len(cap));assert p
  for net,nodes in initial_unions.items():assert lib.rc_ledger_add(p,net,1,arr(nodes),len(nodes))==0
  def export():
   out=(U*len(cap))();assert lib.rc_ledger_export(p,out,len(cap))==0
   return {i:v for i,v in enumerate(out) if v}
  def getepoch(n):return lib.rc_ledger_epoch(p,n)
 assert export()==initial_ledger and all(getepoch(n)==1 for n in initial_unions)
 initialized=time.perf_counter();event_total=0;exports=0
 for events,expected_ledger,expected_epochs in rounds:
  for net,old_epoch,new_epoch,nodes,expected_delta,expected_status in events:
   assert getepoch(net)==old_epoch
   if mode=='python':
    new=set(nodes);removed=owned[net]-new;added=new-owned[net]
    updates={n:ledger[n]-1 for n in removed};updates.update({n:ledger[n]+1 for n in added})
    assert all(v>=0 for v in updates.values())
    delta=sum(max(0,v-cap[n])-max(0,ledger[n]-cap[n]) for n,v in updates.items());status=3 if delta>0 else 0
    if status==0:
     for n,v in updates.items():
      if v:ledger[n]=v
      else:del ledger[n]
     owned[net]=new;epochs[net]+=1
   else:
    result=C.c_int64();status=lib.rc_ledger_replace(p,net,old_epoch,arr(nodes),len(nodes),C.byref(result));delta=result.value
   assert delta==expected_delta and status==expected_status and getepoch(net)==new_epoch;event_total+=1
  tick=time.perf_counter();assert export()==expected_ledger and all(getepoch(n)==ep for n,ep in expected_epochs.items());exports+=time.perf_counter()-tick
 if p:lib.rc_ledger_free(p)
 elapsed=time.perf_counter()-begin
 return dict(mode=mode,component_seconds=elapsed,initialization_and_initial_full_validation_seconds=initialized-begin,round_export_validation_seconds=exports,events=event_total,all_decisions_deltas_target_epochs_and_three_full_states_equal=True)
rows=[]
for i,mode in enumerate(['python','native','native','python']):
 row=run(mode);row['index']=i;rows.append(row);print(json.dumps(row),flush=True)
write('rows.json',rows)
pairs=[]
for a,b in [(0,1),(3,2)]:
 py=rows[a]['component_seconds'];native=rows[b]['component_seconds'];pairs.append(dict(python_index=a,native_index=b,python_seconds=py,native_seconds=native,saved_seconds=py-native,relative_saving=(py-native)/py))
assert all(sha(k)==h for k,h in bindings.items())
write('verification.json',dict(bindings=bindings,rows_sha256=sha(D/'rows.json'),common_graph_and_union_preparation_seconds=prep_seconds,complete_candidates=4498,pairs=pairs,both_orders_native_faster=all(p['saved_seconds']>0 for p in pairs),all_four_fresh_states_complete_and_equal=True,scope='Archived component ABBA n2/mode, resident shared library, same-process/no host cache control. Full crossings/conversions and full export validation included. Graph/union preparation common and reported separately. No native search or full model timing; cannot subtract these clocks from older workflow as a measured gain.'))
print(json.dumps(dict(pairs=pairs,common_preparation_seconds=prep_seconds)),flush=True)

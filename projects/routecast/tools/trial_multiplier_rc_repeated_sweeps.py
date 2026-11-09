"""Real initial-to-swapped placement RC NET admission and wholemove rollback."""
import json,sys,hashlib,shutil
from pathlib import Path
from collections import Counter,defaultdict
from prepared_csr import read,U64,TYPES
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from native_integer_rc_sink_bound import NativeIntegerRCSinkBound
from csr_integer_sink_bound_search import query
from rc_feasible_cost_region import RCFeasibleCostRegion
from verify_rc_remaining_certificate import verify as certificate
from local_other_demand import LocalOtherDemand
from immutable_xml_prediction_audit import ImmutableXMLAudit
from net_occupancy_delta import replace_net
from incremental_channel_pressure import ChannelPressure
from move_prediction_transaction import MoveState,MovePredictionTransaction
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';name=sys.argv[1];assert name in [f'mult_{w}x{w}' for w in range(4,10)]
out=base/'multiplier_rc_repeated_sweeps_2026-10-06'/name;out.mkdir(parents=True);shutil.copyfile(Path(__file__),out/'source.py');bindings={}
def readjson(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
budgetroot=base/'multiplier_moved_rc_budgets_2026-10-06';br=readjson(budgetroot/'receipt.json');proof=readjson(base/'multiplier_moved_rc_budget_xml_audit_2026-10-06/verification.json');assert proof['inputs_sha256'][str(budgetroot/'receipt.json')]==sha(budgetroot/'receipt.json');assert all(sha(p)==h for p,h in proof['inputs_sha256'].items())
oldroot=base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset';swap=base/'multiplier_placement_swap_2026-10-06'/name
refs=[readjson(oldroot/'prediction.json'),readjson(base/'multiplier_moved_incremental_search_2026-10-06'/name/'prediction.json')];eps=[readjson(base/'multiplier_family_endpoints_2026-10-06'/name/'endpoints.json'),readjson(swap/'endpoints.json')];protocol=readjson(oldroot/'protocol.json');graph=protocol['inputs']['graph'];assert sha(graph['path'])==graph['sha256'];bindings[graph['path']]=graph['sha256']
context=base/'multiplier_cw300_exact_buffered_rc_classes_2026-10-06'/name;csr=base/'multiplier_family_length_switch_csr_2026-10-06'/name/'csr'
for folder in (context,csr):
 for p in folder.rglob('*'):
  if p.is_file():bindings[str(p)]=sha(p)
m,f=read(csr,graph['sha256']);rc=IntegerRC(ExactBufferedRC(f,*load(context,graph['sha256'])));native=NativeIntegerRCSinkBound(rc);xml=ImmutableXMLAudit(graph['path'],graph['sha256']);slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};region=RCFeasibleCostRegion(m['nodes'],[(u,f['dest_ranks'][i],rc.increments[i],f['costs'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0]);certs={}
for p in (root/'build/rc_budget_native_sink_bound_2026-10-06/search.so',):bindings[str(p)]=sha(p)
(out/'sources').mkdir()
for n in ('local_other_demand.py','native_integer_rc_sink_bound.py','native_integer_rc_delta_search.py','native_integer_rc_search.py','rc_feasible_cost_region.py','csr_integer_sink_bound_search.py','verify_rc_remaining_certificate.py','move_prediction_transaction.py','immutable_xml_prediction_audit.py','net_occupancy_delta.py','integer_rc_context.py','csr_exact_buffered_rc.py','buffered_rc_context.py','prepared_csr.py','incremental_channel_pressure.py'):
 shutil.copyfile(root/'tools'/n,out/'sources'/n);bindings[str(root/'tools'/n)]=sha(root/'tools'/n)
def union(rows):
 s=set()
 for r in rows:
  s.add(r['source'])
  for e in r['physical_edge_ids']:s.update(slots[e])
 return s
def state(pred):
 groups=defaultdict(list)
 for r in pred['connections']:groups[r['net_id']].append(r)
 unions={n:union(rows) for n,rows in groups.items()};return unions,Counter(n for s in unions.values() for n in s)
overflow=lambda occ:sum(max(0,v-f['capacities'][n]) for n,v in occ.items())
def pressure(occ):
 p=ChannelPressure(f['types'],f['capacities']);p.refresh(occ,range(m['nodes']));return p.payload(graph['sha256']).encode()
places=[Path(protocol['inputs']['place']['path']) if 'place' in protocol['inputs'] else root/'work/multiplier_family_native_capture_2026-10-06'/name/'design.place',swap/'swapped.place']
for p in places:bindings[str(p)]=sha(p)
encode=lambda x:(json.dumps(x)+'\n').encode()
_,occ=state(refs[0]);ctx=hashlib.sha256(encode(bindings)).hexdigest();old=MoveState(0,ctx,places[0].read_bytes(),encode(eps[0]),encode(refs[0]),(budgetroot/name/'step_0_budgets.json').read_bytes(),pressure(occ));tx=MovePredictionTransaction(old)
def stage(old,step,fault=None):
 budgetpath=budgetroot/name/f'step_{step}_budgets.json';bs=readjson(budgetpath);expected=next(x for x in br['steps'] if x['design']==name and x['step']==step);assert sha(budgetpath)==expected['budget_sha256'];budgets={r['connection_id']:r['scaled_integer_budget'] for r in bs};active={r['connection_id']:r for r in json.loads(old.prediction)['connections']};reference={r['connection_id']:r for r in refs[step]['connections']};groups=defaultdict(list)
 for r in eps[step]['connections']:groups[r['net_id']].append(r)
 restored=[]
 for net,rows in sorted(groups.items()):
  if any(any(active[r['connection_id']][k]!=r[k] for k in ('net_id','source','sink')) or rc.path(r['source'],r['sink'],active[r['connection_id']]['physical_edge_ids'])>budgets[r['connection_id']] for r in rows):
   restored.append(net)
   for r in rows:active[r['connection_id']]=reference[r['connection_id']]
 if fault=='after_repairs':raise RuntimeError(fault)
 unions,occ=state({'connections':list(active.values())});current=overflow(occ);start=current;local=LocalOtherDemand(native);dirty=set();journal=[];count=0
 for net,rows in sorted(groups.items()):
  local.transition(occ,unions[net],dirty);dirty=set();other=occ.copy();other.subtract(unions[net]);assert local.values==dict(+other);assert all(int(native.other[n])==other[n] for n in range(m['nodes']));candidate=[];results=[]
  for r in rows:
   sink=r['sink'];remaining=region.distance(sink,True)
   if sink not in certs:certs[sink]=certificate(f,rc.increments,sink,[remaining.get(n,U64) for n in range(m['nodes'])])
   found=native.query_bound(r['source'],sink,budgets[r['connection_id']],remaining,10000);oracle=query(rc,r['source'],sink,budgets[r['connection_id']],lambda u,i:f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0,lambda u,i:int(f['costs'][i])*(1+other[f['dest_ranks'][i]]),remaining,10000);assert found==oracle;results.append(found);count+=1
   if fault=='during_search' and count==20:raise RuntimeError(fault)
   if found['status']=='FOUND':candidate.append({**r,'physical_edge_ids':found['physical_edge_ids'],'method':'online_dynamic_net'})
  accepted=False;tree_ok=False;before=current
  if len(candidate)==len(rows):
   newunion=union(candidate);incoming=Counter();outgoing=defaultdict(list)
   for eid in {e for r in candidate for e in r['physical_edge_ids']}:
    u,v=slots[eid];incoming[v]+=1;outgoing[u].append(v)
   source=rows[0]['source'];tree_ok=not incoming[source] and all(v<=1 or f['types'][n]==TYPES['SINK'] for n,v in incoming.items());degree={n:incoming[n] for n in newunion};queue=[n for n in newunion if degree[n]==0];visited=0
   while queue:
    n=queue.pop();visited+=1
    for v in outgoing[n]:
     degree[v]-=1
     if degree[v]==0:queue.append(v)
   tree_ok=tree_ok and visited==len(newunion);staged,total,_=replace_net(occ,unions[net],newunion,f['capacities'],current)
   if tree_ok and total<=current:
    dirty=unions[net]^newunion;unions[net]=newunion;occ=staged;current=total;accepted=True
    for r in candidate:active[r['connection_id']]=r
  journal.append({'net_id':net,'accepted':accepted,'tree_ok':tree_ok,'before_overflow':before,'after_overflow':current,'results':results})
 if fault=='after_search':raise RuntimeError(fault)
 pred={'physical_graph_sha256':graph['sha256'],'connections':[active[c] for c in sorted(active)],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(active),'completed':len(active),'methods':dict(Counter(r['method'] for r in active.values()))}
 for r in pred['connections']:assert rc.path(r['source'],r['sink'],r['physical_edge_ids'])<=budgets[r['connection_id']]
 rebuilt_u,rebuilt_o=state(pred);assert rebuilt_u==unions and +occ==rebuilt_o
 audit=xml.verify(eps[step],pred,topology=True);assert audit['all_physical_and_union_checks_passed']
 if fault=='after_audit':raise RuntimeError(fault)
 payload=pressure(occ)
 if fault=='after_pressure':raise RuntimeError(fault)
 result=MoveState(old.epoch+1,old.context,places[step].read_bytes(),encode(eps[step]),encode(pred),budgetpath.read_bytes(),payload,b'[]')
 return result,{'step':step,'restored_nets':restored,'queries':count,'initial_overflow':start,'final_overflow':current,'journal':journal,'physical':audit}
def validate(s):
 pred=json.loads(s.prediction);_,occ=state(pred);assert s.pressure==pressure(occ);return True
reports=[]
for iteration,step in enumerate((0,1,1,1,1)):
 old=tx.snapshot();failures=[]
 if iteration==1:
  for fault in ('after_repairs','during_search','after_search','after_audit','after_pressure'):
   assert tx.commit(old.epoch,lambda s:stage(s,step,fault)[0],validate)=='FAILED';assert tx.snapshot() is old;failures.append(fault)
 metadata={}
 def build(s):
  try: candidate,report=stage(s,step)
  except Exception:
   import traceback;traceback.print_exc();raise
  metadata.update(report);return candidate
 assert tx.commit(old.epoch,build,validate)=='COMMITTED';published=tx.snapshot()
 for kind in ('prediction','endpoints','budgets','pressure'):(out/f'iteration_{iteration}_{kind}.json').write_bytes(getattr(published,kind))
 (out/f'iteration_{iteration}_journal.json').write_bytes(encode(metadata.pop('journal')));(out/f'iteration_{iteration}_physical.json').write_bytes(encode(metadata.pop('physical')))
 reports.append(metadata|{'iteration':iteration,'published_epoch':published.epoch,'failures_preserved_snapshot':failures});print(reports[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'steps':reports,'certified_sinks':len(certs),'outputs_sha256':{p.name:sha(p) for p in out.glob('iteration_*')},'scope':'One initial stage, one real swap, three repeated same-placement sweeps; full Python pruned oracles/full-buffer comparisons included. In-memory snapshot rollback, not filesystem atomicity/native STA/native routing performance. No dependency cache.'},indent=2)+'\n')

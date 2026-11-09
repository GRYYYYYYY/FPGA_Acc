"""Postroute reference-budget switch and live coordinated private NET repair."""
import json,shutil,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from prepared_csr import read,U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from csr_integer_sink_bound_search import query
from rc_feasible_cost_region import RCFeasibleCostRegion
from immutable_xml_prediction_audit import ImmutableXMLAudit
from incremental_channel_pressure import ChannelPressure
from move_prediction_transaction import MoveState,MovePredictionTransaction
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'multiplier_live_native_budget_pair_transaction_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');bindings={}
def readjson(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
name='mult_6x6';parent=base/'multiplier_rc_repeated_sweeps_2026-10-06'/name;prior=readjson(parent/'receipt.json');assert all(sha(parent/n)==h for n,h in prior['outputs_sha256'].items());oldpred=readjson(parent/'iteration_4_prediction.json');eps=readjson(parent/'iteration_4_endpoints.json');oldbudgets=readjson(parent/'iteration_4_budgets.json');refroot=base/'multiplier_native_reference_rc_budgets_2026-10-06';ref=readjson(refroot/'receipt.json');budgets=readjson(refroot/'budgets.json');assert sha(refroot/'budgets.json')==ref['budgets_sha256'];witness=readjson(refroot/'native_class_witness.json');assert sha(refroot/'native_class_witness.json')==ref['native_class_witness_sha256'];paths={(r['net_id'],r['source'],r['sink']):r['native_paths'] for r in witness};protocol=readjson(base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/protocol.json');graph=protocol['inputs']['graph'];m,f=read(base/'multiplier_family_length_switch_csr_2026-10-06'/name/'csr',graph['sha256']);rc=IntegerRC(ExactBufferedRC(f,*load(base/'multiplier_cw300_exact_buffered_rc_classes_2026-10-06'/name,graph['sha256'])));xml=ImmutableXMLAudit(graph['path'],graph['sha256']);slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};bs={r['connection_id']:r for r in budgets};assert rc.scale==ref['integer_scale'];encode=lambda x:(json.dumps(x)+'\n').encode()
def state(rows):
 unions=defaultdict(set)
 for r in rows:
  unions[r['net_id']].add(r['source'])
  for eid in r['physical_edge_ids']:unions[r['net_id']].update(slots[eid])
 return unions,Counter(n for u in unions.values() for n in u)
def pressure(occ):
 p=ChannelPressure(f['types'],f['capacities']);p.refresh(occ,range(m['nodes']));return p.payload(graph['sha256']).encode()
_,initialocc=state(oldpred['connections']);placement=base/'multiplier_placement_swap_2026-10-06'/name/'swapped.place';bindings[str(placement)]=sha(placement);old=MoveState(5,hashlib.sha256(encode(bindings)).hexdigest(),placement.read_bytes(),encode(eps),encode(oldpred),encode(oldbudgets),pressure(initialocc),b'[]');tx=MovePredictionTransaction(old);reports=[]
def build(s,fault=None):
 rows=json.loads(s.prediction)['connections'];groups=defaultdict(list)
 for r in rows:groups[r['net_id']].append(r)
 repairs=[]
 for net,values in groups.items():
  if any(rc.path(r['source'],r['sink'],r['physical_edge_ids'])>bs[r['connection_id']]['scaled_integer_budget'] for r in values):
   repairs.append(net)
   for r in values:
    values=paths[(r['net_id'],r['source'],r['sink'])];assert len(values)==1;r['physical_edge_ids']=values[0]['physical_edge_ids'];r['method']='native_reference_repair'
 if fault=='after_budget_repair':raise RuntimeError(fault)
 for net,blocked in ((4,{255,259,263,267}),(11,{255})):
  unions,occ=state(rows);other=occ.copy();other.subtract(unions[net]);region=RCFeasibleCostRegion(m['nodes'],[(u,f['dest_ranks'][i],rc.increments[i],int(f['costs'][i])) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if u not in blocked and f['dest_ranks'][i] not in blocked and f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0]);count=0
  for r in groups[net]:
   assert r['source'] not in blocked and r['sink'] not in blocked
   result=query(rc,r['source'],r['sink'],bs[r['connection_id']]['scaled_integer_budget'],lambda u,i:u not in blocked and f['dest_ranks'][i] not in blocked and f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0,lambda u,i:int(f['costs'][i])*(1+other[f['dest_ranks'][i]]),region.distance(r['sink'],True),10000);assert result['status']=='FOUND';r['physical_edge_ids']=result['physical_edge_ids'];r['method']='live_joint_avoidance';count+=1
   if fault==f'during_net_{net}' and count==1:raise RuntimeError(fault)
  if fault=='after_net4' and net==4:raise RuntimeError(fault)
 unions,occ=state(rows);pred={**oldpred,'connections':rows,'node_occupancy':{str(n):v for n,v in occ.items() if v},'methods':dict(Counter(r['method'] for r in rows))};audit=xml.verify(eps,pred,topology=True);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==0
 for net in set(repairs)|{4,11}:
  r=next(x for x in audit['net_union_topology']['nets'] if x['net_id']==net);assert not r['cyclic_union'] and not r['internal_multi_incoming_nodes'] and not r['source_has_incoming']
 if fault=='after_audit':raise RuntimeError(fault)
 payload=pressure(occ)
 if fault=='after_pressure':raise RuntimeError(fault)
 candidate=MoveState(s.epoch+1,s.context,s.placement,s.endpoints,encode(pred),encode(budgets),payload,b'[]')
 if fault is None:reports.append({'repaired_nets_for_budget_switch':repairs,'searched_nets':[4,11],'overflow':0})
 return candidate

def validate(s):
 rows=json.loads(s.prediction)['connections'];assert s.placement==old.placement and s.endpoints==old.endpoints and json.loads(s.budgets)==budgets and s.search_cache==b'[]';assert len(rows)==len(bs)==len({r['connection_id'] for r in rows})
 for r in rows:
  b=bs[r['connection_id']];assert all(r[k]==b[k] for k in ('net_id','source','sink'));assert rc.path(r['source'],r['sink'],r['physical_edge_ids'])<=b['scaled_integer_budget']
 _,occ=state(rows);assert s.pressure==pressure(occ);return True
failures=[]
for phase in ('after_budget_repair','during_net_4','after_net4','during_net_11','after_audit','after_pressure'):
 assert tx.commit(5,lambda s:build(s,phase),validate)=='FAILED' and tx.snapshot() is old;failures.append(phase)
def success(s):
 try:return build(s)
 except Exception:
  import traceback;traceback.print_exc();raise
assert tx.commit(5,success,validate)=='COMMITTED';current=tx.snapshot();(out/'prediction.json').write_bytes(current.prediction);(out/'candidate.pressure').write_bytes(current.pressure);assert all(sha(p)==h for p,h in bindings.items());(out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'prediction_sha256':sha(out/'prediction.json'),'pressure_sha256':sha(out/'candidate.pressure'),'budget_policy':ref['budget_policy'],'previous_epoch':5,'published_epoch':current.epoch,'failures_preserved_old_snapshot':failures,'reports':reports,'scope':'Live private Python reduced-graph joint NET4/11 search, complete native-reference budget-change repair, joint whole-snapshot publication. New budgets are explicit postroute calibration; unchanged placement/endpoints. Empty cache; no native search/native route/STA/performance or filesystem atomicity claim.'},indent=2)+'\n');print(reports,failures)

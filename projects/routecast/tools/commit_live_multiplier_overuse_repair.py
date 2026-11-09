"""Publish audited full-NET avoidance witness with complete private validation."""
import json,shutil,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from prepared_csr import read,U64
from integer_rc_context import IntegerRC
from csr_integer_sink_bound_search import query
from rc_feasible_cost_region import RCFeasibleCostRegion
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from immutable_xml_prediction_audit import ImmutableXMLAudit
from incremental_channel_pressure import ChannelPressure
from move_prediction_transaction import MoveState,MovePredictionTransaction
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';name='mult_5x5';out=base/'multiplier_live_overuse_repair_transaction_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');bindings={}
def readjson(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
parent=base/'multiplier_rc_repeated_sweeps_2026-10-06'/name;prior=readjson(parent/'receipt.json');assert all(sha(parent/n)==h for n,h in prior['outputs_sha256'].items());proof=readjson(base/'multiplier_avoidance_candidates_xml_audit_2026-10-06/verification.json');assert all(sha(p)==h for p,h in proof['inputs_sha256'].items());candidatefile=base/'multiplier_rc_overuse_avoidance_2026-10-06/mult_5x5_net_19_candidate.json';assert proof['inputs_sha256'][str(candidatefile)]==sha(candidatefile);candidate=readjson(candidatefile);previous=readjson(parent/'iteration_4_prediction.json');eps=readjson(parent/'iteration_4_endpoints.json');budgets=readjson(parent/'iteration_4_budgets.json');protocol=readjson(base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/protocol.json');graph=protocol['inputs']['graph'];xml=ImmutableXMLAudit(graph['path'],graph['sha256']);m,f=read(base/'multiplier_family_length_switch_csr_2026-10-06'/name/'csr',graph['sha256']);rc=ExactBufferedRC(f,*load(base/'multiplier_cw300_exact_buffered_rc_classes_2026-10-06'/name,graph['sha256']));bindings.update(prior['inputs_sha256']);changed={r['connection_id'] for r in candidate['connections'] if r!=next(x for x in previous['connections'] if x['connection_id']==r['connection_id'])};assert changed and all(r['net_id']==19 for r in candidate['connections'] if r['connection_id'] in changed)
encode=lambda x:(json.dumps(x)+'\n').encode()
def pressure(pred):
 p=ChannelPressure(f['types'],f['capacities']);p.refresh(Counter({int(n):v for n,v in pred['node_occupancy'].items()}),range(m['nodes']));return p.payload(graph['sha256']).encode()
placement=(base/'multiplier_placement_swap_2026-10-06'/name/'swapped.place').read_bytes();old=MoveState(5,hashlib.sha256(encode(bindings)).hexdigest(),placement,encode(eps),encode(previous),encode(budgets),pressure(previous),b'[]');tx=MovePredictionTransaction(old)
def build(s,fault=None):
 pred=json.loads(s.prediction);integer=IntegerRC(rc);slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set)
 for r in pred['connections']:
  unions[r['net_id']].add(r['source'])
  for eid in r['physical_edge_ids']:unions[r['net_id']].update(slots[eid])
 occ=Counter(n for union in unions.values() for n in union);blocked={n for n,v in occ.items() if v>f['capacities'][n]};other=occ.copy();other.subtract(unions[19]);region=RCFeasibleCostRegion(m['nodes'],[(u,f['dest_ranks'][i],integer.increments[i],int(f['costs'][i])) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if u not in blocked and f['dest_ranks'][i] not in blocked and f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0]);bs={r['connection_id']:r for r in budgets};searched=0
 for r in pred['connections']:
  if r['net_id']!=19:continue
  assert r['source'] not in blocked and r['sink'] not in blocked
  result=query(integer,r['source'],r['sink'],bs[r['connection_id']]['scaled_integer_budget'],lambda u,i:u not in blocked and f['dest_ranks'][i] not in blocked and f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0,lambda u,i:int(f['costs'][i])*(1+other[f['dest_ranks'][i]]),region.distance(r['sink'],True),10000);assert result['status']=='FOUND';r['physical_edge_ids']=result['physical_edge_ids'];r['method']='avoid_overused';searched+=1
  if fault=='during_search' and searched==1:raise RuntimeError(fault)
 unions=defaultdict(set)
 for r in pred['connections']:
  unions[r['net_id']].add(r['source'])
  for eid in r['physical_edge_ids']:unions[r['net_id']].update(slots[eid])
 occ=Counter(n for union in unions.values() for n in union);pred['node_occupancy']={str(n):v for n,v in occ.items() if v};pred['methods']=dict(Counter(r['method'] for r in pred['connections']));assert pred==candidate
 audit=xml.verify(eps,pred,topology=True);assert audit['all_physical_and_union_checks_passed'];assert audit['all_type_overuse_units']==0
 net=next(x for x in audit['net_union_topology']['nets'] if x['net_id']==19);assert not net['internal_multi_incoming_nodes'] and not net['cyclic_union'] and not net['source_has_incoming']
 if fault=='after_audit':raise RuntimeError(fault)
 payload=pressure(pred)
 if fault=='after_pressure':raise RuntimeError(fault)
 if fault=='invalid_budget_witness':pred['connections'][0]['sink']+=1
 return MoveState(s.epoch+1,s.context,s.placement,s.endpoints,encode(pred),s.budgets,payload,b'[]')
def validate(s):
 assert s.placement==old.placement and s.endpoints==old.endpoints and s.budgets==old.budgets and s.search_cache==b'[]';pred=json.loads(s.prediction);bs={r['connection_id']:r for r in budgets}
 for r in pred['connections']:
  b=bs[r['connection_id']];assert all(r[k]==b[k] for k in ('net_id','source','sink'));from fractions import Fraction
  assert rc.path(r['source'],r['sink'],r['physical_edge_ids'])<=Fraction(*b['exact_delay_s'])
 assert s.pressure==pressure(pred);return True
failures=[]
for fault in ('during_search','after_audit','after_pressure','invalid_budget_witness'):
 status=tx.commit(5,lambda s:build(s,fault),validate);assert status=='FAILED' and tx.snapshot() is old;failures.append(fault)
assert tx.commit(5,build,validate)=='COMMITTED';current=tx.snapshot();assert current.epoch==6
(out/'prediction.json').write_bytes(current.prediction);(out/'candidate.pressure').write_bytes(current.pressure);assert all(sha(p)==h for p,h in bindings.items())
(out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'prediction_sha256':sha(out/'prediction.json'),'pressure_sha256':sha(out/'candidate.pressure'),'changed_connections':sorted(changed),'previous_epoch':5,'published_epoch':6,'old_overflow':1,'new_overflow':0,'failed_snapshot_identity_preserved':failures,'scope':'Live private Python wholeNET19 avoidance search matches independently XML-audited witness and is published via private immutable snapshot. Original placement/endpoints/budgets retained, empty cache. Search executes inside private transaction, no native search parity for the reduced graph, native legality/STA/performance or filesystem atomicity claim.'},indent=2)+'\n');print({'published_epoch':6,'overflow':0,'changed':sorted(changed),'failures':failures})

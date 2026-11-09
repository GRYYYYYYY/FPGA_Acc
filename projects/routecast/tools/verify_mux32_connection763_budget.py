"""Exact path validation and full candidate substitution topology audit."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_connection763_budget_2026-10-07';p=out/'protocol.json';d=out/'diagnosis.json';protocol=json.loads(p.read_text());r=json.loads(d.read_text());assert r['protocol_sha256']==sha(p);assert all(sha(f)==h for f,h in protocol['bindings'].items())
graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml';a=ImmutableXMLAudit(graph,sha(graph));ids,classes,switches,_=read(graph);q=protocol['query'];candidate=json.loads((ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/w32_m2/result.json').read_text())['result']['candidate'];unions=defaultdict(set)
for record in candidate['records']:
 used=unions[record['net_id']];used.add(record['source'])
 for eid in record['answer']['physical_edge_ids']:e=a.graph.edges[eid];used.update((e.source,e.sink))
ledger=Counter(n for u in unions.values() for n in u);assert dict(ledger)=={int(k):v for k,v in candidate['ledger'].items()}
other={n:count-int(n in unions[q['net_id']]) for n,count in ledger.items()}
for name in ('relaxed','residual'):
 witness=r[name];node=q['source'];res,cap=classes[ids[node]];delay=res*cap/2;used={node}
 for eid in witness['physical_edge_ids']:
  e=a.graph.edges[eid];assert e.source==node and e.sink not in used and a.caps[e.sink]>0
  if name=='residual':assert other.get(e.sink,0)<a.caps[e.sink]
  node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
 assert node==q['sink'] and delay==F(witness['delay_seconds'])<=F(protocol['budget_seconds'])
parents=defaultdict(dict);newunions=defaultdict(set);conflicts=[];delays={}
for record in candidate['records']:
 cid=record['connection_id'];net=record['net_id'];node=record['source'];newunions[net].add(node)
 edges=r['residual']['physical_edge_ids'] if cid==763 else record['answer']['physical_edge_ids']
 for eid in edges:
  e=a.graph.edges[eid];assert e.source==node
  incoming=(node,eid)
  if e.sink in parents[net] and parents[net][e.sink]!=incoming:conflicts.append(dict(net_id=net,node=e.sink,connection_id=cid))
  parents[net][e.sink]=incoming;node=e.sink;newunions[net].add(node)
 assert node==record['sink']
 delays[str(cid)]=F(r['residual']['delay_seconds'])*10**9 if cid==763 else F(record['answer']['delay']*10**9,candidate['scale'])
newledger=Counter(n for used in newunions.values() for n in used);overflow=sum(max(0,v-a.caps[n]) for n,v in newledger.items())
load=lambda path:json.loads((ROOT/path).read_text())
dag=ExactTimingDAG.from_native_metadata(load('experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json'),load('experiments/mux_full_timing_rr_2026-10-06/w32.json'),load('experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json'),delays)
result=dict(source_sha256=sha(Path(__file__)),diagnosis_sha256=sha(d),protocol_sha256=sha(p),relaxed_path_ns=str(F(r['relaxed']['delay_seconds'])*10**9),residual_path_ns=str(F(r['residual']['delay_seconds'])*10**9),replacement_parent_conflicts=conflicts,replacement_overflow_units=overflow,replacement_model_cpd_ns=str(dag.cpd),scope='Original XML path delay/capacity witnesses validated, not independent optimality proof. Single-connection substitution full union/parent conflicts and model timing audited; no native legality/STA or gain guarantee.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

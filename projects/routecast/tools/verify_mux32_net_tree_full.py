"""Independent physical paths, full union topology and backward timing audit."""
import json
from pathlib import Path
from collections import defaultdict,Counter,deque
from fractions import Fraction as F
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_net_tree_full_2026-10-07';p=out/'protocol.json';rp=out/'receipt.json';cp=out/'candidate.json';r=json.loads(rp.read_text());protocol=json.loads(p.read_text());c=json.loads(cp.read_text());assert r['protocol_sha256']==sha(p) and r['candidate_sha256']==sha(cp);assert all(sha(f)==h for f,h in {**protocol['sources'],**protocol['inputs']}.items())
graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml';a=ImmutableXMLAudit(graph,c['graph_sha256']);ids,classes,switches,_=read(graph);old=json.loads((ROOT/'experiments/mux32_critical_repair_2026-10-07/candidate.json').read_text());before={q['connection_id']:q for q in old['records']};records={q['connection_id']:q for q in c['records']};assert len(records)==len(c['records'])==1929 and records.keys()==before.keys();changed=[];unions=defaultdict(set);parents=defaultdict(dict);delays={}
for cid,q in records.items():
 assert (q['net_id'],q['source'],q['sink'])==(before[cid]['net_id'],before[cid]['source'],before[cid]['sink'])
 if q['answer']['physical_edge_ids']!=before[cid]['answer']['physical_edge_ids']:changed.append(cid)
 node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;net=q['net_id']
 for eid in q['answer']['physical_edge_ids']:
  e=a.graph.edges[eid];assert e.source==node and e.sink not in used and a.caps[e.sink]>0
  incoming=(node,eid);assert e.sink not in parents[net] or parents[net][e.sink]==incoming
  parents[net][e.sink]=incoming;node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
 assert node==q['sink'] and delay==F(q['answer']['delay'],c['scale'])
 unions[net].update(used);delays[str(cid)]=delay*10**9
ledger=Counter(n for used in unions.values() for n in used);assert dict(ledger)=={int(k):v for k,v in c['ledger'].items()};assert all(count<=a.caps[n] for n,count in ledger.items());assert all(records[cid]['net_id'] in {e['net_id'] for e in r['trace'] if e['accepted']} for cid in changed)
load=lambda name:json.loads((ROOT/name).read_text())
g=load('experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json');m=load('experiments/mux_full_timing_rr_2026-10-06/w32.json');meta=load('experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json');adj=defaultdict(list);ind={int(n):0 for n in g['nodes']}
for eid,e in g['edges'].items():
 if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
queue=deque(n for n in ind if not ind[n]);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for v,eid in adj[u]:
  ind[v]-=1
  if not ind[v]:queue.append(v)
assert len(order)==len(ind);tail={n:F(0) for n in order}
for u in reversed(order):
 for v,eid in adj[u]:
  cid=meta['edge_connection_ids'].get(eid);value=(delays[str(cid)]+F(m['external_edges'][eid]['old_local_offset_seconds'])*10**9) if cid is not None else F(g['edges'][eid]['max_delay_seconds'])*10**9
  tail[u]=max(tail[u],value+tail[v])
assert max(tail.values())==F(r['final_cpd_ns'])<=F(r['target_cpd_ns'])
wire=sum(a.spans[n]*count for n,count in ledger.items() if a.types[n] in (4,5))
assert wire==r['final_wirelength'] and wire<=r['initial_wirelength']
assert all(F(records[cid]['answer']['delay'],c['scale'])<=F(before[cid]['answer']['delay'],old['scale'])*F(5,4) for cid in changed)
result=dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(rp),candidate_sha256=sha(cp),connections=1929,changed_connections=sorted(changed),channel_union_wirelength=wire,backward_model_cpd_ns=str(max(tail.values())),parent_conflicts=0,overflow_units=0,scope='Independent original XML full physical path/RC/NET tree/ledger and backward DAG audit. Existing endpoints identity preserved. No native FULL/STA, pin legality, prospective result or netgain guarantee.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

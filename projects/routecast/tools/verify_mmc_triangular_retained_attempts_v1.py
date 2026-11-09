"""Independent XML/Fraction audit of all replay attempts and feasible initial witnesses."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from exact_rc_lattice_unique_pairs_v1 import exact_scale
D=R/'experiments/mmc_triangular_retained_attempt_replay_v1_2026-10-09';model=R/'experiments/mmc_triangular_span_v9_2026-10-09/model'
bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
r=load(D/'receipt.json');assert r['all_retained_failed_ID_lists_exactly_replayed'] and r['retained_events']==2192
for p,h in r['bindings'].items():assert sha(p)==h;bindings[p]=h
protocol=load(model.parent/'protocol.json');ep=load(Path(protocol['endpoint']));graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==ep['graph_sha256'];scale,_=exact_scale(ids,classes,switches,xml.graph.edges)
queries={q['connection_id']:q for q in ep['connections']};initial=load(model/'initial.json');witnesses={x['connection_id']:x for x in initial['records']};states=[load(model/'round0.json'),load(model/'round1.json')];receipt=load(model/'receipt.json');original={(i,e['net_id']):e for i,row in enumerate(receipt['rounds']) for e in row['events'] if e['status']=='RETAIN_BUDGET_OR_UNREACHABLE'}
rows=load(D/'attempts.json');assert len(rows)==len(original)==2192 and {(x['round'],x['net_id']) for x in rows}==set(original)
weight=load(model/'protocol.json')['price_unit_integer'];assert weight==scale//(20*10**9)
def path(q,edges,prices,parents=None):
 u=q['source'];seen={u};assert xml.graph.nodes[u].capacity>0;a,b=classes[ids[u]];delay=a*b/2;price=0
 for eid in edges:
  e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen and xml.graph.nodes[e.sink].capacity>0
  if parents is not None:assert e.sink not in parents or parents[e.sink]==(u,eid);parents[e.sink]=(u,eid)
  delay+=arc_delay(classes,switches,ids[e.sink],e.switch_id);u=e.sink;seen.add(u);price+=prices.get(str(u),0)
 assert u==q['sink'];integer=delay*scale;assert integer.denominator==1
 return integer.numerator,integer.numerator+weight*price
query_ids=defaultdict(set)
for cid,q in queries.items():query_ids[q['net_id']].add(cid)
counts=Counter();max_excess=0
for row in rows:
 event=original[row['round'],row['net_id']];prices=states[row['round']]['prices'];parents={};bad=[]
 expected=query_ids[row['net_id']]
 assert {a['connection_id'] for a in row['attempts']}==expected and len(row['attempts'])==len(expected)
 for attempt in row['attempts']:
  cid=attempt['connection_id'];q=queries[cid];w=witnesses[cid];assert all(w[k]==q[k] for k in q)
  delay,wcost=path(q,w['answer']['physical_edge_ids'],prices);assert delay==w['answer']['delay']==attempt['feasible_initial_delay']<=w['budget_integer']==attempt['budget']
  assert attempt['reason']!='NOT_SETTLED'
  delay,cost=path(q,attempt['physical_edge_ids'],prices,parents);assert delay==attempt['raw_RC'] and cost<=wcost
  excess=max(0,delay-attempt['budget']);assert excess==attempt['excess']
  if excess:assert attempt['reason']=='RAW_RC_ABOVE_BUDGET';bad.append(cid);counts['raw_RC_above_budget']+=1;max_excess=max(max_excess,excess)
  else:assert attempt['reason']=='BUDGET_SAFE_IN_RETAINED_NET';counts['budget_safe_connection_in_retained_NET']+=1
  counts['audited_attempt_paths']+=1;counts['audited_feasible_initial_witnesses']+=1
 assert bad==event['failed_connection_ids']==row['failed_connection_ids']
assert counts['raw_RC_above_budget']==r['reasons']['raw_RC_above_budget'] and counts['audited_attempt_paths']==r['attempted_connections']
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,all_original_XML_paths_Fraction_RC_budgets_and_weighted_witness_comparisons_pass=True,retained_events=2192,counts=dict(counts),max_raw_RC_excess=max_excess,scope='Every retained NET replayed; every returned attempted tree independently checked against original XML arcs/positive capacity/acyclic/parent/Fraction RC. All attempts have budget-feasible authenticated initial paths, and attempted weighted cost <= witness weighted cost. This does not prove constrained-weighted optimum or causal recovery/quality/native runtime gains. Recorded archive originally lacks attempted paths; paths come from deterministic unchanged-search diagnostic replay.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)

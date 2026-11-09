"""Independent XML paths, Fraction RC, exact scope, perNET parents and both demand ledgers."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_fraction_arc_context_v2 import load_context
from buffered_rc_node_classes import read
from independent_fraction_arc_context_v2 import arc_delay
out=Path(sys.argv[1]).resolve();rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert p['bindings']==r['bindings'];bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());endpoint=next(Path(k) for k in r['bindings'] if k.endswith('/endpoints.json'));ep=json.loads(endpoint.read_text());floorfile=out/'floors.json';floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(floorfile.read_text())};graph=Path(ep['inputs']['graph']['path']);xml,ids,classes,switches,digest=load_context(graph,ep['graph_sha256']);assert digest==ep['graph_sha256'];which=sys.argv[2];assert which in ['initial','sketch'];c=json.loads((out/(which+'.json')).read_text());assert c['graph_sha256']==digest and c['eligible_for_legal_route_commit'] is False;assert c['status']=='COMPLETE_DEMAND_SKETCH' and not c['failures'] and c['failure'] is None;queries={q['connection_id']:q for q in ep['connections']};assert len(queries)==len(ep['connections'])==c['required_connections']==c['completed_connections']==len(c['records']);assert {x['connection_id'] for x in c['records']}==set(queries);owners=defaultdict(set);parents=defaultdict(dict);independent=Counter()
# Recover the exact RC lattice scale independently from graph parameters.
from exact_rc_lattice_direct_pairs_v2 import exact_scale
scale,electrical_pairs=exact_scale(ids,classes,switches,xml.graph.edges)
for rec in c['records']:
 q=queries[rec['connection_id']];assert all(rec[k]==q[k] for k in q);u=q['source'];used={u};a,b=classes[ids[u]];delay=a*b/2;assert xml.graph.nodes[u].capacity>0
 for eid in rec['answer']['physical_edge_ids']:
  e=xml.graph.edges[eid];assert e.source==u and e.sink not in used and xml.graph.nodes[e.sink].capacity>0;v=e.sink;incoming=(u,eid);assert v not in parents[q['net_id']] or parents[q['net_id']][v]==incoming;parents[q['net_id']][v]=incoming;used.add(v);delay+=arc_delay(classes,switches,ids[v],e.switch_id);u=v
 assert u==q['sink'];integer=delay*scale;assert integer.denominator==1 and integer.numerator==rec['answer']['delay'];floor=floors[q['source'],q['sink']];budget=max(scale//10**9,(3*floor+1)//2);assert rec['floor_integer']==floor and rec['budget_integer']==budget and integer<=budget;owners[q['net_id']].update(used);independent.update(used)
ledger=Counter(n for owned in owners.values() for n in owned);assert dict(ledger)=={int(n):v for n,v in c['ledger'].items()};assert dict(independent)=={int(n):v for n,v in c['independent_connection_ledger'].items()};overflow=sum(max(0,v-xml.graph.nodes[n].capacity) for n,v in ledger.items());assert overflow==c['overflow_units']==(r['rounds'][0]['overflow_before'] if which=='initial' else r['rounds'][-1]['overflow_after']);assert c['overflow_nodes']==sum(v>xml.graph.nodes[n].capacity for n,v in ledger.items());assert all(sha(k)==h for k,h in bindings.items());Path(sys.argv[3]).resolve().write_text(json.dumps(dict(bindings=bindings,all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True,completed=len(queries),overflow_units=overflow,scope='Audited demand estimation, not legal joint route; no optimality/native QoR/heldout/workflow-gain proof.'),indent=2)+'\n');print('PASS soft demand',len(queries),overflow,flush=True)

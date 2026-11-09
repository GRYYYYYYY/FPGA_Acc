"""All attempt paths against original XML/Fraction, allocation and exclusions."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_quadratic_history_online_loop_2026-10-06';protocol=json.loads((out/'protocol.json').read_text());last=None
for spec in protocol['cases']:
 w,i=spec['width'],spec['index'];file=out/f'w{w}_m{i}/result.json'
 if not file.exists():continue
 digest=sha(file);d=json.loads(file.read_text());ep=json.loads(Path(spec['target']).read_text());assert all(sha(f)==h for f,h in spec['inputs'].items())
 if w!=last:graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph);last=w
 template=(ROOT/'tools/verify_tseng_selected_reference_import.py').read_text();code=template[template.index('def check('):template.index('inc=json.loads')];code=code.replace("assert len(snapshot['records'])==len(queries)==1234 and {q['connection_id'] for q in snapshot['records']}==set(queries)","assert len(snapshot['records'])==snapshot['completed_connections'] and {q['connection_id'] for q in snapshot['records']}<=set(queries)");scope=dict(Counter=Counter,defaultdict=defaultdict,Fraction=Fraction,xml=xml,ids=ids,classes=classes,switches=switches,arc_delay=arc_delay);exec(code,scope);rows=[]
 for j,attempt in enumerate(d['attempts']):
  allocation=d['allocations'][attempt['allocation_index']];update=attempt['update'];candidate=update['repair'] or update['incremental'];scope['check'](candidate,ep);expanded=set(allocation['expanded']);initial=update['incremental'];assert set(initial['affected']['affected_complete_net_connection_ids'])==expanded;committed={e['query']['connection_id'] for e in initial['events'] if e['committed']};assert {q['connection_id'] for q in initial['records']}==({q['connection_id'] for q in ep['connections']}-expanded)|committed
  pair_bans={}
  for q in ep['connections']:
   bans=allocation['restrictions'].get(str(q['net_id']),[])
   if bans:pair_bans.setdefault((q['source'],q['sink']),set()).update(bans)
  checked=0;violations=[]
  for record in candidate['records']:
   cid=str(record['connection_id']);delay=Fraction(record['answer']['delay']*10**9,candidate['scale']);budget=Fraction(allocation['budgets_ns'][cid])
   if delay>budget:violations.append(dict(connection_id=int(cid),delay_ns=str(delay),budget_ns=str(budget)))
   bans=pair_bans.get((record['source'],record['sink']),set())
   if bans:
    used={record['source']}
    for eid in record['answer']['physical_edge_ids']:edge=xml.graph.edges[eid];used.update((edge.source,edge.sink))
    assert not used&bans;checked+=1
  rows.append(dict(attempt=j,paths=len(candidate['records']),restricted_paths=checked,budget_violations=violations))
 assert sha(file)==digest
 (file.parent/'physical_budget_verification.json').write_text(json.dumps(dict(result_sha256=digest,auditor_sha256=sha(Path(__file__)),rows=rows,scope='All attempts original XML/Fraction paths/parents/NETunion capacity, initial expanded release scope, surviving actual budgets and resource exclusions. Incomplete routes not native FULL/STA proof.'),indent=2)+'\n');print(w,i,'audited',sum(r['paths'] for r in rows),'paths',sum(len(r['budget_violations']) for r in rows),'budget violations',flush=True)

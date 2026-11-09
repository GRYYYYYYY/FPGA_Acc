"""Development subset pilot; no native labels used to rank or judge utility."""
import json,sys,time
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from whole_net_seed_selection_v2 import select
R=Path(__file__).resolve().parents[1];P=R/'experiments/resident_hybrid_complete_v5_2026-10-08/xtea/resident';proof=P/'sketch_physical_verification.json';v=json.loads(proof.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
assert all(sha(p)==h for p,h in v['bindings'].items())
snapshot=P/'sketch.json';c=json.loads(snapshot.read_text());assert sha(snapshot)==v['bindings'][str(snapshot)]
epfile=next(Path(p) for p in v['bindings'] if p.endswith('/endpoints.json'));ep=json.loads(epfile.read_text());ctx=ImmutableXMLAudit(ep['inputs']['graph']['path'],ep['graph_sha256']);required={q['connection_id'] for q in ep['connections']};D=R/'experiments/xtea_seed_selection_order_v1_2026-10-09';D.mkdir();rows=[]
for policy in ['connection_count','connection_per_channel_span']:
 tick=time.perf_counter();out=select(c['records'],required,ctx,policy);seconds=time.perf_counter()-tick
 groups=defaultdict(list)
 for r in c['records']:groups[r['net_id']].append(r)
 accepted={r['connection_id'] for r in out['records']};ledger=Counter()
 for net,recs in groups.items():
  states={r['connection_id'] in accepted for r in recs};assert len(states)==1
  if True in states:
   ledger.update({r['source'] for r in recs}|{ctx.graph.edges[e].sink for r in recs for e in r['answer']['physical_edge_ids']})
 assert dict(ledger)==out['ledger'] and all(n<=ctx.graph.nodes[k].capacity for k,n in ledger.items())
 assert not accepted.intersection(out['pending']) and accepted|set(out['pending'])==required
 f=D/(policy+'.json');f.write_text(json.dumps(out)+'\n');rows.append(dict(policy=policy,retained_connections=len(accepted),pending_connections=len(out['pending']),admitted_nets=sum(r['admitted'] for r in out['decisions']),seconds=seconds,whole_net_and_capacity_and_complete_partition_pass=True,output_sha256=sha(f)))
assert all(sha(p)==h for p,h in v['bindings'].items());bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(snapshot):sha(snapshot),str(epfile):sha(epfile)}
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='XTEA development input-only ordering pilot. All omitted connections remain required. No native pin/canonical admission, native reroute, QoR, heldout or gain proof. Higher coverage alone is not a utility metric.'),indent=2)+'\n');print(json.dumps(rows,indent=2))

"""Frozen whole-NET capacity admission; omitted NETs remain required native work."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
base=R/'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07';proof=R/'experiments/fresh_resident_soft_demand_verification_v1_2026-10-07/verification.json';verified=json.loads(proof.read_text());assert verified['fresh_conversion_floors_initial_and_complete_rounds_reference_parity_pass'];out=R/'experiments/resident_native_seed_subset_v1_2026-10-07';out.mkdir();bindings={**closure([Path(__file__)]),str(proof):sha(proof)};rows=[];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='All three existing development cases. Admit complete NET trees in descending requested CID count, ascending unique tree node count, ascending original NET ID. Charge each NET-node once, all original positive node capacities; reject completeNET if any charge exceeds capacity. No native labels or oracle ranking. OmittedNETs are ALL required for subsequent exact native routing, not dropped acceptance. Physical capacity-compatible subset not yet native pin/nonconfigurable/canonical admission.'),indent=2)+'\n')
for row in verified['rows']:
 begin=time.perf_counter();name=row['name'];sp=base/name/'resident/sketch.json';epfile=base/name/'endpoints.json'
 for path in [sp,epfile]:assert sha(path)==verified['bindings'][str(path)];bindings[str(path)]=sha(path)
 ep=json.loads(epfile.read_text());c=json.loads(sp.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);groups=defaultdict(list)
 for rec in c['records']:groups[rec['net_id']].append(rec)
 def own(recs):return {x['source'] for x in recs}|{xml.graph.edges[eid].sink for x in recs for eid in x['answer']['physical_edge_ids']}
 owners={n:own(recs) for n,recs in groups.items()};order=sorted(groups,key=lambda n:(-len(groups[n]),len(owners[n]),n));ledger=Counter();kept=[];rejected=[];decisions=[]
 for net in order:
  blockers=sorted(n for n in owners[net] if ledger[n]+1>xml.graph.nodes[n].capacity)
  if blockers:rejected.append(net)
  else:ledger.update(owners[net]);kept.append(net)
  decisions.append(dict(net_id=net,admitted=not blockers,blocking_nodes=blockers))
 records=sorted([x for n in kept for x in groups[n]],key=lambda x:x['connection_id']);allids={q['connection_id'] for q in ep['connections']};retainedids={x['connection_id'] for x in records};pending=sorted(allids-retainedids);assert len(retainedids)==len(records) and len(allids)==c['required_connections'];w=out/name;w.mkdir();payload=dict(records=records,ledger=dict(ledger),retained_nets=sorted(kept),required_reroute_nets=sorted(rejected),required_reroute_connection_ids=pending,retained_connections=len(records),required_connections=len(allids),graph_sha256=ep['graph_sha256'],native_admission_verified=False,eligible_for_full_route_commit=False);(w/'subset.json').write_text(json.dumps(payload)+'\n');(w/'decisions.json').write_text(json.dumps(decisions)+'\n');rows.append(dict(name=name,retained_nets=len(kept),reroute_nets=len(rejected),retained_connections=len(records),required_connections=len(allids),reroute_connections=len(pending),selection_seconds=time.perf_counter()-begin));print('NET SUBSET',rows[-1],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')

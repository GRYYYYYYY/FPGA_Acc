"""Independent exact wholeNET partition, greedy replay and capacity proof."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/resident_native_seed_subset_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());rows=[]
for row in r['rows']:
 name=row['name'];ep=json.loads((R/f'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07/{name}/endpoints.json').read_text());c=json.loads((R/f'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07/{name}/resident/sketch.json').read_text());xml=ImmutableXMLAudit(Path(ep['inputs']['graph']['path']),ep['graph_sha256']);p=json.loads((out/name/'subset.json').read_text());groups=defaultdict(list)
 for rec in c['records']:groups[rec['net_id']].append(rec)
 def own(recs):return {x['source'] for x in recs}|{xml.graph.edges[eid].sink for x in recs for eid in x['answer']['physical_edge_ids']}
 owned={n:own(recs) for n,recs in groups.items()};ledger=Counter();kept=[];rejected=[];decisions=[]
 for n in sorted(groups,key=lambda n:(-len(groups[n]),len(owned[n]),n)):
  blocked=sorted(v for v in owned[n] if ledger[v]+1>xml.graph.nodes[v].capacity);decisions.append(dict(net_id=n,admitted=not blocked,blocking_nodes=blocked))
  if blocked:rejected.append(n)
  else:kept.append(n);ledger.update(owned[n])
 assert decisions==json.loads((out/name/'decisions.json').read_text());assert sorted(kept)==p['retained_nets'] and sorted(rejected)==p['required_reroute_nets'];assert p['records']==sorted([rec for n in kept for rec in groups[n]],key=lambda x:x['connection_id']);assert dict(ledger)=={int(n):c for n,c in p['ledger'].items()};assert all(c<=xml.graph.nodes[n].capacity for n,c in ledger.items());retained={x['connection_id'] for x in p['records']};allids={q['connection_id'] for q in ep['connections']};remaining={q['connection_id'] for q in ep['connections'] if q['net_id'] in rejected};assert retained.isdisjoint(remaining) and retained|remaining==allids;assert sorted(remaining)==p['required_reroute_connection_ids'];assert p['retained_connections']==len(retained) and p['required_connections']==len(allids);assert p['native_admission_verified'] is False and p['eligible_for_full_route_commit'] is False;rows.append(row);print('PASS wholeNET subset and all required reroute partition',name,len(retained),len(remaining),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,wholeNET_selection_original_capacity_and_all_query_partition_pass=True,scope='Original XML node capacity subset only; native endpoint pin/nonconfigurable/localOPIN/canonical routing admission remains required. No partial commit or improved whole-route checkpoint.'),indent=2)+'\n')

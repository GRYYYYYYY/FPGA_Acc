"""Fixed all3 label-free capacity-compatible wholeNET seed preparation."""
import json,sys,time
from pathlib import Path
from collections import Counter,defaultdict
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
from stream_native_route_audit_expat_v3 import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_primary_budget_repair_v1_2026-10-19';T=E/'prospective_external_family_frame_timings_v1_2026-10-19';D=E/'prospective_external_family_native_utility_seed_inputs_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 begin=time.perf_counter();protocol=read(I/'protocol.json');D.mkdir(exist_ok=False);cases=[];bindings={str(I/'protocol.json'):sha(I/'protocol.json'),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/serialize_whole_net_subset_pin_index_v2.py'):sha(R/'tools/serialize_whole_net_subset_pin_index_v2.py')}
 for c in protocol['cases']:
  frame=I/c['case']/'sketch.json';proof=I/c['case']/'complete_trace_event_audit_v2.json';assert read(proof)['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(p)==h for p,h in read(proof)['bindings'].items());assert read(proof)['bindings'][str(frame)]==sha(frame);ep=read(c['endpoint']);timing=T/c['case'];tp=timing/'verification.json';a=read(tp);assert all(sha(p)==h for p,h in a['bindings'].items());payload=timing/'initial_connection_criticalities.json';values=read(payload);assert len(values)==len(ep['connections'])==15616;assert {r['connection_id'] for r in values}=={q['connection_id'] for q in ep['connections']};cases.append(dict(case=c['case'],frame=str(frame),proof=str(proof),endpoint=c['endpoint'],timing_proof=str(tp),pin_payload=str(payload),place=ep['inputs']['place']['path'],graph=ep['inputs']['graph']['path']))
  for p in [frame,proof,tp,payload,Path(c['endpoint'])]:bindings[str(p)]=sha(p)
 pp=D/'protocol.json';pp.write_text(json.dumps(dict(cases=cases,bindings=bindings,policy='Fixed current primary-budget-repair frames ALL3, no score-head/label/oracle input. Existing wholeNET policy descending CID fanout, ascending unique tree-node count, NETid; admit iff uniqueNET-node occupancy within original capacity. All sinks of admitted NET retained; every omitted NET/CID remains required native work. Existing indexed serializer, identity from already-verified pre-search current native pin snapshots and original RR coordinates. Static preparation only: native packed-pin/nonconfigurable import/canonical acceptance still pending. Original forecast/full9/family/native utility/full-time/hardware gates unchanged.'),indent=2)+'\n');bindings[str(pp)]=sha(pp);setup=time.perf_counter();inventory=Inventory(cases[0]['graph']);inventory_seconds=time.perf_counter()-setup;rows=[]
 for c in cases:
  tick=time.perf_counter();case=c['case'];out=D/case;out.mkdir(parents=True);ep=read(c['endpoint']);assert sha(c['graph'])==inventory.digest==ep['graph_sha256'];frame=read(c['frame']);groups=defaultdict(list)
  for q in frame['records']:groups[q['net_id']].append(q)
  owned={net:{q['source'] for q in recs}|{inventory.edges[e][1] for q in recs for e in q['answer']['physical_edge_ids']} for net,recs in groups.items()};order=sorted(groups,key=lambda n:(-len(groups[n]),len(owned[n]),n));counts=Counter();kept=[];rejected=[];decisions=[]
  for net in order:
   blockers=sorted(n for n in owned[net] if counts[n]+1>inventory.graph.nodes[n].capacity)
   if blockers:rejected.append(net)
   else:kept.append(net);counts.update(owned[net])
   decisions.append(dict(net_id=net,admitted=not blockers,blocking_nodes=blockers))
  selected=sorted([q for n in kept for q in groups[n]],key=lambda q:q['connection_id']);allids={q['connection_id'] for q in ep['connections']};selectedids={q['connection_id'] for q in selected};pending=sorted(allids-selectedids);assert len(selectedids)==len(selected) and set(groups)==set(kept)|set(rejected) and not set(kept)&set(rejected);candidate=dict(records=selected,ledger=dict(counts),retained_nets=sorted(kept),required_reroute_nets=sorted(rejected),required_reroute_connection_ids=pending,required_connections=len(allids),retained_connections=len(selected),graph_sha256=ep['graph_sha256'],native_admission_verified=False,eligible_for_full_route_commit=False)
  payload=read(c['pin_payload']);identities={};queries={q['connection_id']:q for q in ep['connections']}
  def pin(index,node):
   kind,loc=inventory.nodes[node];return dict(index=index,x=int(loc['xlow']),y=int(loc['ylow']),layer=int(loc.get('layer','0')),**{'class':int(loc['ptc'])})
  for r in payload:
   q=queries[r['connection_id']];name=ep['net_names'][str(q['net_id'])];assert (r['endpoint_net_id'],r['source_rr'],r['target_rr'],r['net_name'])==(q['net_id'],q['source'],q['sink'],name);native=r['native_net_id'];entry=identities.setdefault(name,dict(name=name,net_id=native,pins=[pin(0,q['source'])]));assert entry['net_id']==native and entry['pins'][0]==pin(0,q['source']);entry['pins'].append(pin(r['local_sink_pin'],q['sink']))
  identity=out/'identity.jsonl'
  with identity.open('x') as f:
   for name,row in sorted(identities.items()):
    assert sorted(p['index'] for p in row['pins'])==list(range(len(row['pins'])));row['pins'].sort(key=lambda p:p['index']);f.write(json.dumps(row)+'\n')
  (out/'subset.json').write_text(json.dumps(candidate)+'\n');(out/'decisions.json').write_text(json.dumps(decisions)+'\n');text,pins=serialize_subset(candidate,c['endpoint'],identity,c['place'],inventory);route=out/'seed.route';route.write_text(text);(out/'pin_bindings.json').write_text(json.dumps(pins)+'\n');physical=audit(c['graph'],route);expected=Counter((pins[q['connection_id']]['net'],q['source'],q['sink']) for q in selected);assert Counter((r['net_id'],r['source'],r['sink']) for r in physical['connections'])==expected and physical['overflow_units']==0;(out/'physical_audit.json').write_text(json.dumps(physical)+'\n');row=dict(case=case,retained_NETs=len(kept),required_native_reroute_NETs=len(rejected),retained_connections=len(selected),required_native_reroute_connections=len(pending),required_total_connections=len(allids),selection_serialization_physical_audit_seconds=time.perf_counter()-tick,native_import_admitted=False);rows.append(row)
  for p in out.iterdir():
   if p.is_file():bindings[str(p)]=sha(p)
  print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_CAPACITY_SUBSETS_CURRENT_NATIVE_PIN_BINDINGS_AND_SERIALIZED_PHYSICAL_PATHS_PREPARED',rows=rows,inventory_setup_seconds=inventory_seconds,total_preparation_seconds=time.perf_counter()-begin,bindings=bindings,scope='Static physical/path/indexed identity checks only. All omitted demands required native work. Packed pin-equivalence/nonconfigurable native import/canonical/STA not admitted; no native trial or full-route commit.'),indent=2)+'\n')
if __name__=='__main__':main()

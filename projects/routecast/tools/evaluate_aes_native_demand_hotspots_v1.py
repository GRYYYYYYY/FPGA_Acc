"""Fixed full development cohort and matched fresh cold labels, no best-round selection."""
import sys,json,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from rr_graph import read_rr_graph
from stream_native_route_audit import audit
from prediction_metrics import compare
from endpoint_bbox_demand_v1 import predict as geometry
out=R/'experiments/aes_native_demand_hotspots_v1_2026-10-08';out.mkdir();wire=R/'experiments/aes_native_demand_estimates_v1_2026-10-08';frontend=R/'experiments/aes_native_demand_frontend_v1_2026-10-08';cold=R/'experiments/aes_mapped_fresh_cold_v2_2026-10-08';names=['aes_cipher','aes_inv_cipher'];bindings=closure([Path(__file__)])
proof=R/'experiments/aes_verbose_canonical_v1_2026-10-08/physical_invariants_verification.json';p=json.loads(proof.read_text());assert all(sha(k)==v for k,v in p['bindings'].items());bindings[str(proof)]=sha(proof)
for name in names:
 for f in [frontend/name/'endpoints.json',wire/name/'resident/sketch.json',wire/name/'resident/initial.json']:bindings[str(f)]=sha(f)
 for filename,key in [('initial_physical_verification.json','all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'),('sketch_physical_verification.json','all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'),('verification.json','complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass')]:
  proof=wire/name/'resident'/filename;p=json.loads(proof.read_text());assert p[key] and all(sha(k)==v for k,v in p['bindings'].items());bindings[str(proof)]=sha(proof)
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'cases':names,'policy':'Fixed final round only, static50ps CHANspan vs initial RC, independent-count same wire paths, unfitted geometry. Same original graph/endpoints and NEW unseeded cold native labels for all methods. Original graph positive CHAN universe; same capacity-normalized spatial layer/x/y/type/segment bins, spatialtop20 and concrete top5percent. Both previously observed AES-derived mapped siblings NOT heldout; no case/round selection. Native quality/time already recorded separately.'},indent=2)+'\n');rows=[]
for name in names:
 start=time.perf_counter();w=out/name;w.mkdir();ep=json.loads((frontend/name/'endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);g=read_rr_graph(graph);assert g.sha256==ep['graph_sha256'];bindings[str(graph)]=sha(graph)
 c=json.loads((wire/name/'resident/sketch.json').read_text());initial=json.loads((wire/name/'resident/initial.json').read_text());assert all(x['completed_connections']==x['required_connections']==len(ep['connections']) for x in [c,initial]);geo,capacities=geometry(g.nodes,ep['connections']);ledgers={'wire_shared':{int(n):v for n,v in c['ledger'].items()},'wire_independent':{int(n):v for n,v in c['independent_connection_ledger'].items()},'rc_initial':{int(n):v for n,v in initial['ledger'].items()}}
 route=cold/name/'output.route';bindings[str(route)]=sha(route);native=audit(graph,route);assert native['overflow_units']==0;truth={int(n):v for n,v in native['node_occupancy'].items()};channels=sorted(n for n,x in g.nodes.items() if x.capacity>0 and x.type in {'CHANX','CHANY'});td=defaultdict(int);pd={m:defaultdict(int) for m in ledgers}
 for n in channels:
  node=g.nodes[n];loc=dict(node.location)
  for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
   for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
    key=(int(loc.get('layer','0')),x,y,node.type,node.segment_id if node.segment_id is not None else -1);td[key]+=truth.get(n,0)
    for m,l in ledgers.items():pd[m][key]+=l.get(n,0)
 metrics={m:{'concrete':compare({n:l.get(n,0)/g.nodes[n].capacity for n in channels},{n:truth.get(n,0)/g.nodes[n].capacity for n in channels},max(1,len(channels)//20)),'spatial':compare({k:pd[m][k]/cap for k,cap in capacities.items()},{k:td[k]/cap for k,cap in capacities.items()},20)} for m,l in ledgers.items()};metrics['geometry']={'concrete':None,'spatial':compare(geo,{k:td[k]/cap for k,cap in capacities.items()},20)}
 vectors={'channels':[{'node':n,'capacity':g.nodes[n].capacity,'native':truth.get(n,0),'predictions':{m:l.get(n,0) for m,l in ledgers.items()}} for n in channels],'bins':[{'key':list(k),'capacity':capacities[k],'native':td[k],'geometry':geo[k],'predictions':{m:pd[m][k] for m in ledgers}} for k in sorted(capacities)]};file=w/'comparison_vectors.json';file.write_text(json.dumps(vectors)+'\n');bindings[str(file)]=sha(file);rows.append({'name':name,'completed':len(ep['connections']),'required':len(ep['connections']),'metrics':metrics,'evaluation_seconds':time.perf_counter()-start});print(name,{m:(round(x['spatial']['spearman'],4),x['spatial']['precision_at_k']) for m,x in metrics.items()},flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'comparison.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n')

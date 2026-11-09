"""Original XML greedy replay, reference serializer and full model parity."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_v1 import serialize_subset
D=R/'experiments/sha1_native_handoff_v1_2026-10-10';bindings=closure([Path(__file__)])
def checked(p):
 d=json.loads(p.read_text());bindings[str(p)]=sha(p)
 for section in ['bindings','files']:
  for k,v in d.get(section,{}).items():assert sha(k)==v;bindings[k]=v
 return d
pipeline=checked(D/'handoff/receipt.json');model=D/'model';old=R/'experiments/sha1_frozen_model_v1_2026-10-10/sha1'
for directory in [old,model]:
 for n in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  p=checked(directory/n);assert p['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert p['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and p['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
for n in ['floors.json','initial.json','sketch.json','round0.json','round1.json']:
 a,b=old/n,model/n;assert json.loads(a.read_text())==json.loads(b.read_text());bindings.update({str(a):sha(a),str(b):sha(b)})
epf=R/'experiments/sha1_native_demand_v1_2026-10-10/sha1/endpoints.json';ep=checked(epf);c=checked(model/'sketch.json');subset=checked(D/'native/subset.json')
graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);bindings[str(graph)]=sha(graph)
groups=defaultdict(list)
for rec in c['records']:groups[rec['net_id']].append(rec)
owned={n:{x['source'] for x in recs}|{xml.graph.edges[e].sink for x in recs for e in x['answer']['physical_edge_ids']} for n,recs in groups.items()}
ledger=Counter();kept=[];decisions=[]
for n in sorted(groups,key=lambda n:(-len(groups[n]),len(owned[n]),n)):
 blocked=sorted(v for v in owned[n] if ledger[v]+1>xml.graph.nodes[v].capacity)
 decisions.append(dict(net_id=n,admitted=not blocked,blocking_nodes=blocked))
 if not blocked:kept.append(n);ledger.update(owned[n])
records=sorted([x for n in kept for x in groups[n]],key=lambda x:x['connection_id']);allids={q['connection_id'] for q in ep['connections']};selected={x['connection_id'] for x in records};pending=sorted(allids-selected)
assert subset==dict(records=records,pending=pending,decisions=decisions)
assert len(selected)==len(records) and selected.isdisjoint(pending) and selected|set(pending)==allids
assert all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items())
text,pins=serialize_subset(dict(records=records),epf,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),Inventory(graph))
assert (D/'native/seed.route').read_text()==text, 'reference route bytes differ'
assert json.loads((D/'native/bindings.json').read_text())==json.loads(json.dumps(pins)), 'reference pin bindings differ'
assert pipeline['selected_connections']==len(records) and pipeline['pending_connections']==len(pending) and pipeline['required_connections']==len(allids)
assert all(sha(k)==v for k,v in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,complete_model_frames_and_events_equal=True,complete_seed_bytes_pin_bindings_selection_and_pending_equal=True,required=len(allids),selected=len(records),pending=len(pending),scope='Full original XML greedy capacity replay and reference non-indexed serializer equality; fresh frames equal frozen SHA frames. No native import/canonical/full-cost gain proof.'),indent=2)+'\n')
print('PASS SHA full handoff',len(records),len(pending))

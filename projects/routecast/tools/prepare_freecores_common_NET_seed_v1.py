"""Development crossover: same complete NETs, two price-model tree sets.
Intersection is label-free and capacity-safe as subset of each audited admission.
"""
import sys,json,shutil
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_v1 import serialize_subset
D=R/'experiments/freecores_common_NET_seed_v1_2026-10-08';D.mkdir();bindings=closure([Path(__file__)]);cases=[]
for name in ['8051','xtea']:
 front=R/'experiments/freecores_native_demand_v1_2026-10-08'/name;epfile=front/'endpoints.json';ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile);graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph);inputs={};selected={}
 for mode in ['baseline','no_ipin']:
  model=R/('experiments/freecores_resident_v1_2026-10-08' if mode=='baseline' else 'experiments/freecores_no_ipin_dynamic_price_v1_2026-10-08')/name/'resident'
  proof=model/'verification.json';v=json.loads(proof.read_text());assert v['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and all(sha(k)==h for k,h in v['bindings'].items());sp=model/'sketch.json';bindings[str(proof)]=sha(proof);bindings[str(sp)]=sha(sp);inputs[mode]=str(sp)
  native=R/('experiments/freecores_native_seed_v1_2026-10-08' if mode=='baseline' else 'experiments/freecores_no_ipin_native_seed_v1_2026-10-08')/name;rp=native/'receipt.json';r=json.loads(rp.read_text());assert all(sha(k)==h for group in ['bindings','files'] for k,h in r[group].items());sf=native/'subset.json';subset=json.loads(sf.read_text());bindings[str(rp)]=sha(rp);bindings[str(sf)]=sha(sf);selected[mode]=dict(path=str(sf),nets=sorted({x['net_id'] for x in subset['records']}))
 cases.append(dict(name=name,endpoint=str(epfile),identity=str(front/'identity.jsonl'),graph=str(graph),models=inputs,selections=selected,common_NETs=sorted(set(selected['baseline']['nets'])&set(selected['no_ipin']['nets']))))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='Frozen development crossover from both previously observed price arms. Same NET identity set = intersection of both unchanged wholeNET selector admissions; each arm retains its own complete tree for these NETs. All other physical connections remain required pending native work. No native labels, tail NET lists or metric ranking used to choose intersection. No favorable case selection; native/budget/pin/canonical gates remain separate, no gain claim.'),indent=2)+'\n');rows=[]
for case in cases:
 name=case['name'];epfile=Path(case['endpoint']);ep=json.loads(epfile.read_text());xml=Inventory(Path(case['graph']));xml.validate(Path(case['graph']),ep['graph_sha256']);allqueries={q['connection_id']:q for q in ep['connections']};modelgroups={};selection_proofs={}
 def own(recs):return {x['source'] for x in recs}|{xml.graph.edges[eid].sink for x in recs for eid in x['answer']['physical_edge_ids']}
 for mode,sp in case['models'].items():
  c=json.loads(Path(sp).read_text());groups=defaultdict(list)
  for x in c['records']:assert all(x[k]==allqueries[x['connection_id']][k] for k in allqueries[x['connection_id']]);groups[x['net_id']].append(x)
  assert len(c['records'])==len(allqueries) and len({x['connection_id'] for x in c['records']})==len(allqueries);owned={n:own(recs) for n,recs in groups.items()};load=Counter();kept=[];decisions=[]
  for n in sorted(groups,key=lambda n:(-len(groups[n]),len(owned[n]),n)):
   blocked=sorted(v for v in owned[n] if load[v]+1>xml.graph.nodes[v].capacity);decisions.append(dict(net_id=n,admitted=not blocked,blocking_nodes=blocked))
   if not blocked:load.update(owned[n]);kept.append(n)
  archived=json.loads(Path(case['selections'][mode]['path']).read_text());assert decisions==archived['decisions'] and sorted(kept)==case['selections'][mode]['nets'];assert archived['records']==sorted([x for n in kept for x in groups[n]],key=lambda x:x['connection_id']);assert all(v<=xml.graph.nodes[n].capacity for n,v in load.items());modelgroups[mode]=groups;selection_proofs[mode]=dict(admitted_NETs=len(kept),retained_connections=len(archived['records']))
 common=set(case['common_NETs']);changed_NETs=sorted(n for n in common if [(x['connection_id'],x['answer']['physical_edge_ids']) for x in sorted(modelgroups['baseline'][n],key=lambda x:x['connection_id'])]!=[(x['connection_id'],x['answer']['physical_edge_ids']) for x in sorted(modelgroups['no_ipin'][n],key=lambda x:x['connection_id'])]);counts={}
 for mode,groups in modelgroups.items():
  w=D/name/mode;w.mkdir(parents=True);rr=R/'experiments/freecores_rr_only_v1_2026-10-08'/name
  for f in ['design.blif','design.net','design.place']:shutil.copyfile(rr/f,w/f);bindings[str(rr/f)]=sha(rr/f)
  records=sorted([x for n in common for x in groups[n]],key=lambda x:x['connection_id']);ids={x['connection_id'] for x in records};pending=sorted(set(allqueries)-ids);assert len(ids)==len(records) and ids.isdisjoint(pending) and ids|set(pending)==set(allqueries);load=Counter(n for net in common for n in own(groups[net]));assert all(v<=xml.graph.nodes[n].capacity for n,v in load.items());payload=dict(records=records,pending=pending,common_NETs=sorted(common),ledger=dict(load),required_connections=len(allqueries));(w/'subset.json').write_text(json.dumps(payload)+'\n');text,pins=serialize_subset(dict(records=records),epfile,Path(case['identity']),w/'design.place',xml);(w/'seed.route').write_text(text);(w/'bindings.json').write_text(json.dumps(pins)+'\n');counts[mode]=dict(retained_connections=len(records),pending_connections=len(pending));
 assert counts['baseline']==counts['no_ipin'];rows.append(dict(name=name,original_selection=selection_proofs,common_NET_count=len(common),common_tree_changed_NET_count=len(changed_NETs),common_tree_changed_NETs=changed_NETs,common_scope=counts['baseline'],all_wholeNET_greedy_capacity_and_full_query_partition_checks_pass=True));print(name,rows[-1]['common_NET_count'],rows[-1]['common_tree_changed_NET_count'],counts,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,files={str(p):sha(p) for p in D.rglob('*') if p.is_file()},scope='Prepared capacity-compatible crossover seeds, original full physical query partition; no native routing/FULL/canonical admission yet. Historical per-tree model audits authenticate raw RC budgets; capacity and greedy decisions independently replayed here.'),indent=2)+'\n')

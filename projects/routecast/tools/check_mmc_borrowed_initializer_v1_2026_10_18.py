"""All3real dirty-NET initializer workloads, unchanged answers/budgets/fallbacks."""
import collections,json,sys,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compiled_criticality_tree_v1 import Graph,BINARY
from retained_tree_frontier_state_v3 import GraphContext
from borrowed_compiled_frontier_v1 import Probe
from native_retained_net_initializer_v1 import initialize as baseline
from native_retained_net_initializer_observed_v2 import initialize as observed

def main():
 E=R/'experiments';out=E/'mmc_borrowed_initializer_probe_v1_2026-10-18';out.mkdir(exist_ok=False);corep=E/'borrowed_compiled_frontier_core_v1_2026-10-18/verification.json';core=json.loads(corep.read_text());assert core['status']=='borrowed_tree_read_only_and_initializer_output_stats_fallback_parity_pass';oldcorep=E/'native_retained_initializer_core_v3_2026-10-18/verification.json';oldcore=json.loads(oldcorep.read_text());assert sha(BINARY)==oldcore['bindings'][str(BINARY)];bindings={str(p):sha(p) for p in [corep,oldcorep,Path(__file__),BINARY,R/'tools/borrowed_compiled_frontier_v1.py',R/'tools/native_retained_net_initializer_observed_v2.py',R/'tools/native_retained_net_initializer_v1.py',R/'tools/retained_tree_frontier_state_v3.py',R/'tools/compiled_criticality_tree_v1.py',R/'tools/compact_stream_rc_endpoint_context_v1.py',R/'tools/raw_retained_tree_expand_v1.py',R/'tools/retained_criticality_tree_seed_v1.py']};cases={};oldp=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';source=json.loads(oldp.read_text());old={r['connection_id']:r for r in source['records']};assert len(old)==115572;bindings[str(oldp)]=sha(oldp)
 for case in ['case_01','case_02','case_03']:
  folder=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}';ap=folder/'initial_independent_verification_v1.json';audit=json.loads(ap.read_text());assert audit['status']=='pass' and audit['all115572V2budgets_matched'] and sha(oldp)==audit['bindings'][str(oldp)];bindings[str(ap)]=sha(ap);frames=[]
  for mode in ['native_retained','raw_min']:
   p=folder/mode/'initial.json';assert sha(p)==audit['bindings'][str(p)];bindings[str(p)]=sha(p);frames.append(json.loads(p.read_text()))
  eventp=folder/'native_retained/initializer_events.json';assert sha(eventp)==audit['bindings'][str(eventp)];bindings[str(eventp)]=sha(eventp);cases[case]=(frames,{e['net_id']:e for e in json.loads(eventp.read_text())})
 plan=dict(selection='All3existing independent-XML audited MMC native-retained initialization workloads, every dirty NET and sibling included. Original matched budgets and raw fallback answers unchanged.',probe='Borrow existing compiled tree.arrival. Report actual all-node seeds and terminal-excluded projection separately, before/after every raw expansion. Raw expand commit is not final NET admission.',equivalence='Baseline versus observed initializer return serialization, archived initialized answers, wholeNET fallback/retention events, complete query/NET ledgers, overflow and compiled work counters must all agree.',cost='Shared model graph setup and added geometry/probe setup separate; single baseline then observed function pass percase, no balanced speed claim. All observation work is new overhead. No new graph/NET ownership cache or compiled workspace per probe.')
 (out/'protocol.json').write_text(json.dumps(plan,indent=2));endpoint=E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';tick=time.perf_counter();graph,digest,nodes,fields,rc,_=load_endpoints(endpoint);g=Graph(fields,rc.increments,[rc.initial(n) for n in range(len(nodes))]);common_setup=time.perf_counter()-tick;assert digest==source['graph_sha256'];edge_ids=fields['edge_ids'];slots=range(len(edge_ids)) if all(i==e for i,e in enumerate(edge_ids)) else {e:i for i,e in enumerate(edge_ids)};kinds=tuple(n.get('type') for n in nodes);bindings[str(graph)]=sha(graph);bindings[str(endpoint)]=sha(endpoint);tick=time.perf_counter();geo={}
 for n,node in enumerate(nodes):
  loc=node.find('loc');geo[n]=(node.get('type'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']],int(loc.get('layer','0')))
 def edge_exists(a,b):return any(g.dest[i]==b for i in range(g.offsets[a],g.offsets[a+1]))
 context=GraphContext(digest,geo,edge_exists);probe=Probe(g,context);probe_setup=time.perf_counter()-tick;del geo;oldnodes={};byoldnet=collections.defaultdict(set)
 def pathnodes(q,answer):
  current=q['source'];seen={current}
  for edge in answer['physical_edge_ids']:
   slot=slots[edge];assert fields['edge_ids'][slot]==edge and g.offsets[current]<=slot<g.offsets[current+1];current=g.dest[slot];assert current not in seen;seen.add(current)
  assert current==q['sink'];return seen
 for cid,r in old.items():oldnodes[cid]=pathnodes(r,r['answer']);byoldnet[r['net_id']].update(oldnodes[cid])
 rows=[]
 for case,(frames,events_ref) in cases.items():
  reference,raw=frames;expected={r['connection_id']:r for r in reference['records']};minimum={r['connection_id']:r for r in raw['records']};queries={c:{k:r[k] for k in ['connection_id','net_id','source','sink']} for c,r in expected.items()};assert set(queries)==set(old);direct={c for c in old if (old[c]['source'],old[c]['sink'])!=(queries[c]['source'],queries[c]['sink'])};dirty={queries[c]['net_id'] for c in direct};groups=collections.defaultdict(list)
  for q in queries.values():groups[q['net_id']].append(q)
  assert dirty==set(events_ref) and reference['scale']==rc.scale;folder=out/case;folder.mkdir();results={};observations=[];timings={};counters={}
  for mode,fn in [('baseline',baseline),('observed',observed)]:
   outputs=[];answers={c:r['answer'] for c,r in old.items()};ledger=collections.Counter({int(n):v for n,v in source['ledger'].items()});independent=collections.Counter({int(n):v for n,v in source['independent_connection_ledger'].items()});elapsed=0.0;before=tuple(g.total_stats)
   for net in sorted(dirty):
    qs=sorted(groups[net],key=lambda q:q['connection_id']);budgets={q['connection_id']:expected[q['connection_id']]['budget_integer'] for q in qs};fallback=lambda qs=qs:{q['connection_id']:dict(minimum[q['connection_id']]['answer'],physical_edge_ids=list(minimum[q['connection_id']]['answer']['physical_edge_ids'])) for q in qs};tick=time.perf_counter();result=fn(g,fields,kinds,qs,[old[q['connection_id']] for q in qs],budgets,slots,fallback,**(dict(frontier_probe=probe,emit=lambda e:observations.append(dict(e))) if mode=='observed' else {}));elapsed+=time.perf_counter()-tick;assert dict(net_id=net,**{k:v for k,v in result.items() if k not in ['answers','owner_nodes']})==events_ref[net];outputs.append(dict(net_id=net,result=result));ledger.subtract(byoldnet[net]);ledger.update(result['owner_nodes'])
    for c,a in result['answers'].items():assert a==expected[c]['answer'];independent.subtract(oldnodes[c]);independent.update(pathnodes(queries[c],a));answers[c]=a
   counters[mode]=tuple(x-y for x,y in zip(g.total_stats,before));timings[mode]=elapsed;assert all(answers[c]==expected[c]['answer'] for c in answers);actual=+ledger;actual_i=+independent;assert dict(actual)=={int(n):v for n,v in reference['ledger'].items()} and dict(actual_i)=={int(n):v for n,v in reference['independent_connection_ledger'].items()};assert sum(max(0,v-fields['capacities'][n]) for n,v in actual.items())==reference['overflow_units'];blob=json.dumps(outputs,separators=(',',':')).encode();p=folder/(mode+'_initializer_returns.json');p.write_bytes(blob);results[mode]=dict(path=str(p),sha256=sha(p),bytes=len(blob))
  assert results['baseline']['sha256']==results['observed']['sha256'] and counters['baseline']==counters['observed'];assert len(observations)==2*sum(e['repair_calls'] for e in events_ref.values());p=folder/'observations.jsonl'
  with p.open('x') as f:
   for e in observations:f.write(json.dumps(e,separators=(',',':'))+'\n')
  rows.append(dict(case=case,dirty_NETs=len(dirty),changed_endpoint_CIDs=len(direct),complete_CIDs_checked=115572,observations=len(observations),repair_calls=sum(e['repair_calls'] for e in events_ref.values()),fallback_NETs=sum(e['whole_NET_fallback'] for e in events_ref.values()),compiled_work_counters=counters['baseline'],initializer_function_seconds=timings,results=results,observation_file=str(p),observation_sha256=sha(p),no_new_NET_or_search_workspace_per_observation=True));print('BORROWED INITIALIZER REAL PARITY PASS',case,len(dirty),len(observations),timings,flush=True)
 g.close();assert all(sha(p)==h for p,h in bindings.items())
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all3_real_initializer_answers_events_ledgers_budgets_and_compiled_work_unchanged',bindings=bindings,rows=rows,shared_model_graph_setup_seconds=common_setup,added_probe_geometry_context_setup_seconds=probe_setup,scope='Observer integrated into versioned initializer function, using its existing compiled trees. Not yet the complete Session/feedback/native producer flow. Captures are new overhead and do not change routing decisions; original quality/zero-counter/heldout/failure/hardware gates unchanged.'),f,indent=2)
if __name__=='__main__':main()

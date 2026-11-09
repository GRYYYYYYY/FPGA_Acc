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
from native_retained_frontier_order_v1 import initialize as candidate

def main():
 E=R/'experiments';out=E/'mmc_frontier_order_initial_v1_2026-10-18';out.mkdir(exist_ok=False);corep=E/'borrowed_compiled_frontier_core_v1_2026-10-18/verification.json';core=json.loads(corep.read_text());assert core['status']=='borrowed_tree_read_only_and_initializer_output_stats_fallback_parity_pass';oldcorep=E/'native_retained_initializer_core_v3_2026-10-18/verification.json';oldcore=json.loads(oldcorep.read_text());assert sha(BINARY)==oldcore['bindings'][str(BINARY)];bindings={str(p):sha(p) for p in [corep,oldcorep,Path(__file__),BINARY,R/'tools/borrowed_compiled_frontier_v1.py',R/'tools/native_retained_net_initializer_observed_v2.py',R/'tools/native_retained_net_initializer_v1.py',R/'tools/retained_tree_frontier_state_v3.py',R/'tools/compiled_criticality_tree_v1.py',R/'tools/compact_stream_rc_endpoint_context_v1.py',R/'tools/raw_retained_tree_expand_v1.py',R/'tools/retained_criticality_tree_seed_v1.py']};cases={};oldp=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';source=json.loads(oldp.read_text());old={r['connection_id']:r for r in source['records']};assert len(old)==115572;bindings[str(oldp)]=sha(oldp)
 sourceproofp=E/'mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json';sourceproof=json.loads(sourceproofp.read_text());assert sourceproof['all_native_paths_exact'] and sha(oldp)==sourceproof['bindings'][str(oldp)];bindings[str(sourceproofp)]=sha(sourceproofp)
 candidate_corep=E/'frontier_order_core_v1_2026-10-18/verification.json';candidate_core=json.loads(candidate_corep.read_text());assert candidate_core['reference_repair_calls']==600;specp=E/'mmc_frontier_order_candidate_protocol_v1_2026-10-18/protocol.json';spec=json.loads(specp.read_text());assert all(sha(p)==h for p,h in spec['bindings'].items());bindings[str(candidate_corep)]=sha(candidate_corep);bindings[str(specp)]=sha(specp);bindings[str(R/'tools/native_retained_frontier_order_v1.py')]=sha(R/'tools/native_retained_frontier_order_v1.py')
 for case in ['case_01','case_02','case_03']:
  folder=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}';ap=folder/'initial_independent_verification_v1.json';audit=json.loads(ap.read_text());assert audit['status']=='pass' and audit['all115572V2budgets_matched'] and sha(oldp)==audit['bindings'][str(oldp)];bindings[str(ap)]=sha(ap);frames=[]
  for mode in ['native_retained','raw_min']:
   p=folder/mode/'initial.json';assert sha(p)==audit['bindings'][str(p)];bindings[str(p)]=sha(p);frames.append(json.loads(p.read_text()))
  eventp=folder/'native_retained/initializer_events.json';assert sha(eventp)==audit['bindings'][str(eventp)];bindings[str(eventp)]=sha(eventp);cases[case]=(frames,{e['net_id']:e for e in json.loads(eventp.read_text())})
 plan=dict(spec=str(specp),spec_sha256=sha(specp),scope='Fixed source-only nearest-projected-frontier initialization candidate, all3exposed layouts. Original matched V2budgets, sibling retention and wholeNET raw fallback; paths/order/outcomes may differ. No native VPR policy trial. Independent XML/RC/selection verification and original feedback/cold gates pending.')
 (out/'protocol.json').write_text(json.dumps(plan,indent=2));endpoint=E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';tick=time.perf_counter();graph,digest,nodes,fields,rc,_=load_endpoints(endpoint);g=Graph(fields,rc.increments,[rc.initial(n) for n in range(len(nodes))]);common_setup=time.perf_counter()-tick;assert digest==sourceproof['bindings'][str(graph)];edge_ids=fields['edge_ids'];slots=range(len(edge_ids)) if all(i==e for i,e in enumerate(edge_ids)) else {e:i for i,e in enumerate(edge_ids)};kinds=tuple(n.get('type') for n in nodes);bindings[str(graph)]=sha(graph);bindings[str(endpoint)]=sha(endpoint);tick=time.perf_counter();geo={}
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
  assert dirty==set(events_ref) and reference['scale']==rc.scale;folder=out/case;folder.mkdir();answers={c:r['answer'] for c,r in old.items()};ledger=collections.Counter({int(n):v for n,v in source['ledger'].items()});independent=collections.Counter({int(n):v for n,v in source['independent_connection_ledger'].items()});elapsed=0.0;before=tuple(g.total_stats);outputs=[];traces=[];order_changes=0
  for net in sorted(dirty):
   qs=sorted(groups[net],key=lambda q:q['connection_id']);budgets={q['connection_id']:expected[q['connection_id']]['budget_integer'] for q in qs};fallback=lambda qs=qs:{q['connection_id']:dict(minimum[q['connection_id']]['answer'],physical_edge_ids=list(minimum[q['connection_id']]['answer']['physical_edge_ids'])) for q in qs};trace=[];tick=time.perf_counter();result=candidate(g,fields,kinds,qs,[old[q['connection_id']] for q in qs],budgets,slots,fallback,frontier_probe=probe,emit=lambda e:trace.append(dict(e)));elapsed+=time.perf_counter()-tick;outputs.append(dict(net_id=net,result=result));traces.extend(trace);chosen=[e['connection_id'] for e in trace if e['phase']=='select'];order_changes+=chosen!=sorted(chosen);ledger.subtract(byoldnet[net]);ledger.update(result['owner_nodes'])
   assert result['attempted_retained_connection_ids']==events_ref[net]['attempted_retained_connection_ids']
   for c,a in result['answers'].items():
    assert a['delay']<=expected[c]['budget_integer'];independent.subtract(oldnodes[c]);independent.update(pathnodes(queries[c],a));answers[c]=a
  work=tuple(x-y for x,y in zip(g.total_stats,before));actual=+ledger;actual_i=+independent;records=[dict(row,answer=answers[row['connection_id']]) for row in reference['records']];by_net=collections.defaultdict(set);full=collections.Counter()
  for row in records:
   owned=pathnodes(row,row['answer']);by_net[row['net_id']].update(owned);full.update(owned)
  assert full==actual_i and collections.Counter(n for ns in by_net.values() for n in ns)==actual
  initial=dict(reference,records=records,ledger={str(n):v for n,v in actual.items()},independent_connection_ledger={str(n):v for n,v in actual_i.items()},overflow_units=sum(max(0,v-fields['capacities'][n]) for n,v in actual.items()),eligible_for_legal_route_commit=False,initializer_policy='nearest_projected_retained_frontier_v1',scope='Fixed development source-only frontier-order model candidate; exact original matched budgets and fallback. Not a legal native route, quality promotion, unseen family or complete-time gain.')
  if 'overflow_nodes' in initial:initial['overflow_nodes']=sum(v>fields['capacities'][n] for n,v in actual.items())
  with (folder/'initial.json').open('x') as f:json.dump(initial,f);f.write('\n')
  with (folder/'initializer_returns.json').open('x') as f:json.dump(outputs,f)
  with (folder/'selection_trace.jsonl').open('x') as f:
   for trace in traces:f.write(json.dumps(trace,separators=(',',':'))+'\n')
  # Same matched floors/history files are input metadata, not candidate outcomes.
  sourcefolder=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained'
  for name in ['floors.json','history.json']:
   p=sourcefolder/name;assert not name.startswith('history') or json.loads(p.read_text())=={};(folder/name).write_bytes(p.read_bytes());bindings[str(p)]=sha(p)
  row=dict(case=case,dirty_NETs=len(dirty),changed_endpoint_CIDs=len(direct),repair_calls=sum(x['result']['repair_calls'] for x in outputs),fallback_NETs=sum(x['result']['whole_NET_fallback'] for x in outputs),NETs_with_changed_repair_order=order_changes,changed_path_CIDs=sum(answers[c]!=expected[c]['answer'] for c in answers),baseline_overflow=reference['overflow_units'],candidate_overflow=initial['overflow_units'],initializer_function_seconds=elapsed,compiled_work_counters=work,files={str(p):sha(p) for p in folder.iterdir() if p.is_file()});rows.append(row);print('FRONTIER ORDER MODEL INITIAL DONE',case,json.dumps({k:v for k,v in row.items() if k!='files'}),flush=True)
 g.close();assert all(sha(p)==h for p,h in bindings.items())
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='all3_frontier_order_model_initials_produced_independent_audit_pending',bindings=bindings,rows=rows,shared_model_graph_setup_seconds=common_setup,added_geometry_context_setup_seconds=probe_setup,scope=plan['scope']),f,indent=2)
if __name__=='__main__':main()

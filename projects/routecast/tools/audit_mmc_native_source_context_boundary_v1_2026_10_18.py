"""Source-only price/criticality observation boundary audit, not a new model."""
import collections,json,math,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';out=E/'mmc_native_source_context_boundary_v1_2026-10-18';out.mkdir(exist_ok=False);bindings=closure([Path(__file__)])
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  d=load(p);assert all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);return d
 sp=E/'mmc_native_source_context_boundary_protocol_v1_2026-10-18/protocol.json';spec=admit(sp);observer=E/'mmc_native_iteration_state_observer_v1_2026-10-10';v=admit(observer/'verification.json');assert v['exit_status']==0 and v['route_bytes_equal_fully_audited_cold'];stateproof=admit(observer/'state_node_audit_v1.json');assert stateproof['all21rounds_full_XML_capacity_and_float32_history_recurrence_pass'];cpp=R/'build/native_iteration_state_observer_v1_2026-10-10/route.cpp';build=admit(cpp.parent/'receipt.json');assert build['bindings'][str(cpp)]==sha(cpp);text=cpp.read_text();start=text.index('RouteIterResults iter_results = netlist_router->route_netlist');reserve=text.index('reserve_locally_used_opins(',start);feasible=text.index('bool routing_is_feasible = feasible_routing();',reserve);update=text.index('pathfinder_update_acc_cost_and_overuse_info(',feasible);dump=text.index('if(const char* directory=std::getenv("ROUTECAST_ITERATION_STATE_DIR"))',update);timing=text.index('timing_info->update();',dump);assert start<reserve<feasible<update<dump<timing;bindings[str(cpp)]=sha(cpp);phase=dict(route_netlist_line=text[:start].count('\n')+1,reservation_line=text[:reserve].count('\n')+1,accumulated_cost_update_line=text[:update].count('\n')+1,snapshot_line=text[:dump].count('\n')+1,STA_update_line=text[:timing].count('\n')+1,snapshot_phase='after route/reservation/accumulated-cost update; before this iteration STA update')
 oldp=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';oldproof=admit(oldp.parent/'independent_xml_verification_v1.json');assert oldproof['all_native_paths_exact'] and oldproof['bindings'][str(oldp)]==sha(oldp);old=load(oldp);ledger={int(n):c for n,c in old['ledger'].items()};state=observer/'states/round_21.tsv';assert sha(state)==v['bindings'][str(state)];bindings[str(state)]=sha(state);nodes={};header=None;hist=collections.Counter();occupied_history=0;mismatch=[];tree_nodes=collections.Counter();seen_pairs=set()
 def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
 with state.open() as stream:
  for line in stream:
   x=line.split()
   if x[0]=='H':assert header is None;header=dict(iteration=int(x[1]),present_factor=float(x[2]),accumulated_factor=float(x[3]))
   elif x[0]=='N':
    n,occ,cap=int(x[1]),int(x[2]),int(x[3]);a=f32(float(x[4]));assert n not in nodes and occ>=0 and cap>0 and math.isfinite(a) and a>=1;nodes[n]=(occ,cap,a);hist[format(a,'.9g')]+=1;occupied_history+=occ>0 and a>1
    if occ!=ledger.get(n,0):mismatch.append(dict(node=n,native=occ,source=ledger.get(n,0)))
   elif x[0]=='T':
    pair=(int(x[1]),int(x[2]));assert pair not in seen_pairs;seen_pairs.add(pair);tree_nodes[pair[1]]+=1
   else:raise ValueError('snapshot tag')
 assert header['iteration']==21 and len(nodes)==904438 and set(nodes)==set(range(904438));assert header['present_factor']==v['iteration_pres_factors']['21'];assert all(tree_nodes[n]==values[0] for n,values in nodes.items());assert not stateproof['rows'][-1]['occupancy_owner_difference_groups'];positive=sum(a>1 for _,_,a in nodes.values());warm=[]
 for case in ['case_01','case_02','case_03']:
  folder=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';w=admit(folder/'verification.json');h=load(folder/'history.json');assert w['zero_initial_history'] and h=={};warm.append(dict(case=case,history_nonzero_entries=0,explicit_zero_initial_history=True))
 manifest=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';assert str(manifest) in v['bindings'] and sha(manifest)==v['bindings'][str(manifest)];bindings[str(manifest)]=sha(manifest);expected={}
 with manifest.open() as stream:
  for line in stream:
   x=line.split()
   if x[0]=='Q':
    cid,net,pin=map(int,x[1:4]);key=(net,pin);assert key not in expected;expected[key]=cid
 assert len(expected)==115572;trace=observer/'criticality.tsv';assert sha(trace)==v['bindings'][str(trace)];bindings[str(trace)]=sha(trace);first={};last={};calls=0;last_iteration=0
 with trace.open() as stream:
  for line in stream:
   x=line.split();assert x[0]=='C';tag,seq,net,pin,index,value,maximum,exponent=x;stamp=next(stream).split();assert stamp[0]=='I' and int(stamp[1])==int(seq)==calls+1;iteration=int(stamp[2]);assert iteration>=last_iteration;last_iteration=iteration;key=(int(net),int(index));assert key in expected;value=f32(float(value));assert math.isfinite(value) and 0<=value<=float(maximum)+1e-7;item=(iteration,value,int(seq));first.setdefault(key,item);last[key]=item;calls+=1
 assert first.keys()==last.keys()==expected.keys() and calls==v['total_calls'];changed=sum(first[k][1]!=last[k][1] for k in expected);last_iters=collections.Counter(last[k][0] for k in expected);perpin=[dict(connection_id=expected[k],native_NET=k[0],native_sink_index=k[1],first_iteration=first[k][0],first_observed_criticality=first[k][1],last_observed_iteration=last[k][0],last_observed_criticality=last[k][1]) for k in sorted(expected)];pp=out/'perpin_observation_boundaries.json';pp.write_text(json.dumps(perpin));bindings[str(pp)]=sha(pp)
 result=dict(status='source_native_context_boundary_diagnostic_computed_independent_verification_pending',bindings=bindings,snapshot_phase=phase,native_snapshot_header=header,RR_nodes=len(nodes),native_history_multiplier_histogram=dict(sorted(hist.items(),key=lambda kv:float(kv[0]))),native_nonunit_history_nodes=positive,native_occupied_nonunit_history_nodes=occupied_history,native_source_occupancy_mismatch_count=len(mismatch),native_source_occupancy_mismatches=mismatch,all_native_snapshot_tree_union_occupancies_equal_N_rows=True,warm_model_history=warm,criticality_calls=calls,physical_connections=len(expected),first_vs_last_observed_criticality_changed=changed,last_observed_iteration_counts=dict(sorted(last_iters.items())),not_observed_in_final_iteration=115572-last_iters[21],all_first_observations_in_iteration1=all(v[0]==1 for v in first.values()),limits='Native accumulated-cost multipliers and pres_fac are recorded in native units, not substituted into the current model. Last observed perpin criticality is not an all-pin final-STA snapshot: values have different observation iterations, and the N/T snapshot precedes that iteration STA update. This diagnostic does not establish that restoring history improves forecasts or make a native-equivalence/state-integration claim. All prior original gates remain unchanged. Source occupancy mismatches, if any, block direct state reuse and remain explicit.')
 assert all(sha(k)==h for k,h in bindings.items());(out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','native_history_multiplier_histogram','native_source_occupancy_mismatches','limits']}),flush=True)
if __name__=='__main__':main()

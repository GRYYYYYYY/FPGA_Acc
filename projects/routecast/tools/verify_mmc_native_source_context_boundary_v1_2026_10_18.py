"""Independent RR integer-history and perpin float-bit observation reconciliation."""
import collections,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_native_source_context_boundary_v1_2026-10-18';rp=root/'results.json';r=json.loads(rp.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};obs=E/'mmc_native_iteration_state_observer_v1_2026-10-10';source=json.loads((E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json').read_text());ledger={int(n):c for n,c in source['ledger'].items()};snapshot=obs/'states/round_21.tsv';multipliers=collections.Counter();node_occ={};node_cap={};tree_owners=collections.defaultdict(set);h=None;occupied_nonunit=0;bad=[]
 with snapshot.open('rb') as f:
  for line in f:
   x=line.rstrip(b'\n').split(b'\t')
   if x[0]==b'H':h=[int(x[1]),float(x[2]),float(x[3])]
   elif x[0]==b'N':
    node,occ,cap=map(int,x[1:4]);value=float(x[4]);assert value.is_integer() and value>=1 and node not in node_occ and cap>0;mult=int(value);node_occ[node]=occ;node_cap[node]=cap;multipliers[str(mult)]+=1;occupied_nonunit+=occ>0 and mult>1
    if occ!=ledger.get(node,0):bad.append(dict(node=node,native=occ,source=ledger.get(node,0)))
   elif x[0]==b'T':tree_owners[int(x[2])].add(int(x[1]))
   else:raise ValueError('unknown snapshot row')
 assert h==[r['native_snapshot_header'][k] for k in ['iteration','present_factor','accumulated_factor']];assert len(node_occ)==r['RR_nodes']==904438 and set(node_occ)==set(range(904438));assert all(node_occ[n]==len(tree_owners[n]) for n in node_occ);assert bad==r['native_source_occupancy_mismatches'] and len(bad)==r['native_source_occupancy_mismatch_count'];assert dict(multipliers)==r['native_history_multiplier_histogram'];assert sum(v for k,v in multipliers.items() if int(k)>1)==r['native_nonunit_history_nodes'] and occupied_nonunit==r['native_occupied_nonunit_history_nodes']
 cpp=R/'build/native_iteration_state_observer_v1_2026-10-10/route.cpp';lines=cpp.read_text().splitlines();positions=r['snapshot_phase'];markers=[('route_netlist_line','netlist_router->route_netlist('),('reservation_line','reserve_locally_used_opins('),('accumulated_cost_update_line','pathfinder_update_acc_cost_and_overuse_info('),('snapshot_line','ROUTECAST_ITERATION_STATE_DIR'),('STA_update_line','timing_info->update();')]
 assert all(token in lines[positions[field]-1] for field,token in markers);assert [positions[field] for field,_ in markers]==sorted(positions[field] for field,_ in markers)
 expected={}
 with (E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries').open('rb') as f:
  for line in f:
   x=line.split()
   if x[0]==b'Q':cid,net,pin=map(int,x[1:4]);assert (net,pin) not in expected;expected[net,pin]=cid
 def bits(raw):return struct.pack('<f',float(raw))
 table=json.loads((root/'perpin_observation_boundaries.json').read_text());assert len(table)==len(expected)==115572;bycid={p['connection_id']:p for p in table};assert len(bycid)==115572;first={};last={};last_seq=0
 with (obs/'criticality.tsv').open('rb') as f:
  while True:
   c=f.readline()
   if not c:break
   i=f.readline();assert i;c=c.rstrip(b'\n').split(b'\t');i=i.rstrip(b'\n').split(b'\t');assert c[0]==b'C' and i[0]==b'I';seq=int(c[1]);assert seq==int(i[1])==last_seq+1;last_seq=seq;key=(int(c[2]),int(c[4]));assert key in expected;entry=(int(i[2]),bits(c[5]));first.setdefault(key,entry);last[key]=entry
 assert first.keys()==last.keys()==expected.keys() and last_seq==r['criticality_calls'];changed=0;iters=collections.Counter()
 for key,cid in expected.items():
  row=bycid[cid];assert row['native_NET']==key[0] and row['native_sink_index']==key[1];assert (row['first_iteration'],bits(row['first_observed_criticality']))==first[key];assert (row['last_observed_iteration'],bits(row['last_observed_criticality']))==last[key];changed+=first[key][1]!=last[key][1];iters[last[key][0]]+=1
 assert changed==r['first_vs_last_observed_criticality_changed'] and {str(k):v for k,v in iters.items()}==r['last_observed_iteration_counts'];assert 115572-iters[21]==r['not_observed_in_final_iteration'] and r['all_first_observations_in_iteration1']==all(v[0]==1 for v in first.values())
 for w in r['warm_model_history']:
  p=E/f"mmc_multiplacement_models_v1_2026-10-18/{w['case']}/native_retained/history.json";assert json.loads(p.read_text())=={} and w['history_nonzero_entries']==0 and w['explicit_zero_initial_history']
 assert all(sha(k)==h for k,h in bindings.items())
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='complete904438RR_history_and_source_occupancy_and115572pin_observation_boundaries_independently_verified',bindings=bindings,all_native_history_counts_and_source_occupancy_mismatches_exact=True,all_snapshot_tree_owner_counts_equal_native_N=True,all115572_first_last_criticalities_and_iterations_float32_bits_equal=True,snapshot_after_route_cost_update_before_STA=True,native_nonunit_history_nodes=r['native_nonunit_history_nodes'],first_last_changed_pins=changed,only3pins_last_observed_in_final_iteration=iters[21]==3,scope='Independent native text token replay and float32 bit checks. Native source price/timing context is not silently admitted as current-model history or final STA. No forecast improvement, native equivalence, five-project integration, heldout or speed claim.'),f,indent=2)
 print('SOURCE_CONTEXT_INDEPENDENT_PASS',r['native_nonunit_history_nodes'],changed,iters[21],flush=True)
if __name__=='__main__':main()

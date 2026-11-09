"""Dense source identity, native snapshot bit parity and post-STA phase admission."""
import collections,json,math,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_dense_post_STA_source_v1_2026-10-18';rp=root/'receipt.json';r=json.loads(rp.read_text());assert r['exit_status']==0 and r['route_bytes_equal_reference'] and r['all_integer_iteration_work_equal_reference'];assert all(sha(k)==h for k,h in {**r['bindings'],**r['files']}.items());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)}
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  v=load(p);assert all(sha(k)==h for k,h in v['bindings'].items());bindings.update(v['bindings']);return v
 def bits(x):return struct.unpack('<I',struct.pack('<f',float(x)))[0]
 def number(b):return struct.unpack('<f',struct.pack('<I',b))[0]
 build=R/'build/dense_post_STA_source_v1_2026-10-18';b=admit(build/'receipt.json');original=(R/'build/native_iteration_state_observer_v1_2026-10-10/route.cpp').read_text();patched=(build/'route.cpp').read_text();hook=(R/'tools/native_search_seed/dense_post_STA_capture_v1.inc').read_text();assert patched.replace('#include "route_net.h"\n','',1).replace('\n'+hook,'',1)==original;assert patched.index('        timing_info->update();')<patched.index('        pin_timing_invalidator->reset();')<patched.index('// ROUTECAST_DENSE_POST_STA_CAPTURE_BEGIN');assert 'if (routing_is_feasible)' in hook
 obs=E/'mmc_native_iteration_state_observer_v1_2026-10-10';sv=admit(obs/'verification.json');stateproof=admit(obs/'state_node_audit_v1.json');edgeproof=admit(obs/'tree_edge_audit_v1.json');delayproof=admit(obs/'tree_delay_audit_v1.json');assert sv['route_bytes_equal_fully_audited_cold'] and stateproof['all21rounds_full_XML_capacity_and_float32_history_recurrence_pass'] and edgeproof['all21rounds_rooted_acyclic_parent_structure_and_original_XML_edge_switch_membership_pass'] and delayproof['all21rounds_tree_delay_float32_recurrence_pass'];assert [x['iteration'] for x in stateproof['rows'] if x['overflow_units']==0]==[21]
 oldnodes={};oldtrees={}
 with (obs/'states/round_21.tsv').open() as f:
  for line in f:
   x=line.split()
   if x[0]=='N':oldnodes[int(x[1])]=(int(x[2]),int(x[3]),bits(x[4]))
   elif x[0]=='T':key=(int(x[1]),int(x[2]));assert key not in oldtrees;oldtrees[key]=(int(x[3]),int(x[4]),bits(x[5]))
 initial_dir=E/'mmc_native_initial_criticality_snapshot_v2_2026-10-10';initialproof=admit(initial_dir/'verification.json');initialpath=initial_dir/'initial_connection_criticalities.json';assert initialproof['bindings'][str(initialpath)]==sha(initialpath);initial={x['connection_id']:x for x in load(initialpath)};priorroot=E/'mmc_native_source_context_boundary_v1_2026-10-18';prior=admit(priorroot/'independent_verification_v1.json');observations={x['connection_id']:x for x in load(priorroot/'perpin_observation_boundaries.json')};manifest=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';expected={}
 with manifest.open() as f:
  for line in f:
   x=line.split()
   if x[0]=='Q':expected[int(x[1])]=tuple(map(int,x[2:6]))
 assert len(expected)==len(initial)==len(observations)==115572;header=None;footer=None;nodes={};trees={};pins={};counts=collections.Counter()
 with (root/'context.tsv').open('rb') as f:
  for line in f:
   x=line.rstrip(b'\n').split(b'\t');tag=x[0];counts[tag.decode()]+=1
   if tag==b'H':assert header is None;header=(int(x[1]),float(x[2]),float(x[3]),float(x[4]))
   elif tag==b'N':
    node,occ,cap,raw=map(int,x[1:5]);assert raw==bits(x[5]) and node not in nodes;nodes[node]=(occ,cap,raw)
   elif tag==b'T':
    net,node,parent,switch,raw=map(int,x[1:6]);assert raw==bits(x[6]) and (net,node) not in trees;trees[net,node]=(parent,switch,raw)
   elif tag==b'C':
    cid,net,index,pin,source,sink,raw=map(int,x[1:8]);assert raw==bits(x[8]) and cid not in pins and (net,index,source,sink)==expected[cid];ref=initial[cid];assert (index,pin,source,sink)==(ref['local_sink_pin'],ref['global_pin'],ref['source_rr'],ref['target_rr']);value=number(raw);assert math.isfinite(value) and 0<=value<=header[2]+1e-7;pins[cid]=dict(connection_id=cid,native_NET=net,local_sink_pin=index,global_pin=pin,source_rr=source,target_rr=sink,criticality_float32_bits=raw,criticality=value,criticality_float32_text=x[8].decode())
   elif tag==b'F':assert footer is None;footer=tuple(map(int,x[1:4]))
   else:raise ValueError('dense source tag')
 assert header[0]==21 and header[1]==sv['iteration_pres_factors']['21'];assert header[2]==float(initial[0]['maximum_text']) and header[3]==float(initial[0]['exponent_text']);assert nodes==oldnodes and trees==oldtrees and set(pins)==set(expected);assert footer==(len(nodes),len(trees),len(pins))==(904438,counts['T'],115572);assert counts['H']==counts['F']==1
 sourceproof=admit(E/'mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json');source=load(E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json');assert sourceproof['all_native_paths_exact'];ledger={int(n):v for n,v in source['ledger'].items()};assert all(value[0]==ledger.get(n,0)<=value[1] for n,value in nodes.items());mapping={};members=collections.defaultdict(set)
 for row in source['records']:
  net=pins[row['connection_id']]['native_NET'];assert mapping.setdefault(net,row['net_id'])==row['net_id'];assert (pins[row['connection_id']]['source_rr'],pins[row['connection_id']]['target_rr'])==(row['source'],row['sink']);members[net].add(row['connection_id'])
 assert len(mapping)==55300 and {net for net,node in trees}==set(mapping);tree_occupancy=collections.Counter(node for net,node in trees);assert all(tree_occupancy[n]==value[0] for n,value in nodes.items())
 # Final native route file is exact reference bytes; verify equality and wire/CPD too.
 old=E/'ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/native/mmc';assert (root/'output.route').read_bytes()==(old/'output.route').read_bytes();import re
 for pattern in [r'Total wirelength:\s*(\d+)',r'Final critical path delay \(least slack\):\s*([0-9.]+)']:
  a=re.findall(pattern,(old/'native.log').read_text());z=re.findall(pattern,(root/'native.log').read_text());assert a and a[-1]==z[-1]
 first_diff=sum(pins[c]['criticality_float32_bits']!=bits(observations[c]['first_observed_criticality']) for c in pins);last_diff=sum(pins[c]['criticality_float32_bits']!=bits(observations[c]['last_observed_criticality']) for c in pins);path=root/'dense_physical_criticalities.json';path.open('x').write(json.dumps([pins[c] for c in sorted(pins)]));bindings[str(path)]=sha(path);assert all(sha(k)==h for k,h in bindings.items())
 result=dict(status='dense_source_post_STA_phase_all115572physical_pins_RR_history_tree_bits_and_native_parity_verified',bindings=bindings,physical_connections=len(pins),NETs=len(mapping),RR_nodes=len(nodes),tree_records=len(trees),source_iteration=21,post_STA_criticality_different_from_first_observation=first_diff,post_STA_criticality_different_from_sparse_last_observation=last_diff,native_source_route_and_every_integer_iteration_work_equal=True,native_wire_and_printed_diagnostic_CPD_equal=True,all904438_RR_occupancy_capacity_accumulated_cost_bits_equal_before_STA_snapshot=True,all_tree_parent_switch_delay_bits_equal_before_STA_snapshot=True,all_physical_pin_global_NET_local_identity_and_RR_endpoints_equal=True,native_price_present_factor=header[1],native_maximum_criticality=header[2],native_criticality_exponent=header[3],source_original_canonical_reload_gate=False,source_original_zero_counter_gate=False,scope='Dense actual native get_net_pin_criticality returns after feasible source routing STA update; required physical manifest only, excluding ignored pins. Independent identity/bit/phase/route/work validation, not independent numerical STA recomputation, asynchronous STA, native-equivalent estimator, five-project integration, changed original gates or forecast/speed gain.')
 (root/'verification_v1.json').open('x').write(json.dumps(result,indent=2));print('DENSE_POST_STA_VERIFIED',len(pins),first_diff,last_diff,len(trees),flush=True)
if __name__=='__main__':main()

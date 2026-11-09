"""Freeze one MMC development move from authenticated prior physical state."""
import json,sys,itertools,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from pre_route_endpoints import sha,physical_maps,placements
D=R/'experiments/mmc_native_state_geometry_v1_2026-10-18';D.mkdir(exist_ok=False);start=time.perf_counter();epfile=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';ep=json.loads(epfile.read_text());src=Path(ep['inputs']['net']['path']).parent;graph=Path(ep['inputs']['graph']['path']);mappingfile=src/'mapping.json';prior=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold';nr=prior/'native/mmc/receipt.json';np=prior/'native/mmc/verification.json';cp=prior/'canonical/receipt.json';ip=prior/'canonical/ignored_pin_verification_v1.json';crit=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10/verification.json';base=R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10/verification.json';route=prior/'native/mmc/output.route'
files=[Path(__file__),epfile,mappingfile,nr,np,cp,ip,crit,base,route];bindings={str(p):sha(p) for p in files}
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256'];bindings[spec['path']]=spec['sha256']
native=json.loads(nr.read_text());physical=json.loads(np.read_text());canonical=json.loads(cp.read_text())['rows'][0]['canonical'];ignored=json.loads(ip.read_text())['rows'][0];assert physical['physical_connections']==len(ep['connections'])==115572 and physical['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and physical['original_native_FULL_check_pass'] and physical['overflow_units']==0;assert canonical['semantic_consistency_gate_pass'] and canonical['all_NET_physical_node_type_switch_sequences_identical'] and canonical['packed_netlist_byte_identical'];assert ignored['every_mismatch_matches_native_ignored_sink_pin'];assert canonical['fixups']==330 and not canonical['original_zero_counter_gate_pass'];assert native['files'][str(route)]==sha(route)
for name in ['net','place']:
 original=Path(ep['inputs'][name]['path']);nativefile=prior/'native/mmc'/('design.'+('net' if name=='net' else 'place'));assert sha(original)==sha(nativefile)
assert sha(graph)==native['bindings'][native['command'][native['command'].index('--read_rr_graph')+1]]
cv=json.loads(crit.read_text());assert cv['nonignored_pin_keys_exactly_manifest'] and cv['routed_connections']==115572;assert cv['bindings'][str(epfile)]==sha(epfile)
bv=json.loads(base.read_text());assert bv['all_original_node_ids_types_segments_and_native_group_counts_pass'];assert len(ep['connections'])==115572
with (D/'selection_rule.json').open('x') as f:json.dump(dict(bindings=bindings,selection='First pair in ascending original block-ID combination order of same rooted unit CLB type/subtile/layer, nonempty physical-demand NET touch set, and nonpositive total physical-demand HPWL delta. No native target/model outputs read; one pair only, no replacement after outcomes.',scope='Exposed MMC development design. Historical cold observation and input readiness select design; not strict heldout or timing benefit.'),f,indent=2);f.write('\n')
context=physical_maps(graph);types,grid,_=context;pos=placements(src/'design.place',sha(src/'design.net'));mapping=json.loads(mappingfile.read_text());included={q['net_id'] for q in ep['connections']};nets=defaultdict(set);touches=defaultdict(set)
for pin in mapping['pin_details']:
 if pin['net_id'] in included:nets[pin['net_id']].add(pin['block']);touches[pin['block']].add(pin['net_id'])
def hpwl(p,ids):return sum(max(p[n][0] for n in nets[k])-min(p[n][0] for n in nets[k])+max(p[n][1] for n in nets[k])-min(p[n][1] for n in nets[k]) for k in ids)
blocks=[]
for name,p in sorted(pos.items(),key=lambda item:item[1][4]):
 x,y,z,layer,bid=p;tid,wo,ho=grid[x,y,layer]
 if types[tid]['name']=='clb' and (wo,ho)==(0,0) and (types[tid]['width'],types[tid]['height'])==(1,1):blocks.append((name,(tid,z,layer)))
selected=None;examined=0
for (a,ac),(b,bc) in itertools.combinations(blocks,2):
 if ac!=bc:continue
 dirty=touches[a]|touches[b]
 if not dirty:continue
 examined+=1;changed={**pos,a:(*pos[b][:4],pos[a][4]),b:(*pos[a][:4],pos[b][4])};delta=hpwl(changed,dirty)-hpwl(pos,dirty)
 if delta<=0:
  selected=dict(pair=[a,b],block_ids=[pos[a][4],pos[b][4]],before_positions={a:pos[a],b:pos[b]},after_positions={a:changed[a],b:changed[b]},hpwl_delta=delta,touched_physical_nets=sorted(dirty));break
assert selected is not None
assert all(sha(p)==h for p,h in bindings.items())
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,previous_endpoint=str(epfile),previous_native_route=str(route),native_initial_criticality_directory=str(crit.parent),nodebase_proof=str(base),selection_rule_sha256=sha(D/'selection_rule.json'),selected=selected,compatible_pairs_examined=examined,previous_native_seconds=native['native_process_seconds'],prior_canonical_semantic_pass=True,original_zero_counter_canonical_gate=False,ignored_pin_fixups=330,native_target_outputs_generated=False,preparation_seconds=time.perf_counter()-start,scope='Geometry selection and old state identity readiness only. No placement consistency run, new endpoints, full bootstrap or target QoR. No hidden amortization or new timing claim.'),f,indent=2);f.write('\n')
print('MMC GEOMETRY',selected['pair'],'HPWL',delta,'touched NETs',len(selected['touched_physical_nets']),'examined',examined,flush=True)

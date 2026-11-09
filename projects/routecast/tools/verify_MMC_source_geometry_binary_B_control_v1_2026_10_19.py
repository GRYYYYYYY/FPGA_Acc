"""Exact source-geometry cross-binary input/route/work and native-canonical comparison."""
import pathlib,json,hashlib
from audit_mmc_v16_native_iteration_work_v1 import parse
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_source_geometry_binary_B_control_v1_2026-10-19';pp=O/'protocol.json';rp=O/'receipt.json';p=json.loads(pp.read_text());r=json.loads(rp.read_text());assert r['status']=='SAME_SOURCE_GEOMETRY_BINARY_B_FULL_PHYSICAL_CANONICAL_PASS';A=pathlib.Path(p['reference_A_directory']);B=O/'native';assert p['reference_A_command'][1:]==p['B_command'][1:] and sha(pathlib.Path(p['reference_A_command'][0]))!=sha(pathlib.Path(p['B_command'][0]))
 for doc in [p,r]:
  for f,h in doc['bindings'].items():assert sha(pathlib.Path(f))==h
 for f,h in r['canonical']['files'].items():assert sha(pathlib.Path(f))==h
 for name in ['design.blif','design.net','design.place']:assert (A/name).read_bytes()==(B/name).read_bytes()
 route_same=(A/'output.route').read_bytes()==(B/'output.route').read_bytes();post_same=(A/'design.net.post_routing').read_bytes()==(B/'design.net.post_routing').read_bytes();assert route_same==r['native']['route_bytes_equal_A'];assert r['native']['FULL_pass'] and r['native']['VPR_success'] and r['canonical']['semantic_consistency_gate_pass'];physical=json.loads((B/'physical_audit.json').read_text());assert physical['overflow_units']==0 and physical['routed_nets']==55300 and len(physical['connections'])==115572;assert physical['inputs_sha256']['graph']==sha(pathlib.Path(p['B_command'][p['B_command'].index('--read_rr_graph')+1])) and physical['inputs_sha256']['route']==sha(B/'output.route')
 fields=['iteration','present_factor_text','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes'];a,b=[parse((x/'native.log').read_text()) for x in [A,B]];work_same=a['iterations']==b['iterations'] and [{k:x[k] for k in fields} for x in a['rows']]==[{k:x[k] for k in fields} for x in b['rows']]
 proof=R/'experiments/mmc_same_binary_cold_repeat_v1_2026-10-18/independent_verification_v2.json';v=json.loads(proof.read_text());assert v['all4_same_route_and_work'];sv=next(x for x in v['cases'] if x['layout']=='source');assert sv['route_bytes_equal'] and sv['all_integer_iteration_work_and_present_factors_equal'];assert v['bindings'][str(A/'output.route')]==sha(A/'output.route')
 bindings={str(f):sha(f) for f in [pp,rp,proof,B/'physical_audit.json',A/'output.route',B/'output.route',A/'native.log',B/'native.log',A/'design.net.post_routing',B/'design.net.post_routing',pathlib.Path(__file__).resolve(),R/'tools/audit_mmc_v16_native_iteration_work_v1.py']}
 result=dict(status='SOURCE_GEOMETRY_CROSS_BINARY_CONTROL_NATIVE_PHYSICAL_CANONICAL_VERIFIED',bindings=bindings,source_A_B_route_bytes_equal=route_same,source_A_B_postroute_packed_bytes_equal=post_same,source_A_B_all_integer_work_and_present_factors_equal=work_same,source_A_observed_same_binary_repeat_equal=True,connections=115572,NETs=55300,B_CPD_ns=r['native']['CPD_ns'],B_wirelength=r['native']['wirelength'],B_canonical_ignored_fixups=r['canonical']['fixups'],original_zero_counter_gate_pass=r['canonical']['original_zero_counter_gate_pass'],scope='One fixed source-geometry cross-binary observation. No source-route change observed if equality fields true; does not prove binary equivalence on all layouts, universal determinism or pure causal placement attribution. Original labels, failed predictor gates, exposed-data status and total-cost requirements unchanged.')
 (O/'independent_verification_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','scope']},flush=True)
if __name__=='__main__':main()

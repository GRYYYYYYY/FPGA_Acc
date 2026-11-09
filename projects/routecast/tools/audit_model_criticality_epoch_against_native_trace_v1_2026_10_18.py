"""Direct bit comparison of actual fixed model input and native source observations."""
import json,struct,sys
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_native_source_context_boundary_v1_2026-10-18';vp=root/'independent_verification_v1.json';v=json.loads(vp.read_text());assert v['all115572_first_last_criticalities_and_iterations_float32_bits_equal'];assert all(sha(k)==h for k,h in v['bindings'].items());bindings={**v['bindings'],**closure([Path(__file__)]),str(vp):sha(vp)};p=root/'perpin_observation_boundaries.json';native={x['connection_id']:x for x in json.loads(p.read_text())};rows=[]
 def bits(v):return struct.pack('<f',v)
 for case in ['case_01','case_02','case_03']:
  folder=E/f'mmc_multiplacement_feedback_inputs_v1_2026-10-18/{case}/timing';proof=folder/'verification.json';cert=json.loads(proof.read_text());assert cert['all_native_pin_identities_preserved'] and cert['all_values_equal_before_timing_epoch'];assert all(sha(k)==h for k,h in cert['bindings'].items());bindings.update(cert['bindings']);bindings[str(proof)]=sha(proof);data=folder/'remapped_criticalities.json';assert sha(data)==cert['bindings'][str(data)];values=json.loads(data.read_text());assert len(values)==len(native)==115572 and {r['connection_id'] for r in values}==native.keys();first=last=0;different=[]
  for r in values:
   cid=r['connection_id'];actual=float(Fraction(r['criticality_numerator'],r['criticality_denominator']));assert bits(actual)==bits(r['criticality'])==bits(float(r['criticality_float32_text']));n=native[cid];assert r['local_sink_pin']==n['native_sink_index'];same_first=bits(actual)==bits(n['first_observed_criticality']);same_last=bits(actual)==bits(n['last_observed_criticality']);first+=same_first;last+=same_last
   if not same_first:different.append(cid)
  rows.append(dict(case=case,connections=len(values),model_equal_first_native_observed_float32=first,model_equal_last_native_observed_float32=last,model_not_equal_first_native_observation_CIDs=different,source_epoch=cert['timing_epoch_sha256']))
 assert all(sha(k)==h for k,h in bindings.items());out=root/'model_criticality_epoch_comparison_v1.json'
 with out.open('x') as f:json.dump(dict(status='actual_model_criticality_input_bits_compared_to_verified_native_source_first_last_observations',bindings=bindings,cases=rows,scope='Comparisons use actual model rational value and its float32 bit pattern and retained physical local-sink identity. Last observed is sparse heterogeneous native iteration context, not final all-pin STA. No model mutation, native policy trial, original gate change or improvement claim.'),f,indent=2)
 print(json.dumps(rows),flush=True)
if __name__=='__main__':main()

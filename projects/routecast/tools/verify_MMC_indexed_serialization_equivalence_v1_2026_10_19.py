"""Byte-for-byte real model serializer equivalence, with immutable input bindings."""
import pathlib,json,hashlib,sys
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 case=sys.argv[1];assert case in ['episode_01','episode_02','episode_03'];O=R/'experiments/mmc_indexed_serialization_equivalence_v1_2026-10-19'/case;rp=O/'receipt.json';r=json.loads(rp.read_text())
 for p,h in r['bindings'].items():assert sha(pathlib.Path(p))==h
 baseline=pathlib.Path(r['baseline_route']);sp=baseline.parent/'serialization.json';s=json.loads(sp.read_text());assert s['source_model_sha256']==r['bindings'][s['source_model']]
 assert s['endpoint_sha256']==r['bindings'][str(R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json')]
 assert s['identity_sha256']==r['bindings'][s['identity']]
 assert sha(baseline)==s['input_files'][str(baseline)]==r['route_sha256']==sha(O/'design.route')
 assert baseline.read_bytes()==(O/'design.route').read_bytes() and s['bound_sinks']==r['connections']==115572
 for p,h in s['input_files'].items():assert sha(pathlib.Path(p))==h
 result=dict(status='ALL115572_CONNECTIONS_SERIALIZED_TO_EXACT_BASELINE_BYTES',case=case,route_sha256=r['route_sha256'],bound_sinks=115572,original_serialization_seconds=s['serialization_seconds'],indexed_serialization_seconds=r['serialization_seconds'],bindings={str(p):sha(p) for p in [rp,sp,baseline,O/'design.route',pathlib.Path(__file__).resolve()]},scope='One exposed full cohort and identical inputs, exact byte equality. Sequential unpaired component timings only, no stable speedup or end-to-end claim. Duplicate sites remain list-valued and ambiguous rather than silently collapsed. Existing native job retains original serializer.')
 (O/'independent_equivalence_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','scope']},flush=True)
if __name__=='__main__':main()

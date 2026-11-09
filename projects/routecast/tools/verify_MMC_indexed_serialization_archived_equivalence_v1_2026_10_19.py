"""Exact archived-original versus new indexed full model, including input equality."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 N=R/'experiments/mmc_indexed_serialization_equivalence_v1_2026-10-19/episode_01';B=R/'experiments/mmc_reference_incremental_native_v1_2026-10-19/episode_01';rp=N/'receipt.json';sp=B/'serialization.json';r=json.loads(rp.read_text());s=json.loads(sp.read_text());protocol=B.parent/'protocol.json';pp=json.loads(protocol.read_text())
 for p,h in r['bindings'].items():assert sha(pathlib.Path(p))==h
 original=R/'tools/native_resume_prototype/serialize_shared_inventory.py';assert pp['bindings'][str(original)]==sha(original)
 for p,h in s['input_files'].items():assert sha(pathlib.Path(p))==h
 oldmodel=pathlib.Path(s['source_model']);assert sha(oldmodel)==s['source_model_sha256']==pp['bindings'][str(oldmodel)]
 newmodel=R/'experiments/mmc_reference_budget_incremental_astar_v2_2026-10-19/episode_01/model.json';a=json.loads(oldmodel.read_text());b=json.loads(newmodel.read_text());aa={q['connection_id']:q for q in a['records']};bb={q['connection_id']:q for q in b['records']};assert aa==bb and len(aa)==len(a['records'])==len(b['records'])==115572
 ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';assert sha(ep)==s['endpoint_sha256']==pp['bindings'][str(ep)]
 identity=pathlib.Path(s['identity']);assert sha(identity)==s['identity_sha256']==r['bindings'][str(identity)]
 place=R/'experiments/mmc_reference_incremental_astar_native_v2_2026-10-19/episode_01/design.place';assert (B/'design.place').read_bytes()==place.read_bytes()
 meta=json.loads(ep.read_text());assert meta['graph_sha256']==s['graph_sha256']==r['bindings'][meta['inputs']['graph']['path']]
 assert (B/'design.route').read_bytes()==(N/'design.route').read_bytes() and sha(B/'design.route')==r['route_sha256'] and r['connections']==s['bound_sinks']==115572
 paths=[rp,sp,protocol,oldmodel,newmodel,ep,identity,place,B/'design.place',B/'design.route',N/'design.route',original,pathlib.Path(__file__).resolve()]
 result=dict(status='ALL115572_RECORDS_AND_SERIALIZER_INPUTS_IDENTICAL_EXACT_ARCHIVED_ORIGINAL_ROUTE_BYTES',case='episode_01',connections=115572,route_sha256=r['route_sha256'],indexed_serialization_seconds=r['serialization_seconds'],bindings={str(p):sha(p) for p in paths},scope='Known full episode01. Exact identity/endpoint/graph/placement and model record equality, exact original serializer route bytes; no native gate or other case implied. Archived original lacks serializer component clock, so no measured speedup ratio. Current original native run remains unchanged.')
 (N/'archived_original_equivalence_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],flush=True)
if __name__=='__main__':main()

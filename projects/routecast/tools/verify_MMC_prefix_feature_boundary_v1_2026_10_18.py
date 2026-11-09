"""Read only the recorded source prefix, then reject future-bearing input schemas."""
import pathlib,json,hashlib,sys,copy
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pressure_prefix_feature_contract_v1 import load,validate
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 root=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';cert=root/'verification.json';v=json.loads(cert.read_text());assert v['status']=='all6_strict_temporal_splits_and_exact_pressure_decompositions_pass';bindings={str(cert):sha(cert),str(pathlib.Path(__file__).resolve()):sha(__file__),str(R/'tools/pressure_prefix_feature_contract_v1.py'):sha(R/'tools/pressure_prefix_feature_contract_v1.py')};count=rejects=0
 for row in v['cases']:
  case,policy=row['case'],row['policy'];p=root/f'{case}_{policy}/features.json';feature=load(p,row['feature_sha256']);bindings[str(p)]=sha(p);trace=R/f'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18/{case}/{policy}/owner_trace.tsv'
  with trace.open('rb') as f:prefix=f.read(row['first_checkpoint_end_byte'])
  assert prefix.rstrip().endswith(b'CE');observed={};active=False;ends=0
  for line in prefix.splitlines():
   words=line.split()
   if words[:1]==[b'CP']:
    assert int(words[2])<=1;active=words[1:]==[b'iteration_end_after_local_opins',b'1']
   elif active and words[:1]==[b'V']:
    n,occupancy,capacity=map(int,words[1:]);assert n not in observed;observed[n]=occupancy-capacity
   elif active and words==[b'CE']:ends+=1;active=False
  assert ends==1 and feature==observed;payload=json.loads(p.read_text())
  bads=[]
  for field in ['future_sum_overflow_units','last_target_iteration','targets']:
   bad=copy.deepcopy(payload);bad[field]=0;bads.append(bad)
  bad=copy.deepcopy(payload);bad['cutoff_iteration']=True;bads.append(bad)
  bad=copy.deepcopy(payload);bad['overflow_units_by_rr']['00']=1;bads.append(bad)
  bads.append(json.loads((root/f'{case}_{policy}/targets.json').read_text()))
  for bad in bads:
   try:validate(bad)
   except ValueError:rejects+=1
   else:raise AssertionError('future or malformed feature accepted')
  try:load(p,'0'*64)
  except ValueError:rejects+=1
  else:raise AssertionError('digest mismatch accepted')
  count+=1
 result=dict(status='all6_feature_maps_match_exact_source_prefix_and_future_inputs_rejected',bindings=bindings,source_prefixes_verified=count,invalid_or_future_input_rejections=rejects,scope='Strict iteration1 feature schema and prefix provenance only. Existing traces are exposed partial-seed policy data; future targets remain labels. No predictor trained, revised cold gate, heldout or performance claim.',accepted_gain=False)
 (root/'feature_boundary_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n');print(count,rejects,flush=True)
if __name__=='__main__':main()

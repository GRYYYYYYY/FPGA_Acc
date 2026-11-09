"""Observed native criticality changes; sparse calls do not imply full STA coverage."""
import json, struct, hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
O=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 proof=O/'verification.json'; v=json.loads(proof.read_text())
 assert v['exit_status']==0 and v['route_bytes_equal_fully_audited_cold']
 manifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries'
 trace=O/'criticality.tsv'
 for p in [manifest,trace]: assert sha(p)==v['bindings'][str(p)]
 keys=set()
 for line in manifest.read_text().splitlines():
  f=line.split()
  if f[0]=='Q':keys.add((int(f[2]),int(f[3])))
 assert len(keys)==115572
 previous={}; first={}; rows={}; pending=None; calls=0; extras=0
 with trace.open() as stream:
  for line in stream:
   f=line.split()
   if f[0]=='C':
    assert pending is None and len(f)==8
    pending=(int(f[1]),(int(f[2]),int(f[4])),struct.pack('!f',float(f[5])))
   elif f[0]=='I':
    assert pending is not None and int(f[1])==pending[0]
    seq,key,bits=pending; pending=None; calls+=1
    if key not in keys:extras+=1;continue
    iteration=int(f[2]); row=rows.setdefault(iteration,{'counts':Counter(),'observed':set()})
    row['observed'].add(key); row['counts']['calls']+=1
    if key in previous: row['counts']['changed_from_previous_observation' if previous[key]!=bits else 'unchanged_from_previous_observation']+=1
    else:row['counts']['first_observation']+=1
    first.setdefault(key,bits)
    row['counts']['different_from_first_observation' if first[key]!=bits else 'equal_to_first_observation']+=1
    previous[key]=bits
 assert pending is None
 output=[]
 for iteration,row in sorted(rows.items()):
  output.append(dict(iteration=iteration,observed_manifest_pins=len(row['observed']),unobserved_manifest_pins=len(keys-row['observed']),counts=dict(row['counts'])))
 bindings={str(p):sha(p) for p in [manifest,trace,proof,Path(__file__).resolve()]}
 result=dict(bindings=bindings,total_native_calls=calls,extra_calls=extras,ever_observed_manifest_pins=len(previous),rows=output,scope='Float32 bit equality for actual recorded calls only; first observation is not necessarily initialized criticality. Sparse observations do not certify current full STA state, causal quality effect or native search equivalence.')
 out=O/'criticality_change_diagnosis_v1.json'; assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(calls=calls,extra_calls=extras,ever_observed=len(previous),rows=output)))
if __name__=='__main__':main()

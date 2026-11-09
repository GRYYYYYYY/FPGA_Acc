"""Authenticate exact producer input against prior actual committed state."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_persistent_chain_v1_2026-10-09';mp=R/'tools/paired_persistent_chain_manifest_v1.json';m=json.loads(mp.read_text());rows=[];bindings={str(mp):sha(mp),str(Path(__file__).resolve()):sha(Path(__file__))}
for arm in m['plans']:
 if arm['mode']!='online':continue
 for entry in arm['steps']:
  step=entry['step'];sp=E/entry['selection'];ip=sp.parent/'prior_committed_input.json';inp=json.loads(ip.read_text());assert inp['epoch']==step-1
  if step==1:
   prior=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_0_state.json';expected=json.loads(prior.read_text())['state']
  else:
   prior=D/f"arm_{arm['arm']}_step_{step-1}_committed.json";doc=json.loads(prior.read_text());assert doc['epoch']==step-1;expected=doc['paths']
  assert inp['paths']==expected and len(expected)==516
  receipt=sp.parent/'verification.json';v=json.loads(receipt.read_text());assert v['bindings'][str(ip)]==sha(ip)
  for name,digest in v['bindings'].items():assert sha(name)==digest
  for p in (prior,ip,receipt):bindings[str(p)]=sha(p)
  rows.append(dict(arm=arm['arm'],step=step,input_epoch=step-1,connections=516))
out=D/'independent_input_lineage.json';assert not out.exists();out.write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All six online producer input snapshots equal immediately prior actual committed state, or given initial state. Source bindings authenticate actual driver execution.'),indent=2)+'\n');print(rows,flush=True)

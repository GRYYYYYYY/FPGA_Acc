"""Independent actual-prior-commit path lineage for both online arms."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'paired_history_chain_v1_2026-10-09'
manifest=R/'tools/paired_history_chain_manifest_v1.json';m=json.loads(manifest.read_text());bindings={str(manifest):sha(manifest),str(Path(__file__).resolve()):sha(Path(__file__))};rows=[]
for arm in m['plans']:
 if arm['mode']!='online':continue
 for entry in arm['steps'][1:]:
  step=entry['step'];prior=arm['steps'][step-2]
  committed=D/f"arm_{arm['arm']}_step_{step-1}_committed.json";old=json.loads(committed.read_text())['paths']
  selection=E/prior['selection'];assert old==json.loads(selection.read_text())['paths']
  prefix=f"paired_history_chain_v1_arm{arm['arm']}_step{step}"
  bankpath=E/f'{prefix}_stage_1_2026-10-09/result.json';bank=json.loads(bankpath.read_text())['bank'];count=0
  for cid,opts in bank.items():
   for option in opts:
    if option['origin']=='ELIGIBLE_ACTUAL_OLD_ROUTE':assert option['path']==old[cid];count+=1
  for index in (0,1,2):
   receipt=E/f'{prefix}_stage_{index}_2026-10-09/verification.json';doc=json.loads(receipt.read_text())
   assert doc['bindings'][str(selection)]==sha(selection)
   for name,digest in doc['bindings'].items():assert sha(name)==digest
   bindings[str(receipt)]=sha(receipt)
  for p in (committed,selection,bankpath):bindings[str(p)]=sha(p)
  rows.append(dict(arm=arm['arm'],step=step,eligible_old_candidates_equal_prior_commit=count))
assert len(rows)==4
out=D/'independent_lineage_verification.json';assert not out.exists();out.write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All actual eligible old options match immediately prior committed state and production bindings authenticate prior selection.'),indent=2)+'\n');print(rows,flush=True)

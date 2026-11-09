"""Inventory all logged simple-proof attempts and reset contract failure, no waiver."""
import json,re,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
E=R/'experiments/blob_merge_archived_json_equivalence_v1_2026-10-10';B=R/'experiments/blob_merge_reset_alignment_sat_v1_2026-10-10';bindings={str(Path(__file__)):sha(Path(__file__))}
for D in [E,B]:
 p=D/'receipt.json';r=json.loads(p.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings.update(r['bindings']);bindings[str(p)]=sha(p)
text=(E/'equivalence.log').read_text();m=re.search(r'Found (\d+) unproven \$equiv cells',text);assert m;total=int(m[1]);attempts=[]
for line in text.splitlines():
 m=re.match(r'^\s*Trying to prove \$equiv for (.+): (success!|failed\.)$',line)
 if m:attempts.append(dict(point=m[1],simple_proved=m[2]=='success!'))
assert len(attempts)==total==1715 and len({a['point'] for a in attempts})==total
assert sum(a['simple_proved'] for a in attempts)==995
failed=Counter(re.sub(r' \[\d+\]$','',a['point']) for a in attempts if not a['simple_proved']);source=R/'experiments/blob_merge_frontend_readiness_v1_2026-10-10/design.v';bindings[str(source)]=sha(source)
# Exact source regions archive the state-only reset and retained request behavior.
lines=source.read_text().splitlines();regions=[dict(first_line=a,last_line=b,text='\n'.join(lines[a-1:b])) for a,b in [(254,264),(350,372)]]
assert 'oReadFifoRequest <= `TRUE;' in regions[1]['text'] and 'oReadFifoRequest <= `FALSE;' in '\n'.join(lines[370:374])
assert all(sha(k)==h for k,h in bindings.items());D=R/'experiments/blob_merge_functional_admission_diagnosis_v1_2026-10-10';D.mkdir()
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,all_logged_simple_attempts=attempts,found_equiv_cells=total,simple_proved=995,simple_unproven=720,unproven_groups=dict(failed),source_regions=regions,native_label_admitted=False,scope='Complete logged simple proof inventory; failed simple obligations mean unproven, not counterexamples. Whole induction timed out. Reset-output equality from independent arbitrary states separately fails. Original state-only reset retains request until IDLE nonempty/READ_FIFO; unrelated initial request states need not synchronize just from reset. Not modified HDL, waived initialization, proved equivalence or family admission.'),indent=2)+'\n');print('Simple proof inventory',total,995,720,len(failed))

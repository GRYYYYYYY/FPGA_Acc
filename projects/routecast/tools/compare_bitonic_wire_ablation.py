"""Retrospective all-case native canonical ablation, retaining incomplete outcome."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_wire_ablation_comparison_2026-10-07';out.mkdir();bindings={};rows=[]
def read(file):bindings[str(file)]=sha(file);return json.loads(file.read_text())
for model,pred,native,prefix in [('50ps','bitonic_owned_four_repair_prediction_2026-10-07','bitonic_four_repair_native_import_2026-10-07','bitonic_four_repair'),('0ps','bitonic_owned_four_repair_zero_wire_2026-10-07','bitonic_zero_wire_native_import_2026-10-07','bitonic_zero_wire')]:
 base=ROOT/'experiments'/pred;pr=read(base/'receipt.json');pv=read(base/'verification.json');assert pv['receipt_sha256']==sha(base/'receipt.json');pp=read(base/'protocol.json');assert pr['protocol_sha256']==sha(base/'protocol.json') and all(sha(f)==h for f,h in pp['sources'].items());nr=read(ROOT/'experiments'/native/'receipt.json');nv=read(ROOT/'experiments'/native/'verification.json');assert nv['receipt_sha256']==sha(ROOT/'experiments'/native/'receipt.json');assert [x['count'] for x in pr['rows']]==[4,8,16]
 for row,result,metrics in zip(pr['rows'],nr['rows'],nv['rows']):
  n=row['count'];assert result['count']==metrics['count']==n;item=dict(model=model,count=n,status=row['status'],completed=row['completed'],required=row['required'],search_seconds=row['search_seconds'],repair_seconds=row['repair_seconds'],repairs=row['repairs'],native_status=result['status'])
  if row['status']=='COMPLETE_DIAGNOSTIC':
   canonical=ROOT/f'experiments/{prefix}_n{n}_canonical_2026-10-07';cr=read(canonical/'receipt.json');cv=read(canonical/'verification.json');assert cv['receipt_sha256']==sha(canonical/'receipt.json') and cv['canonical_FULL_STA'] and cv['canonical_named_paths_exactly_match_native_postsync'];assert F(str(cv['cpd_ns']))==F(metrics['cpd_ns']);item.update(cpd_ns=metrics['cpd_ns'],reference_cpd_ns=metrics['reference_cpd_ns'],wirelength=metrics['wirelength'],reference_wirelength=metrics['reference_wirelength'],joint_nonregression=F(metrics['cpd_ns'])<=F(metrics['reference_cpd_ns']) and metrics['wirelength']<=metrics['reference_wirelength'])
  else:assert result['status']=='INCOMPLETE_NOT_SUBMITTED';item.update(failure=row['failure'],joint_nonregression=None)
  rows.append(item)
assert len(rows)==6 and not any(x['joint_nonregression'] for x in rows);assert all(sha(f)==h for f,h in bindings.items())
(out/'comparison.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,complete_variants={'50ps':3,'0ps':2},joint_improving_variants={'50ps':0,'0ps':0},scope='All3 variants eachpolicy retained, originalXML prefixaudit/nativecanonical checked. Archivalnative reference roundedQoR descriptive, not fresh quality gate/allcaseacceptednetgain. Separate single hostobservations; incomplete shorterrepair is not speedup. Development ablation, not strictheldout. No aggregate accuracy omitting incompletevariant.'),indent=2)+'\n');print('All6 policy/case outcomes bound; no joint improvement')

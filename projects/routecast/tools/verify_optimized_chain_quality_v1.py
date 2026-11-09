"""Authenticate actual optimized step lineage and whole-sequence quality arithmetic."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'optimized_chain_quality_verification_v1_2026-10-09'
plans=[(1,'adder_step1_from_inputs_checked_wire_native_quality_v6_2026-10-09','adder_step1_from_inputs_checked_wire_paths_verification_v6_2026-10-09','adder_step1_from_inputs_checked_v6_2026-10-09'),(2,'adder_optimized_step2_checked_wire_native_quality_v10_2026-10-09','adder_optimized_step2_checked_wire_paths_verification_v10_2026-10-09','adder_optimized_step2_checked_v10_2026-10-09'),(3,'adder_optimized_step3_checked_wire_native_quality_v11_2026-10-09','adder_optimized_step3_checked_wire_paths_verification_v11_2026-10-09','adder_optimized_step3_checked_v11_2026-10-09')]
bindings=closure([Path(__file__)]);rows=[];prior=None
for step,quality,selection,production in plans:
 p=E/quality/'verification.json';report=json.loads(p.read_text());assert all(sha(f)==h for f,h in report['bindings'].items());bindings.update(report['bindings']);bindings[str(p)]=sha(p)
 row=report['rows'][0];assert row['step']==step and row['native_and_canonical_connections']==[516,516]
 assert row['exact_model_budget_pass'] and row['full_named_paths_preserved'] and row['canonical_zero_counters']
 sp=E/selection/'selection.json';state=json.loads(sp.read_text())['paths'];assert len(state)==516
 bp=E/production/'result.json';bank=json.loads(bp.read_text())['bank'];old=0
 if prior is not None:
  previous_path,previous=prior;receipt=json.loads((E/production/'verification.json').read_text());assert receipt['bindings'][str(previous_path.resolve())]==sha(previous_path)
  for cid,options in bank.items():
   for option in options:
    if option['origin']=='OLD_ROUTE':assert option['path']==previous[cid];old+=1
  assert old>0
 for f in (sp,bp):bindings[str(f)]=sha(f)
 prior=(sp,state);rows.append(dict(step=step,wirelength=row['wirelength'],cold_wirelength=row['cold_wirelength'],wire_delta=row['wire_delta'],cpd_ns=row['cpd_ns'],old_candidates_exactly_from_prior_optimized_state=old if step>1 else None))
assert all(sha(f)==h for f,h in bindings.items());D.mkdir(exist_ok=False)
wire=sum(r['wirelength'] for r in rows);cold=sum(r['cold_wirelength'] for r in rows)
out=dict(bindings=bindings,rows=rows,sequence_wirelength_sum=wire,cold_sequence_wirelength_sum=cold,sequence_wire_delta=wire-cold,scope='Authenticated actual per-step optimized outputs and OLD_ROUTE lineage for generated steps2/3; wire sum over three placements is an accounting statistic, not a single design wirelength. No whole-sequence runtime gain, independent timing target or transaction execution claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})

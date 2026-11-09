"""Freeze all3 zero-feedback ablation by copying certified original warm frames."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';O=E/'prospective_external_family_zero_feedback_warm_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);cases=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';sp=P/'specifications'/case/'comparison_spec.json';spec=read(sp);base=Path(spec['predictions']['native_retained_on']['frame']);warm=base.parent/'initial.json';audit=Path(spec['predictions']['native_retained_on']['proof']);v=read(audit);assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(p)==h for p,h in v['bindings'].items());assert v['bindings'][str(warm)]==sha(warm);wp=P/'predictions'/case/'warm/native_retained/verification.json';w=read(wp);assert w['status']=='EXTERNAL_WARM_XML_PATHS_MATCHED_BUDGETS_LEDGER_AND_SOURCE_RETENTION_PASS' and w['native_staged_state_independent_xml_pass'];assert all(sha(p)==h for p,h in w['bindings'].items());assert warm.read_bytes()==(wp.parent/'initial.json').read_bytes();cases.append(dict(case=case,base_frame=str(base),warm_frame=str(warm),warm_proof=str(wp),original_audit=str(audit),original_comparison_spec=str(sp),endpoint=spec['endpoint']))
  for p in [sp,base,warm,audit,wp,Path(spec['endpoint'])]:bindings[str(p)]=sha(p)
 policy='Exactly one zero-feedback warm-frame ablation for all3 previously exposed width160 development cases. Copy original certified native_retained_on/initial.json bytes before any feedback round, without new search, route changes, budget/threshold selection or clock/epoch reinterpretation. Compare against original final native_retained_on as supplementary diagnosis and keep original previous_native/raw_min_on controls, all4 metrics and domains/K/gates. Freeze all inputs before reopening labels. No native utility, matched end-to-end time, unseen-family or hardware claim; six source-unavailable cases remain full9 availability failure. Independent original-XML full path/budget/single-parent/ledger audit before metrics.'
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(policy=policy,cases=cases,bindings=bindings,unavailable_cases=[f'w{w:03d}/episode_{i:02d}' for w in (96,128) for i in (1,2,3)]),indent=2)+'\n');bindings[str(pp)]=sha(pp);rows=[]
 for spec in cases:
  out=O/spec['case'];out.mkdir(parents=True);p=out/'frame.json';p.write_bytes(Path(spec['warm_frame']).read_bytes());f=read(p);bindings[str(p)]=sha(p);rows.append(dict(case=spec['case'],frame=str(p),CIDs=len(f['records']),overflow_units=f['overflow_units'],byte_identical_to_warm=True));print('ZERO_FEEDBACK_WARM',json.dumps(rows[-1]),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL3_ZERO_FEEDBACK_WARM_FRAMES_COPIED_PENDING_ORIGINAL_XML_AUDIT',rows=rows,bindings=bindings,labels_opened=False,scope=policy),indent=2)+'\n')
if __name__=='__main__':main()

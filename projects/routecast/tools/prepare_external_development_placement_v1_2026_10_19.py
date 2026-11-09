"""One fixed placement-only input-preparation run; not strict-test admission."""
import json,shutil,subprocess,resource,time,os
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_development_place_v1_2026-10-19';out.mkdir(exist_ok=False);draftp=R/'experiments/prospective_external_family_concrete_cohort_draft_v1_2026-10-18/draft.json';draft=read(draftp);placement=draft['placement'];support=[R/'experiments/prospective_external_family_semantic_review_v1_2026-10-19/verification.json',R/'experiments/prospective_external_family_grounded_packed_cut_v1_2026-10-19/independent_verification_v1.json',R/'experiments/prospective_external_family_packed_FF_v1_2026-10-18/verification.json'];proofs=[read(p) for p in support];assert proofs[0]['conditional_proof_composed'] and proofs[1]['FF_state_pairs']==1938 and proofs[2]['FF_bits']==1938;assert not any(p.get('strict_unseen_admitted',False) for p in proofs);bindings={str(p):sha(p) for p in [draftp,Path(__file__).resolve(),*support]};begin=time.perf_counter()
 for name,source in placement['required_staging'].items():
  source=Path(source);assert sha(source)==draft['bindings'][str(source)];shutil.copyfile(source,out/name);assert sha(out/name)==sha(source);bindings.update({str(p):sha(p) for p in [source,out/name]})
 cmd=placement['command'];assert '--place' in cmd and '--route' not in cmd and '--pack' not in cmd;assert cmd[cmd.index('--seed')+1]=='1' and cmd[cmd.index('--num_workers')+1]=='1';assert not (out/'source.place').exists();staging=time.perf_counter()-begin
 for p in map(Path,cmd[:2]):assert sha(p)==draft['bindings'][str(p)];bindings[str(p)]=sha(p)
 protocol=dict(status='FIXED_DEVELOPMENT_PLACEMENT_INPUT_PREPARATION',command=cmd,bindings=bindings,role='Development input preparation only. Family history UNKNOWN; no strict-test assignment, route label generation, model promotion or predicted/native-utility evaluation.',source_contract='Exact mapped/packed inputs with separately verified conditional-reset source and explicit-ground Boolean functional certificates. Not full unrestricted original HDL/four-state equivalence or physical reset/timing certification. Placement does not invoke a post-synthesis writer or change default-X export options.',policy='One unchanged fixed seed1/width128/workers1 placement call, retain failure. No outcome-driven width/seed selection, no routing. Existing old draft remains unsubmitted as a validation cohort; this separately named input-only development job is not that cohort.',AS_limit_bytes=8*2**30,timeout_seconds=None,staging_seconds=staging,cost_boundary='Source download/hierarchy/compile/pack/proofs/staging/placement remain paid upstream costs in any future workflow claim. This run establishes no matched on/off total-time benefit.')
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2));
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 start=time.perf_counter()
 with (out/'place.log').open('x') as f:
  child=subprocess.Popen(cmd,cwd=out,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit);stat=Path(f'/proc/{child.pid}/stat').read_text().rsplit(') ',1)[1].split();(out/'live_process.json').write_text(json.dumps(dict(pid=child.pid,start_ticks=stat[19],command=cmd),indent=2));print('DEVELOPMENT_PLACE_CHILD',child.pid,flush=True);code=child.wait()
 for p,h in bindings.items():assert sha(p)==h
 text=(out/'place.log').read_text();place=out/'source.place';rows=[]
 if place.exists():
  for line in place.read_text().splitlines():
   t=line.split()
   if t and not t[0].startswith('#') and len(t)>=5 and all(v.lstrip('-').isdigit() for v in t[1:4]):rows.append(t)
 routefiles=[p.name for p in out.glob('*.route')];assert not routefiles;success=code==0 and len(rows)>0
 receipt=dict(status='FIXED_DEVELOPMENT_PLACEMENT_COMPLETED_PENDING_AUDIT' if success else 'FIXED_DEVELOPMENT_PLACEMENT_FAILED_RETAINED',exit_code=code,placement_rows=len(rows),native_process_seconds=time.perf_counter()-start,staging_seconds=staging,strict_unseen_admitted=False,new_route_labels=False,independent_placement_audit_pending=True,bindings={str(p):sha(p) for p in [out/'protocol.json',out/'place.log',*([place] if place.exists() else [])]},source_inputs_unchanged=True,scope=protocol['role'])
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2));print('DEVELOPMENT_PLACE_TERMINAL',code,len(rows),flush=True)
if __name__=='__main__':main()

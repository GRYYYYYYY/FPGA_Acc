"""Restore provenance closure after an explicitly preserved source-path collision."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
 out=R/'experiments/shared_audit_filename_collision_recovery_v1_2026-10-17';recovery=json.loads((out/'recovery.json').read_text());old=Path(recovery['historical_path']);saved=Path(recovery['oct17_fork_implementation_preserved'])
 assert sha(old)==recovery['historical_expected_sha256'] and sha(saved)==recovery['oct17_fork_sha256']
 relocation={str(old):dict(expected_sha256=sha(saved),preserved_source_path=str(saved))};relocated=[];bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(out/'recovery.json'):sha(out/'recovery.json'),str(old):sha(old),str(saved):sha(saved)}
 for name in ['xtea_shared_independent_audit_context_v1_2026-10-17','xtea_shared_independent_audit_negative_v1_2026-10-17']:
  proof=R/'experiments'/name/'verification.json';v=json.loads(proof.read_text());assert v['all_pass'];bindings[str(proof)]=sha(proof)
  for section in ['bindings','outputs']:
   for p,h in v.get(section,{}).items():
    if p in relocation and h==relocation[p]['expected_sha256']:
     assert sha(saved)==h;relocated.append(dict(proof=str(proof),original_bound_path=p,preserved_source_path=str(saved),expected_sha256=h))
    else:assert sha(p)==h
 verified=[]
 for name in ['ultraembedded_mmc_continuous_workflow_v10_2026-10-09','mmc_audit_context_abba_v1_2026-10-17','xtea_audit_context_abba_v1_2026-10-17']:
  proof=R/'experiments'/name/'verification.json';v=json.loads(proof.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings[str(proof)]=sha(proof)
  for row in v.get('results',[]):
   arm=proof.parent/f'arm{row["index"]}_{row["mode"]}'/'verification.json';a=json.loads(arm.read_text());assert sha(arm)==row['proof_sha256']
   assert all(sha(p)==h for sec in ['bindings','outputs'] for p,h in a[sec].items())
  verified.append(name)
 result=dict(all_pass=True,historical_source_byte_exact_restored=True,historical_v10_and_both_recent_ABBA_binding_checks_pass=True,normal_binding_revalidated_roots=verified,early_fork_v1_proofs_require_explicit_source_relocation=relocated,original_proof_JSONs_not_rewritten=True,do_not_rerun_early_fork_v1_at_historical_path=True,interpretation='Restored old source path is authoritative for historical workflow. Oct17 fork source bytes are authenticated at saved unique filename; old v1 proof path no longer matches those bytes directly, so provenance must cite this relocation record. New v2/MMC fork evidence reauthenticates without relocation.',bindings=bindings)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS historical byte recovery, explicit early-fork source relocation and independent ABBA binding closure')
if __name__=='__main__':main()

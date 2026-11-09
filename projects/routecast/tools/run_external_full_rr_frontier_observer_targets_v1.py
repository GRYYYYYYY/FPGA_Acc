"""All3 fixed original native cases with source-verified observer, sequential execution."""
import json,sys,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from run_external_native_route_case_v1 import execute
D=R/'experiments/prospective_external_family_full_rr_frontier_observer_v1_2026-10-19'
def main():
 p=D/'source_equivalence_verification_v1.json';a=json.loads(p.read_text());assert a['final_route_identical'] and all(sha(q)==h for q,h in a['bindings'].items());m=json.loads((D/'manifest.json').read_text());original=json.loads((R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19/native_manifest.json').read_text());binary=m['cases'][0]['command'][0];cases=[]
 for r in original['cases']:
  if r['case'].startswith('w160/episode_'):
   r=copy.deepcopy(r);r['output']=str(D/r['case']);r['command'][0]=binary;cases.append(r)
 assert len(cases)==3;m['cases']=cases;m['bindings'][str(p)]=sha(p);m['bindings'][str(Path(__file__).resolve())]=sha(__file__);mp=D/'target_manifest.json'
 with mp.open('x') as f:json.dump(m,f,indent=2)
 results=[]
 for r in cases:
  a=execute(mp,r['case']);results.append(dict(case=r['case'],status=a['status']));print(results[-1],flush=True)
  if a['status']!='FULL_PHYSICAL_AND_CANONICAL_PASS':raise RuntimeError(results[-1])
 with (D/'targets_terminal.json').open('x') as f:json.dump(dict(status='ALL3_OBSERVER_NATIVE_CASES_PHYSICAL_CANONICAL_PASS',rows=results),f,indent=2)
if __name__=='__main__':main()

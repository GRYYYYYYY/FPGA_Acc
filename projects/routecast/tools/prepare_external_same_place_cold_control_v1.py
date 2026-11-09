"""Audit config identity then freeze one no-edit same-placement cold repeat."""
import json,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prospective_external_family_termination_diagnostic_v1_2026-10-19';T=E/'prospective_external_family_supplementary_development_v1_2026-10-19';D=E/'prospective_external_family_same_place_cold_control_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 m=read(S/'manifest.json');n=read(T/'native_manifest.json');assert all(sha(p)==h for p,h in m['bindings'].items());assert all(sha(p)==h for p,h in n['bindings'].items());source=next(r for r in m['cases'] if r['case']=='w160/noearly_300/source');sp=Path(source['output'])/'verification.json';source_audit=read(sp);assert source_audit['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(sha(p)==h for p,h in source_audit['bindings'].items());D.mkdir(exist_ok=False);rows=[]
 for target in n['cases']:
  if not target['case'].startswith('w160/'):continue
  assert target['command']==source['command'];same={k:sha(source['inputs'][k])==sha(target['inputs'][k]) for k in ['blif','net','place']};assert same['blif'] and same['net'] and not same['place'];rows.append(dict(case=target['case'],command_identical=True,includes_same_binary_arch_graph_seed_workers_and_router_options=True,input_hash_equal=same))
 assert len(rows)==3
 protocol=dict(status='ALL3_EXPLICIT_NATIVE_COMMANDS_IDENTICAL_ONLY_PLACE_INPUT_DIFFERS',comparisons=rows,source_verification=str(sp),policy='Freeze one same-source-placement seed1 single-worker cold repeat, exact binary/arch/graph/net/blif/command, sanitized ROUTECAST environment and same 32GiB limit. No tuning or replacement labels; repeat tests reproducibility of this config only, not universal determinism. Source terminal.json stale failure status conflicts with completed passing verification; rely on full binding-verified verification and exit0, preserve originals.',bindings={str(S/'manifest.json'):sha(S/'manifest.json'),str(T/'native_manifest.json'):sha(T/'native_manifest.json'),str(sp):sha(sp),str(Path(__file__).resolve()):sha(__file__)})
 pp=D/'protocol.json';pp.write_text(json.dumps(protocol,indent=2)+'\n');control=copy.deepcopy(source);control['case']='w160/same_place_repeat_01';control['output']=str(D/'native');control['role']='same_place_no_edit_cold_control';new=copy.deepcopy(m);new['cases']=[control];new['bindings'].update(protocol['bindings']);new['bindings'][str(pp)]=sha(pp);new['scope']='One diagnostic same-placement cold repeat; original cases and labels unchanged.';mp=D/'manifest.json';mp.write_text(json.dumps(new,indent=2)+'\n');print(mp)
if __name__=='__main__':main()

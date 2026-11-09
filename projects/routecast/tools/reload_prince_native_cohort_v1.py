"""Unmodified saved-route native analysis reload; never silently repair artifacts."""
import json,shutil,subprocess,os,time,resource
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/prince_native_cohort_v1_2026-10-20';D=R/'experiments/prince_native_reload_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def main():
 D.mkdir(exist_ok=False);pp=O/'protocol.json';proof=O/'independent_physical_verification_v1.json';p=json.loads(pp.read_text());v=json.loads(proof.read_text());admitted={r['case'] for r in v['rows'] if r['eligible_legal_label']};jobs=[]
 for j in p['jobs']:
  if j['case'] not in admitted:continue
  s=Path(j['directory']);d=D/j['case'];d.mkdir(parents=True)
  for name in ['design.blif','design.net','design.place','output.route']:shutil.copyfile(s/name,d/name)
  cmd=j['command'].copy();cmd[cmd.index('--route')]='--analysis';cmd[cmd.index('--write_rr_graph')]='--read_rr_graph';jobs.append(dict(case=j['case'],source=str(s),directory=str(d),command=cmd))
 paths=[pp,proof,Path(__file__),Path(jobs[0]['command'][0]),Path(jobs[0]['command'][1])]
 for j in jobs:paths.extend(Path(j['directory'])/name for name in ['design.blif','design.net','design.place','output.route']);paths.append(Path(j['source'])/'rr_graph.xml')
 bindings={str(p):sha(p) for p in paths};(D/'protocol.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,scope='Direct native analysis reload of byte-identical saved inputs; no artifact canonicalization, no route search. Full original native checks retained. Success alone does not certify zero mapping repairs or byte-identical final packed netlist.'),indent=2)+'\n');results=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 for j in jobs:
  d=Path(j['directory']);tick=time.perf_counter()
  with (d/'reload.log').open('x') as f:code=subprocess.call(j['command'],cwd=d,stdout=f,stderr=subprocess.STDOUT,env=env,preexec_fn=limit)
  text=(d/'reload.log').read_text();passed=code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;row=dict(case=j['case'],exit_code=code,native_full_reload_pass=passed,seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in d.iterdir() if p.is_file()});results.append(row);(d/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');print('NATIVE_RELOAD',j['case'],code,passed,flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'receipt.json').write_text(json.dumps(dict(results=results,bindings=bindings,canonical_semantic_gate_proven=False,strict_unseen_admitted=False),indent=2)+'\n')
if __name__=='__main__':main()

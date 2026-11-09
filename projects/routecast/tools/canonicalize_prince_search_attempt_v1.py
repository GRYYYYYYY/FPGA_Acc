"""Original full canonical reload gate for every independently legal diagnostic run."""
import json,sys,re,subprocess,resource,os,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
import canonical_reload_pin_index_expat_v3 as canonical
from shared_compact_native_inventory_v1 import Inventory
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_search_attempt_trial_v1_2026-10-20';D=E/'prince_search_attempt_canonical_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def run(cmd,work,log,environment):
 with log.open('x') as f:return subprocess.call(cmd,cwd=work,stdout=f,stderr=subprocess.STDOUT,env=environment,preexec_fn=limit)
def main():
 D.mkdir(exist_ok=False);pp=S/'protocol.json';proof=S/'independent_physical_verification_v1.json';p=json.loads(pp.read_text());v=json.loads(proof.read_text());admitted={x['case'] for x in v['rows'] if x['eligible_legal_label']};canonical.run=run;bindings={str(q):sha(q) for q in [pp,proof,Path(__file__),Path(canonical.__file__),R/'tools/shared_compact_native_inventory_v1.py',canonical.binary,canonical.identity]};(D/'protocol.json').write_text(json.dumps(dict(admitted=sorted(admitted),bindings=bindings,scope='Existing full canonical gate; native analysis reload, exact packed bytes/physical sequences/diagnostic CPD and full XML capacity/arc audit. Failed native runs retained in source cohort, not canonicalized into legality.'),indent=2)+'\n');inventories={};results=[]
 for j in p['jobs']:
  if j['case'] not in admitted:continue
  tick=time.perf_counter();s=Path(j['directory']);graph=Path(j['command'][j['command'].index('--read_rr_graph')+1]);digest=sha(graph)
  key=(str(graph),digest)
  if key not in inventories:inventories[key]=Inventory(graph)
  cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',(s/'native.log').read_text())[-1]);candidate=dict(files={str(q):sha(q) for q in s.iterdir() if q.is_file()},width=int(j['case'].split('/')[0][1:]),decision='R',command=j['command'],cpd_ns=cpd);destination=D/j['case'];destination.parent.mkdir(parents=True,exist_ok=True)
  try:result=canonical.canonical_reload(candidate,s,destination,inventories[key]);result['case']=j['case']
  except Exception as exc:result=dict(case=j['case'],semantic_consistency_gate_pass=False,error=repr(exc))
  result['canonical_paid_seconds']=time.perf_counter()-tick;destination.mkdir(exist_ok=True);(destination/'verification.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);print('ORACLE_CANONICAL',j['case'],result['semantic_consistency_gate_pass'],result.get('error',''),flush=True)
 assert len(results)==len(admitted) and all(sha(q)==h for q,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(results=results,bindings=bindings,label_dependent_diagnostic=False,strict_unseen_admitted=False),indent=2)+'\n')
if __name__=='__main__':main()

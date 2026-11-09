"""Existing full canonical gate applied to source-bound PRINCE native reloads."""
import json,sys,re,subprocess,resource,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
import canonical_reload_pin_index_expat_v3 as canonical
from shared_compact_native_inventory_v1 import Inventory
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_native_canonical_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def run(cmd,work,log,environment):
 with log.open('x') as f:return subprocess.call(cmd,cwd=work,stdout=f,stderr=subprocess.STDOUT,env=environment,preexec_fn=limit)
def main():
 D.mkdir(exist_ok=False);root=E/'prince_native_reload_v1_2026-10-20';pp=root/'protocol.json';p=json.loads(pp.read_text());receipt=root/'receipt.json';v=json.loads(receipt.read_text());assert all(x['native_full_reload_pass'] for x in v['results']);canonical.run=run
 bindings={str(x):sha(x) for x in [pp,receipt,Path(__file__),Path(canonical.__file__),canonical.binary,canonical.identity]};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Apply existing full canonical reload gate; exact source physical sequences, post-routing packed bytes, graph arcs/capacity, diagnostic CPD and ignored-pin-only repair membership. No timeout/retry or physical timing claim.'),indent=2)+'\n');results=[]
 for j in p['jobs']:
  s=Path(j['directory']);graph=Path(j['source'])/'rr_graph.xml';cmd=j['command'].copy();cmd[cmd.index('--analysis')]='--route';cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',(s/'reload.log').read_text())[-1]);candidate=dict(files={str(f):sha(f) for f in s.iterdir() if f.is_file()},width=int(j['case'].split('/')[0][1:]),decision='R',command=cmd,cpd_ns=cpd);destination=D/j['case'];destination.parent.mkdir(parents=True,exist_ok=True)
  try:
   result=canonical.canonical_reload(candidate,s,destination,Inventory(graph));result['case']=j['case']
  except Exception as exc:result=dict(case=j['case'],semantic_consistency_gate_pass=False,error=repr(exc))
  results.append(result);(destination/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('CANONICAL_PRINCE',j['case'],result['semantic_consistency_gate_pass'],result.get('error',''),flush=True)
 assert all(sha(f)==h for f,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(results=results,bindings=bindings,strict_unseen_admitted=False),indent=2)+'\n')
if __name__=='__main__':main()

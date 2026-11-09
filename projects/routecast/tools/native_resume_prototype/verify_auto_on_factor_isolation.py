"""Authenticate raw AUTO equality and isolate effective fanout change on cohort."""
import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'experiments/native_resume_auto_on_equivalence_v2_2026-10-07'
pp,rp,vp=base/'protocol.json',base/'receipt.json',base/'verification.json';p,r,v=[json.loads(f.read_text()) for f in (pp,rp,vp)]
assert r['protocol_sha256']==sha(pp) and v['receipt_sha256']==sha(rp) and v['all24_paths_and_work_equal']
assert all(sha(file)==digest for file,digest in p['bindings'].items())
prior=ROOT/'experiments/native_resume_allfanout_cohort_2026-10-07/verification.json';e=json.loads(prior.read_text());assert all(sha(file)==digest for file,digest in e['bindings'].items())
lookup={(x['width'],x['index']):x for x in e['rows']};bindings={str(f):sha(f) for f in (pp,rp,vp,prior,Path(__file__))};checks=[]
for row in r['rows']:
 w,i,mode=row['width'],row['index'],row['mode'];assert row['exit_code']==0 and row['paths_equal'] and row['work_equal'] and row['rerouted_net_rows_equal'] and row['iterations']<100
 for file,digest in row['files'].items():assert sha(file)==digest;bindings[file]=digest
 log=base/f'w{w}_m{i}_{mode}/run.log';text=log.read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1];wire=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]);index=0 if mode=='workflow' else 1
 assert cpd==lookup[w,i]['cpd_pair'][index] and wire==lookup[w,i]['wire_pair'][index]
 if mode=='workflow':
  seed=ROOT/f'experiments/native_resume_allfanout_w{w}_m{i}_workflow_2026-10-07/first_seed.route';assert sha(seed)==e['bindings'][str(seed)];bindings[str(seed)]=sha(seed)
 checks.append(dict(width=w,index=i,mode=mode,qor_equal=True,paths_and_work_equal=True,iterations=row['iterations']))
old=ROOT/'experiments/native_resume_precritical_cohort_2026-10-07/verification.json';o=json.loads(old.read_text());assert all(sha(file)==digest for file,digest in o['bindings'].items());bindings[str(old)]=sha(old)
assert len(checks)==24 and all(sha(file)==digest for file,digest in bindings.items())
result=dict(bindings=bindings,checks=checks,auto_fanout16_quality_passes=o['quality_passes'],auto_fanout0_quality_passes=e['quality_passes'],scope='Direct AUTO fanout0 vs ON fanout0 native equality, QoR independently read and matched to prior full canonical proofs. Compare previous AUTO defaultfanout16 outcome to AUTO0 on same development inputs; source NORMAL initial/transition threshold100 plus actual iterations12-16 explain AUTO/ON equality. No equivalence after CONFLICTED and no new AUTO0 full-cost measurement. First v1 verifier nonexistent counter-key failure retained, no outputs claimed from it.')
(base/'factor_isolation.json').write_text(json.dumps(result,indent=2)+'\n');print(result['auto_fanout16_quality_passes'],result['auto_fanout0_quality_passes'],len(checks))

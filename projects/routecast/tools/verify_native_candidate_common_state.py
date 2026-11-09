import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_common_state_2026-10-06';work=root/'work/native_candidate_common_state_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['results'])==40 and len(r['comparisons'])==20;files=[out/'receipt.json',out/'protocol.json'];groups={}
for row in r['results']:
 name=f"{row['index']:02d}_{row['mode']}";case=out/name;cwd=work/name;log=(case/'run.log').read_text();assert row['exit_code']==0 and all(sha(p)==h for p,h in row['inputs_sha256'].items());assert sha(case/'run.log')==row['log_sha256'];assert 'moved candidate passed native FULL routing check' in log
 assert sha(cwd/'candidate_0.route')==row['candidate_sha256'] and sha(cwd/'output.route')==row['final_route_sha256'] and sha(cwd/'design.net.post_routing')==row['packed_sha256'];assert 'Placement_ID: SHA256:'+sha(cwd/'accepted.place') in (cwd/'output.route').read_text().splitlines()[0]
 assert row['accepted']==(row['candidate_cpd_ns']<=row['before_cpd_ns']+1e-5);groups.setdefault(row['index'],{})[row['mode']]=row;files.extend(case.glob('*'));files.extend(cwd.glob('*'))
for i,group in groups.items():
 c=group['cold'];t=group['retained'];assert {Path(p).name:h for p,h in c['inputs_sha256'].items()}=={Path(p).name:h for p,h in t['inputs_sha256'].items()} and c['before_cpd_ns']==t['before_cpd_ns'];assert c['pair']==t['pair']
summary={'retained_better':sum(x['retained_minus_cold_cpd_ns']<-1e-5 for x in r['comparisons']),'equal':sum(abs(x['retained_minus_cold_cpd_ns'])<=1e-5 for x in r['comparisons']),'retained_worse':sum(x['retained_minus_cold_cpd_ns']>1e-5 for x in r['comparisons']),'decision_disagreements':sum(x['decision_differs'] for x in r['comparisons'])}
(out/'verification.json').write_text(json.dumps({'pairs':20,'candidate_and_final_routes':80,'summary':summary,'sha256':{str(p):sha(p) for p in files if p.is_file()},'scope':r['scope']},indent=2)+'\n');print(summary)

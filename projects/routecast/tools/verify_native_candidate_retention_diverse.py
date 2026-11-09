import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_retention_diverse_benchmark_2026-10-06';work=root/'work/native_candidate_retention_diverse_benchmark_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['runs'])==12;protocol=json.loads((out/'protocol.json').read_text());files=[out/'receipt.json',out/'protocol.json'];seen={};details=[]
def locations(p):
 return {int(f[-1][1:]):tuple(map(int,f[1:5])) for l in p.read_text().splitlines() if len(f:=l.split())==6 and f[-1].startswith('#')}
for row in r['runs']:
 name=f"{row['design']}_{row['repeat']}_{row['mode']}";case=out/name;cwd=work/name;log=(case/'run.log').read_text();assert sha(case/'run.log')==row['log_sha256'];assert all(sha(p)==h for p,h in row['inputs_sha256'].items());assert sha(cwd/'output.route')==row['route_sha256'] and sha(cwd/'design.net.post_routing')==row['packed_sha256']
 pairs=protocol['pairs'][row['design']];nsteps=len(pairs);chunks=re.split(r'ROUTECAST sequence step=\d+ decision=A\n',log)[1:];assert len(chunks)==nsteps;assert log.count('moved candidate passed native FULL routing check')==nsteps;current=float(re.search(r'synchronized baseline CPD=([0-9.]+)',log)[1]);expected=locations(cwd/'design.place');decisions=[]
 for i,chunk in enumerate(chunks):
  before,candidate=map(float,re.search(r'before_cpd_ns=([0-9.]+) candidate_cpd_ns=([0-9.]+)',chunk).groups());assert abs(before-current)<1e-5;accepted='accepted actual moved candidate after FULL check, packing sync and STA' in chunk
  if accepted:
   assert candidate<=before+1e-5;current=candidate;a,b=pairs[i];expected[a],expected[b]=expected[b],expected[a]
  else:assert candidate>=before-1e-5 and 'restored delay matrix and all edge-delay/STA metric observations' in chunk
  decisions.append('A' if accepted else 'R')
 final=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]);assert abs(final-current)<1e-5 and expected==locations(cwd/'accepted.place');assert 'Placement_ID: SHA256:'+sha(cwd/'accepted.place') in (cwd/'output.route').read_text().splitlines()[0]
 armed=re.findall(r'armed context-bound candidate sync ticket epoch=(\d+)',log);consumed=re.findall(r'consume context-bound candidate sync ticket epoch=(\d+)',log);assert armed==consumed==list(map(str,range(1,len(armed)+1)))
 signature=(row['route_sha256'],row['packed_sha256'],''.join(decisions),final);key=(row['design'],row['mode']);assert key not in seen or seen[key]==signature;seen[key]=signature;details.append({'case':name,'decisions':signature[2],'final_cpd_ns':final,'epochs':len(armed)});files.extend(case.glob('*'));files.extend(cwd.glob('*'))
(out/'verification.json').write_text(json.dumps({'runs':12,'candidate_steps':180,'details':details,'sha256':{str(p):sha(p) for p in files if p.is_file()},'scope':'10/20 native FULL candidate gates per process and independent final-route audits from benchmark; per-decision timing/coordinate replay, repeat byte identity. Intermediate candidates not independently re-audited here; known designs, frozen distinct pair lists.'},indent=2)+'\n');print('verified distinct pair sequences')

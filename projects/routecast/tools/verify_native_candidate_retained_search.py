import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_retained_search_2026-10-06';work=root/'work/native_candidate_retained_search_2026-10-06';r=json.loads((out/'receipt.json').read_text());files=[out/'receipt.json',Path(r['results'][0]['command'][0])]
def locations(p):
 return {int(f[-1][1:]):tuple(map(int,f[1:5])) for l in p.read_text().splitlines() if len(f:=l.split())==6 and f[-1].startswith('#')}
for row in r['results']:
 cwd=work/row['design'];case=out/row['design'];log=(case/'run.log').read_text();chunks=re.split(r'ROUTECAST sequence step=\d+ decision=A\n',log)[1:];assert len(chunks)==4;current=row['baseline_cpd_ns'];expected=locations(cwd/'design.place');decisions=[]
 for chunk,(a,b) in zip(chunks,[(0,1),(2,3),(1,2),(0,4)]):
  before,candidate=map(float,re.search(r'before_cpd_ns=([0-9.]+) candidate_cpd_ns=([0-9.]+)',chunk).groups());assert abs(before-current)<1e-5
  accepted='accepted actual moved candidate after FULL check, packing sync and STA' in chunk
  if accepted:
   assert candidate<=before+1e-5;current=candidate;expected[a],expected[b]=expected[b],expected[a]
  else:
   assert candidate>=before-1e-5 and 'restored delay matrix and all edge-delay/STA metric observations' in chunk
  decisions.append('A' if accepted else 'R')
 assert abs(current-row['final_cpd_ns'])<1e-5 and expected==locations(cwd/'accepted.place');row['verified_decisions']=''.join(decisions)
 assert all(sha(p)==h for p,h in row['inputs_sha256'].items()) and sha(case/'run.log')==row['log_sha256'];files.extend(p for p in cwd.iterdir() if p.is_file());files.extend(p for p in case.iterdir() if p.is_file())
(out/'verification.json').write_text(json.dumps({'results':r['results'],'sha256':{str(p):sha(p) for p in files},'scope':r['scope']},indent=2)+'\n');print('verified')

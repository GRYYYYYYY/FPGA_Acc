import json,re,math
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_dynamic_order_2026-10-06';work=root/'work/native_candidate_dynamic_order_2026-10-06';r=json.loads((out/'receipt.json').read_text());details=[];files=[]
for result,count in zip(r['results'],(129,516)):
 design=result['design'];cwd=work/design;log=(out/design/'run.log').read_text();cmd=result['command'];graph=cmd[cmd.index('--read_rr_graph')+1];chunks=re.split(r'ROUTECAST sequence step=\d+ decision=A\n',log)[1:];epoch=0
 for step,chunk in enumerate(chunks):
  prefix=cwd/f'state_{step}';lines=prefix.with_suffix('.tsv').read_text().splitlines();head=lines[0].split('\t');assert int(head[1])==epoch and int(head[3])==step;cpd=float(head[5]);before=float(re.search(r'before_cpd_ns=([0-9.]+)',chunk)[1]);assert math.isfinite(cpd) and abs(cpd*1e9-before)<1e-5
  rows=[l.split('\t') for l in lines[2:]];assert len(rows)==count
  for x in rows:assert math.isfinite(float(x[6])) and float(x[6])>=0 and math.isfinite(float(x[7])) and 0<=float(x[7])<=1.000001
  a=audit(graph,prefix.with_suffix('.route'));assert len(a['connections'])==count and a['overflow_units']==0
  assert Counter((int(x[0]),int(x[4]),int(x[5])) for x in rows)==Counter((c['net_id'],c['source'],c['sink']) for c in a['connections'])
  if step and 'accepted actual moved candidate after FULL check, packing sync and STA' not in chunks[step-1]:
   previous=cwd/f'state_{step-1}';assert prefix.with_suffix('.tsv').read_text().splitlines()[1:]==previous.with_suffix('.tsv').read_text().splitlines()[1:]
   for ext in ('.route','.place'):assert prefix.with_suffix(ext).read_bytes()==previous.with_suffix(ext).read_bytes()
  details.append({'design':design,'step':step,'epoch':epoch,'cpd_ns':cpd*1e9,'connections':count});files.extend(prefix.with_suffix(x) for x in ('.tsv','.place','.route'))
  if 'accepted actual moved candidate after FULL check, packing sync and STA' in chunk:epoch+=1
(out/'frame_verification.json').write_text(json.dumps({'frames':details,'sha256':{str(p):sha(p) for p in files},'scope':'Current accepted pre-move native observations, all frame physical endpoints audited. Native NET/pin numbering; no predictor score or total performance claim.'},indent=2)+'\n');print('verified',len(details),'frames')

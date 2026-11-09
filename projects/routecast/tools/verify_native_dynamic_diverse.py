import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_dynamic_diverse_2026-10-06';work=root/'work/native_candidate_dynamic_diverse_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());results=[]
def locations(p):
 return {int(f[-1][1:]):tuple(map(int,f[1:5])) for l in p.read_text().splitlines() if len(f:=l.split())==6 and f[-1].startswith('#')}
for result in receipt['results']:
 design=result['design'];pairs=[tuple(x) for x in protocol['pairs'][design]];cwd=work/design;log=(out/design/'run.log').read_text();chosen=re.findall(r'dynamic selection step=(\d+) epoch=(\d+) pool_index=(\d+) score=([^ ]+) blocks=(\d+),(\d+)',log);assert len(chosen)==len(pairs);remaining=set(range(len(pairs)));expected=locations(cwd/'design.place');chunks=re.split(r'ROUTECAST sequence step=\d+ decision=A\n',log)[1:];epoch=0
 for i,(step,e,index,score,a,b) in enumerate(chosen):
  assert int(step)==i and int(e)==epoch;index=int(index);assert index in remaining and (int(a),int(b))==pairs[index];loc=locations(cwd/f'state_{i}.place');assert loc==expected;rows=[l.split('\t') for l in (cwd/f'state_{i}.tsv').read_text().splitlines()[2:]];scores={}
  for j in remaining:
   ca,cb=pairs[j];moved=loc.copy();moved[ca],moved[cb]=moved[cb],moved[ca];value=0
   for row in rows:
    s,t=int(row[2]),int(row[3]);old=abs(loc[s][0]-loc[t][0])+abs(loc[s][1]-loc[t][1]);new=abs(moved[s][0]-moved[t][0])+abs(moved[s][1]-moved[t][1]);value+=float(row[7])*(new-old)
   scores[j]=value
  assert abs(scores[index]-float(score))<1e-5 and scores[index]<=min(scores.values())+1e-5;remaining.remove(index)
  if 'accepted actual moved candidate after FULL check, packing sync and STA' in chunks[i]:
   a,b=pairs[index];expected[a],expected[b]=expected[b],expected[a];epoch+=1
 assert not remaining and expected==locations(cwd/'accepted.place');results.append({'design':design,'order':[int(x[2]) for x in chosen],'final_cpd_ns':result['final_cpd_ns']})
(out/'dynamic_verification.json').write_text(json.dumps({'results':results,'frame_verification_sha256':sha(out/'frame_verification.json'),'receipt_sha256':sha(out/'receipt.json'),'scope':'Recomputed scores from each verified current-state frame; all fixed-pool pairs attempted once, geometry weighted by live native criticality. Not RC/STA prediction or performance evidence.'},indent=2)+'\n');print(results)

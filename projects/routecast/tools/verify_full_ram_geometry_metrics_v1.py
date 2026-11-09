"""Independent pairwise ranks and serialized-vector metric arithmetic."""
import hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'experiments/full_ram_geometry_evaluation_v1_2026-10-09'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
e=json.loads((D/'evaluation.json').read_text())
for p,h in e['bindings'].items():assert sha(p)==h
assert sha(D/'vectors.json')==e['vectors_sha256']
rows=json.loads((D/'vectors.json').read_text());keys=[r['key'] for r in rows]
assert keys==sorted(set(keys)) and len(rows)==2400
p=[r['prediction'] for r in rows];t=[r['truth'] for r in rows]
assert all(math.isfinite(v) and v>=0 for v in p+t)
rank=lambda values:[2*sum(other<value for other in values)+sum(other==value for other in values)-1 for value in values]
a,b=rank(p),rank(t);mean=len(rows)-1
rho=sum((x-mean)*(y-mean) for x,y in zip(a,b))/math.sqrt(sum((x-mean)**2 for x in a)*sum((y-mean)**2 for y in b))
ps=sorted(range(len(rows)),key=lambda i:(-p[i],keys[i]))[:20]
ts=sorted(range(len(rows)),key=lambda i:(-t[i],keys[i]))[:20]
hits=len(set(ps)&set(ts));mae=math.fsum(abs(x-y) for x,y in zip(p,t))/len(rows)
m=e['spatial'];assert abs(rho-m['spearman'])<1e-14
assert hits/20==m['precision_at_k']==m['recall_at_k']
assert abs(mae-m['mae'])<1e-14
out=dict(passed=True,pairwise_rank_spearman=rho,top20_hits=hits,mae=mae,
    bindings={str(path):sha(path) for path in [Path(__file__),D/'evaluation.json',D/'vectors.json']},
    scope='Independent metric arithmetic on all serialized spatial vectors. Not independent graph/route reconstruction, unseen-family evidence or routability calibration.')
(D/'metric_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(rho,hits,mae)

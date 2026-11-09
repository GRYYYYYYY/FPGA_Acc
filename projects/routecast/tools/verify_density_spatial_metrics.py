"""Independent pairwise exact midranks and top20 from serialized full vectors."""
import json
import math
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/density_spatial_cells_2026-10-07'
ep=base/'evaluation.json';ev=json.loads(ep.read_text());assert all(sha(p)==h for p,h in ev['bindings'].items())
rows=[]
for expected in ev['rows']:
    w,i=expected['width'],expected['index'];vf=base/f'w{w}_m{i}.json'
    assert sha(vf)==ev['bindings'][str(vf)];data=json.loads(vf.read_text())
    ids=[tuple(r['cell']) for r in data];assert ids==sorted(set(ids)) and len(ids)==expected['universe_size']
    p=[F(r['prediction']) for r in data];t=[F(r['native']) for r in data]
    assert all(type(r['capacity']) is int and r['capacity']>0 for r in data)
    assert all(x>=0 for x in p+t)
    # Twice midrank, determined by independent pairwise comparisons.
    rank=lambda xs:[2*sum(v<x for v in xs)+sum(v==x for v in xs)-1 for x in xs]
    a,b=rank(p),rank(t);center=len(ids)-1
    numerator=sum((x-center)*(y-center) for x,y in zip(a,b))
    denominator=math.sqrt(sum((x-center)**2 for x in a)*sum((y-center)**2 for y in b))
    rho=None if denominator==0 else numerator/denominator
    assert rho is not None and abs(rho-expected['spearman'])<1e-14
    ps=sorted(range(len(ids)),key=lambda k:(-p[k],ids[k]))[:20]
    ts=sorted(range(len(ids)),key=lambda k:(-t[k],ids[k]))[:20]
    overlap=len(set(ps)&set(ts));assert overlap/20==expected['precision_at_k']==expected['recall_at_k']
    mae=sum(abs(x-y) for x,y in zip(p,t))/len(p);assert mae==F(expected['mae'])
    rows.append(dict(width=w,index=i,pairwise_rank_parity=True,top20_hits=overlap,mae_exact=True))
report=dict(evaluation_sha256=sha(ep),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent metric arithmetic on all serialized cells; input provenance hashes revalidated. Does not independently reconstruct XML capacities or native physical route, and does not establish heldout generalization.')
(base/'metric_verification.json').write_text(json.dumps(report,indent=2)+'\n');print('verified',len(rows))

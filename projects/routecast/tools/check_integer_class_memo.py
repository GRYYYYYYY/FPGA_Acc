"""Used-class exact lattice versus original per-node/per-arc enumeration."""
import random,json
from fractions import Fraction as F
from pathlib import Path
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context_memo import IntegerRC as Reference
from integer_rc_context_class_memo import IntegerRC
from pre_route_endpoints import sha
rng=random.Random(17);arcs=0
for trial in range(120):
 n=rng.randrange(2,25);classes=[(F(rng.randrange(9),rng.randrange(1,13)),F(rng.randrange(9),rng.randrange(1,13))) for _ in range(7)];indices=[rng.randrange(5) for _ in range(n)];switches={s:(F(rng.randrange(9),rng.randrange(1,13)),F(rng.randrange(9),rng.randrange(1,13))) for s in range(4)};rows=[0];dest=[];sids=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.25:dest.append(v);sids.append(rng.randrange(3))
  rows.append(len(dest))
 fields=dict(node_ids=list(range(n)),row_offsets=rows,dest_ranks=dest,switch_ids=sids,edge_ids=list(range(len(dest))));a=Reference(ExactBufferedRC(fields,indices,classes,switches));b=IntegerRC(ExactBufferedRC(fields,indices,classes,switches));assert a.scale==b.scale and a.increments==b.increments;assert [a.initial(x) for x in range(n)]==[b.initial(x) for x in range(n)];arcs+=len(dest)
p=Path(__file__).resolve().parents[1]/'experiments/integer_class_memo_contract_2026-10-07';p.mkdir();(p/'verification.json').write_text(json.dumps(dict(graphs=120,arcs=arcs,source_sha256=sha(Path(__file__)),implementation_sha256=sha(Path(__file__).with_name('integer_rc_context_class_memo.py')),scope='Exact Fraction random repeated/unused classes, zero R/C and actual used switches; scale/increments/initial states match original enumeration. No true graph runtime claim.'),indent=2)+'\n');print(arcs)

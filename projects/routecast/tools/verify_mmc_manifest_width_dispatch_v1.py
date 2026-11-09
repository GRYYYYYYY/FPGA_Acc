"""Every actual dispatch bound vs current native manifest and fresh model prices."""
from pathlib import Path
import json,re
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10';M=O/'model';N=O/'native';files=[Path(__file__).resolve(),N/'queries.txt',N/'native.log',M/'round0.json',M/'round1.json'];g=(N/'queries.txt').open().readline().split();assert g[0]=='G';n,edges,queries=map(int,g[1:]);assert (n,edges,queries)==(904438,8097539,115572)
vectors=[{},{}]+[{int(k):v for k,v in json.loads((M/f'round{i}.json').read_text())['prices'].items()} for i in range(2)];rows=[];log=(N/'native.log').read_text();assert f'nodes={n} edges={edges} exact rows/capacity/source/sink/switch' in log
for index,m in enumerate(re.finditer(r'ROUTECAST_WIDTH phase=(\d+) bits=(\d+) bound_hi=(\d+) bound_lo=(\d+) max_price=(\d+)',log)):
 phase,bits,hi,lo,maximum=map(int,m.groups());assert phase==[0,0,1,2][index];assert maximum==max(vectors[index].values(),default=0);weight=0 if phase==0 else 50000000;bound=2*n*(312900011+weight*maximum);assert bound==(hi<<64)+lo and bound<2**120 and bits==(64 if bound<2**64-1 else 128);rows.append(dict(phase=phase,bits=bits,maximum_price=maximum,bound=bound))
assert len(rows)==4 and all(r['bits']==64 for r in rows)
(O/'width_dispatch_verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},actual_bounds_and_modes_pass=True,all_current_MMC_price_phases_use64_safely=True,rows=rows,scope='Complete observed current MMC dispatch and exact conservative integer envelope; not near-boundary/randomgraph proof or runtime128 switching on MMC.'),indent=2)+'\n');print('MMC WIDTH BOUNDS PASS',rows)

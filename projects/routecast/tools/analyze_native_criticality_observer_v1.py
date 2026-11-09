"""Descriptive per-NET variation; no fitted global weight for the predictor."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_criticality_observer_v1_2026-10-10';proof=O/'verification.json';v=json.loads(proof.read_text());assert v['all115572_native_NET_local_pin_criticalities_observed'] and v['route_bytes_equal_fully_audited_cold'] and all(sha(p)==h for p,h in v['bindings'].items())
first={};last={}
for line in (O/'criticality.tsv').read_text().splitlines():
 x=line.split();key=int(x[2]),int(x[4]);value=float(x[5]);first.setdefault(key,value);last[key]=value
assert len(first)==115572
groups=defaultdict(list)
for (net,pin),value in first.items():groups[net].append(value)
multi=[values for values in groups.values() if len(values)>1];varying=sum(max(values)-min(values)>1e-6 for values in multi)
rows=[]
for label,select in [('1',lambda n:n==1),('2-4',lambda n:2<=n<=4),('5-16',lambda n:5<=n<=16),('17+',lambda n:n>=17)]:
 nets=[values for values in groups.values() if select(len(values))];values=[x for row in nets for x in row]
 rows.append(dict(fanout_group=label,nets=len(nets),connections=len(values),first_call_mean=sum(values)/len(values) if values else None,nets_with_first_call_spread_over_1e_6=sum(max(x)-min(x)>1e-6 for x in nets)))
bindings={**v['bindings'],str(proof):sha(proof),str(Path(__file__).resolve()):sha(Path(__file__))};assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,nets=len(groups),multi_sink_nets=len(multi),multi_sink_nets_with_nonconstant_first_criticality=varying,fanout_groups=rows,first_call_mean=sum(first.values())/len(first),last_call_mean=sum(last.values())/len(last),scope='Observed first/last call per pin, not explicitly tagged routing iterations or product STA. Per-NET variation indicates a fixed global objective is a simplification, not a causal proof or fitted replacement. Fanout groups use pin count, not unique RR targets.')
(O/'variation_analysis.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','scope']})

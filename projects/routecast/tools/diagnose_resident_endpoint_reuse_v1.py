"""Complete endpoint reuse census, without querying outcomes or claiming cache gain."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
P=R/'experiments/resident_radix_count_complete_v4_2026-10-08/protocol.json'
p=json.loads(P.read_text());assert all(sha(k)==h for k,h in p['bindings'].items())
bindings={str(P):sha(P),str(Path(__file__)):sha(Path(__file__))};rows=[]
for case in p['cases']:
 path=Path(case['endpoint']);bindings[str(path)]=sha(path);ep=json.loads(path.read_text());groups=defaultdict(list)
 for q in ep['connections']:groups[q['net_id']].append(q)
 sources=Counter();single_sinks=Counter();targetsets=Counter();fanouts=Counter()
 for net,qs in groups.items():
  src={q['source'] for q in qs};assert len(src)==1
  source=next(iter(src));targets=tuple(sorted({q['sink'] for q in qs}));sources[source]+=1;targetsets[targets]+=1;fanouts[len(targets)]+=1
  if len(targets)==1:single_sinks[targets[0]]+=1
 single_count=sum(single_sinks.values())
 rows.append(dict(name=case['name'],connections=len(ep['connections']),nets=len(groups),distinct_sources=len(sources),nets_sharing_source=sum(v for v in sources.values() if v>1),nets_by_distinct_target_count=dict(sorted(fanouts.items())),single_target_nets=single_count,distinct_single_target_sinks=len(single_sinks),single_target_nets_with_repeated_sink=sum(v for v in single_sinks.values() if v>1),max_single_target_sink_reuse=max(single_sinks.values(),default=0),distinct_complete_target_sets=len(targetsets),max_complete_target_set_reuse=max(targetsets.values(),default=0)))
assert all(sha(k)==h for k,h in bindings.items())
D=R/'experiments/resident_endpoint_reuse_census_v1_2026-10-08';D.mkdir(exist_ok=False)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Complete immutable endpoint structural census. Repeated SINK/target sets are physical class endpoints, not proof of common legal pins or reusable complete forward trees. No reverse-search operation savings, timing, new model or heldout proof.'),indent=2)+'\n')
print(json.dumps([{k:v for k,v in row.items() if k!='nets_by_distinct_target_count'} for row in rows],indent=2))

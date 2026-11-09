"""Input/prediction-only owner index and affected-scope diagnosis."""
import json,time
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_ram_length_switch_prediction_v1_2026-10-09'
D=E/'full_ram_affected_scope_v1_2026-10-09';D.mkdir(exist_ok=False)
r=json.loads((B/'receipt.json').read_text());assert r['status']=='COMPLETE_AUDITED_PREDICTION'
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
prediction=B/'prediction.json';pred=json.loads(prediction.read_text())
bindings={str(p):sha(p) for p in [Path(__file__),B/'receipt.json',prediction,B/'net_results.jsonl',B/'csr/manifest.json',R/'tools/prepared_csr.py']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
    rules=['all overloaded nodes','overloaded CHANX/CHANY only','top20 overloaded nodes ordered by excess then raw node ID'],
    scope='Prediction-only fixed-context reverse ownership; no target route/labels/metrics read. Affected scope is not equivalence to globally reoptimized pressure search or measured incremental speedup.'),indent=2)+'\n')
t=time.perf_counter();m,f=read(B/'csr',pred['physical_graph_sha256'])
ids=f['node_ids'];rank={n:i for i,n in enumerate(ids)};dest=[None]*m['edges']
for slot,eid in enumerate(f['edge_ids']):dest[eid]=ids[f['dest_ranks'][slot]]
owners=defaultdict(set);users=defaultdict(set);refs=Counter();net_connections=defaultdict(set)
for c in pred['connections']:
    assert c['physical_edge_ids'] is not None
    nodes={c['source'],*(dest[eid] for eid in c['physical_edge_ids'])}
    net_connections[c['net_id']].add(c['connection_id'])
    for n in nodes:owners[n].add(c['net_id']);users[n].add(c['connection_id']);refs[n]+=1
assert {str(n):len(v) for n,v in owners.items()}==pred['node_occupancy']
over={n:len(v)-f['capacities'][rank[n]] for n,v in owners.items() if len(v)>f['capacities'][rank[n]]}
assert len(over)==10003 and sum(over.values())==13718
visits={}
for line in (B/'net_results.jsonl').read_text().splitlines():
    row=json.loads(line);visits[row['net_id']]=row['result']['edge_visits']
rules={'all_overloaded':set(over),'channel_overloaded':{n for n in over if f['types'][rank[n]] in (4,5)},
    'top20_overloaded':set(sorted(over,key=lambda n:(-over[n],n))[:20])}
results=[]
for name,nodes in rules.items():
    nets=set().union(*(owners[n] for n in nodes));affected=set().union(*(users[n] for n in nodes))
    fullnet=set().union(*(net_connections[n] for n in nets))
    results.append(dict(rule=name,overloaded_nodes=len(nodes),affected_connections=len(affected),affected_nets=len(nets),
        complete_affected_net_connections=len(fullnet),connection_fraction=len(affected)/pred['requested'],
        old_search_edge_visits_in_affected_nets=sum(visits[n] for n in nets),total_old_search_edge_visits=sum(visits.values()),
        scope='Old frontier-work accounting only, not measured repair cost or dirty-only/global optimization equivalence.'))
out=dict(passed=True,results=results,unique_net_node_touches=sum(map(len,owners.values())),connection_node_touches=sum(refs.values()),
    avoided_same_net_duplicate_touches=sum(refs.values())-sum(map(len,owners.values())),index_and_analysis_s=time.perf_counter()-t,bindings=bindings)
(D/'diagnosis.json').write_text(json.dumps(out,indent=2)+'\n')
(D/'overloaded_owners.json').write_text(json.dumps({str(n):dict(excess=over[n],nets=sorted(owners[n]),connections=sorted(users[n])) for n in sorted(over)},indent=2)+'\n')
print(results)

"""Independent complete-cohort equality and CSR physical ledger reconstruction."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from prepared_csr import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';kind=sys.argv[1];assert kind in ('validated','swap');cid=int(sys.argv[2]);assert cid in ((0,1,2) if kind=='validated' else (1,2))
D=E/f'full_ram_search_equivalence_verification_v1_2026-10-09/{kind}_{cid}';D.mkdir(parents=True,exist_ok=False)
P=E/f"{'full_ram_validated_once_full_search_v1_2026-10-09' if kind=='validated' else 'full_ram_swap_full_search_v1_2026-10-09'}/candidate_{cid}"
B=E/'full_ram_length_switch_prediction_v1_2026-10-09';reference=B/'prediction.json' if cid==0 else E/f'full_ram_swap_incremental_v1_2026-10-09/candidate_{cid}/prediction.json'
r=json.loads((P/'receipt.json').read_text());assert r['status']=='COMPLETE_AUDITED_PREDICTION'
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
proof=E/'full_ram_length_switch_csr_verification_v1_2026-10-09/verification.json';v=json.loads(proof.read_text());assert v['passed']
for p,h in v['bindings'].items():assert sha(p)==h
pred=json.loads((P/'prediction.json').read_text());old=json.loads(reference.read_text());expected={c['connection_id']:c for c in old['connections']};assert len(expected)==16819
m,f=read(B/'csr',pred['physical_graph_sha256']);assert m['context_sha256']==r['details']['csr_context_sha256']
ids=f['node_ids'];rank={n:i for i,n in enumerate(ids)};arcs={}
for i,n in enumerate(ids):
 for slot in range(f['row_offsets'][i],f['row_offsets'][i+1]):arcs[f['edge_ids'][slot]]=(n,ids[f['dest_ranks'][slot]],f['costs'][slot])
net_nodes=defaultdict(set);seen=set()
for c in pred['connections']:
 cid=c['connection_id'];assert cid not in seen;seen.add(cid);prior=expected[cid]
 assert all(c[k]==prior[k] for k in ('net_id','source','sink','physical_edge_ids'))
 current=c['source'];nodes={current}
 for eid in c['physical_edge_ids']:
  a,b,w=arcs[eid];assert a==current and b not in nodes and w!=(1<<64)-1 and f['capacities'][rank[b]]>0;current=b;nodes.add(b)
 assert current==c['sink'];net_nodes[c['net_id']].update(nodes)
assert seen==set(expected)
occupancy={str(n):v for n,v in Counter(n for ns in net_nodes.values() for n in ns).items()};assert occupancy==pred['node_occupancy']==old['node_occupancy']
journal=[json.loads(x) for x in (P/'net_results.jsonl').read_text().splitlines()];assert len(journal)==5794 and len({x['net_id'] for x in journal})==5794
assert sum(x['result']['edge_visits'] for x in journal)==r['details']['edge_visits']
assert sum(x['result']['settled_nodes'] for x in journal)==r['details']['settled_nodes']
if cid==0:
 ref={x['net_id']:x['result'] for x in map(json.loads,(B/'net_results.jsonl').read_text().splitlines())}
 for x in journal:assert x['result']==ref[x['net_id']]
out=dict(passed=True,connections=len(seen),nets=len(journal),all_paths_and_complete_occupancy_equal=True,baseline_per_net_counters_equal=cid==0,bindings={str(p):sha(p) for p in [Path(__file__),P/'receipt.json',P/'prediction.json',P/'net_results.jsonl',reference,proof,B/'csr/manifest.json']},scope='Independent full cohort/path equality and authenticated CSR physical ledger reconstruction. No different cost-context/dynamic pressure equivalence, native route-tree legality or matched performance claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS',kind,sys.argv[2],len(seen),len(journal))

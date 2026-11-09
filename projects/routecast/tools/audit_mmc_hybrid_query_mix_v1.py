"""Authenticated input query mix; no measured search-work attribution."""
import json
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/ultraembedded_mmc_continuous_workflow_v7_2026-10-09';V=D/'verification.json';v=json.loads(V.read_text());assert v['all_cases_both_complete_arms_authenticated'];M=D/'seed/model/mmc/receipt.json';assert sha(M)==v['bindings'][str(M)];m=json.loads(M.read_text());P=next(Path(p) for p in m['bindings'] if p.endswith('/endpoints.json'));assert sha(P)==m['bindings'][str(P)];ep=json.loads(P.read_text());groups=defaultdict(list)
for q in ep['connections']:groups[q['net_id']].append(q)
assert len(ep['connections'])==115572
rows=defaultdict(lambda:dict(nets=0,connections=0,unique_sink_targets=0));hist=Counter()
for net,qs in groups.items():
 assert len({q['source'] for q in qs})==1
 targets=len({q['sink'] for q in qs});hist[targets]+=1;kind='singleton_bidirectional' if targets==1 else 'multitarget_forward';r=rows[kind];r['nets']+=1;r['connections']+=len(qs);r['unique_sink_targets']+=targets
assert sum(r['connections'] for r in rows.values())==115572
O=R/'experiments/mmc_hybrid_query_mix_v1_2026-10-09';O.mkdir(exist_ok=True)
out=dict(bindings={str(p):sha(p) for p in [V,M,P,Path(__file__),R/'tools/hybrid_bidirectional_search_v1.py']},initial_query_groups=dict(rows),targets_per_net_histogram=dict(sorted(hist.items())),scope='Original initial query mix from certified MMC v7 input. Dispatch determined by distinct sink count as implemented. Does not attribute elapsed time, settled nodes or edge relaxations; The current producer searches whole affected NETs in feedback, so per-NET branch remains fixed while the selected NET mix can change. Not unseen-family, optimality or gain proof.')
(O/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['initial_query_groups'],indent=2))

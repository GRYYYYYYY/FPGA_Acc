"""Source- and log-grounded reuse audit of the existing measured processes."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];src=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route';rr=src/'rr_graph.cpp';common=src/'route_common.cpp';assert 'skipping RR graph rebuild' in rr.read_text();assert 'reset_rr_node_route_structs();' in common.read_text()
parent=root/'experiments/native_candidate_retention_benchmark_2026-10-06';receipt=json.loads((parent/'receipt.json').read_text());verify=json.loads((parent/'verification.json').read_text());assert all(sha(p)==h for p,h in verify['sha256'].items());out=root/'experiments/native_initialization_reuse_audit_2026-10-06';out.mkdir();rows=[]
for x in receipt['runs']:
 name=f"{x['design']}_{x['repeat']}_{x['mode']}";p=parent/name/'run.log';log=p.read_text();assert sha(p)==x['log_sha256'];skips=log.count('RR graph channel widths unchanged, skipping RR graph rebuild');lookaheads=len(re.findall(r'^# Computing router lookahead map$',log,re.M));assert skips==5 and lookaheads==1
 stages={}
 for label in ('Loading Architecture Description','Building complex block graph','Load packing','Create Device','Computing router lookahead map'):
  found=re.search(r'^# '+re.escape(label)+r' took ([0-9.]+) seconds',log,re.M);assert found;stages[label]=float(found[1])
 rows.append({'design':x['design'],'mode':x['mode'],'repeat':x['repeat'],'rr_rebuild_skips':skips,'lookahead_computations':lookaheads,'reported_initialization_stages_s':stages,'log_sha256':sha(p)})
(out/'receipt.json').write_text(json.dumps({'runs':rows,'sources_sha256':{str(p):sha(p) for p in (rr,common)},'benchmark_verification_sha256':sha(parent/'verification.json'),'scope':'Native source and archived logs prove five RR rebuild skips and one lookahead calculation in each process. Reported setup timers are rounded and potentially nested; not a sum decomposition of process time. Does not imply mutable endpoint/cost state can be reused unchanged.'},indent=2)+'\n');print('verified reuse in',len(rows),'processes')

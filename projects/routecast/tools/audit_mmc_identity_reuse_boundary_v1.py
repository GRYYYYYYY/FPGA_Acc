"""Inspect pre/post-routing identity boundaries of an authenticated complete trial."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];P=R/'experiments/ultraembedded_mmc_continuous_workflow_v7_2026-10-09';V=P/'verification.json';v=json.loads(V.read_text());assert v['all_cases_both_complete_arms_authenticated'];assert all(sha(p)==h for p,h in v['bindings'].items())
bindings={str(V):sha(V),str(Path(__file__)):sha(Path(__file__))};rows=[]
for arm in ['cold','seed']:
 pre=P/arm/'demand/mmc';post=P/arm/'canonical/mmc';native=P/arm/'native/mmc'
 paths=[pre/'identity.jsonl',post/'identity.jsonl',pre/'design.net',native/'design.net.post_routing',post/'design.net']
 bindings.update({str(p):sha(p) for p in paths});before,after=[{r['name']:r for r in map(json.loads,p.read_text().splitlines())} for p in paths[:2]]
 common=set(before)&set(after);changed=[name for name in common if before[name]!=after[name]]
 assert sha(paths[3])==sha(paths[4])
 rows.append(dict(arm=arm,packed_bytes_identical=sha(paths[2])==sha(paths[3]),native_identity_bytes_identical=sha(paths[0])==sha(paths[1]),before_nets=len(before),after_nets=len(after),common_nets=len(common),changed_common_identity_records=len(changed),removed_names=len(set(before)-set(after)),added_names=len(set(after)-set(before))))
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/mmc_identity_reuse_boundary_v1_2026-10-09';D.mkdir(exist_ok=True);out=dict(bindings=bindings,rows=rows,decision='Reuse must be keyed to exact packed netlist, placement, native binary/options and architecture. Equal placement alone is insufficient. Keep post-routing identity capture whenever packed bytes change; no skip authorized by this inspection.',scope='Boundary inspection on completed MMC v7. No historical identity cache used in v8, no new complete workflow or speedup proof; any candidate reuse needs exact semantic and independent validation.')
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))

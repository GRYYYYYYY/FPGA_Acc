"""Preselect frozen high-fanout feedback cohort from pre-route endpoints only."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
root=Path('experiments/stereo_prospective_validation_2026-10-05');out=root/'incremental_cohort.json'
if out.exists():raise ValueError('fresh cohort required')
policy=json.loads((root/'protocol.json').read_text());ep=root/'endpoints/endpoints.json';receipt=json.loads((root/'endpoints/receipt.json').read_text());assert sha(ep)==receipt['output_sha256']['endpoints.json'];e=json.loads(ep.read_text())
rows=e['connections'];assert len(rows)==81640 and len({r['connection_id'] for r in rows})==81640
threshold=policy['policy']['fanout_threshold'];assert threshold==64
fanout=Counter(r['net_id'] for r in rows);selected=sorted(n for n,k in fanout.items() if k>=threshold);groups=defaultdict(list)
for r in sorted(rows,key=lambda r:(r['net_id'],r['connection_id'])):
 if r['net_id'] in selected:groups[r['net_id']].append(r)
cohort=[]
for net in selected:
 sources={r['source'] for r in groups[net]};assert len(sources)==1
 cohort.append({'net_id':net,'source':next(iter(sources)),'fanout':fanout[net],'distinct_sink_classes':len({r['sink'] for r in groups[net]}),'connection_ids':[r['connection_id'] for r in groups[net]]})
result={'endpoints_sha256':sha(ep),'policy_sha256':sha(root/'protocol.json'),'source_sha256':sha(__file__),'fanout_threshold':threshold,'total_connections':len(rows),'total_nets':len(fanout),'selected_nets':len(selected),'selected_connections':sum(r['fanout'] for r in cohort),'ordered_cohort':cohort,'label_cap':policy['policy']['label_cap'],'budget':policy['policy']['budget'],'pin_policy':policy['policy']['pin_policy'],'commit_policy':policy['policy']['commit'],'scope':'pre-route endpoint-only frozen target cohort; feasibility/path budgets and feedback outcomes unknown; not full mechanism execution'}
out.write_text(json.dumps(result,indent=2)+'\n');assert sha(ep)==receipt['output_sha256']['endpoints.json'];print(json.dumps({k:v for k,v in result.items() if k!='ordered_cohort'}),flush=True)

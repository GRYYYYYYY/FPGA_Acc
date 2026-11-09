"""Freeze pool feedback rule and generate all six real-move payloads before routing."""
import json,shutil
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from prepared_csr import read
from pooled_channel_pressure import rows,payload,KEYS

base=Path('experiments');out=base/'multiplier_pooled_pressure_2026-10-06';out.mkdir();(out/'source').mkdir()
for name in ('prepare_multiplier_pooled_pressure.py','pooled_channel_pressure.py','prepared_csr.py','pre_route_endpoints.py'):shutil.copyfile(Path('tools')/name,out/'source'/name)
protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'group_keys':KEYS,'rule':'every eligible node in group receives acc_cost=1+sum(max(occupancy-capacity,0))/sum(capacity), coefficient1','labels':'authenticated pre-route moved prediction only; no native route input','scope':'development alternative to exact-track pressure; full producer cost not incremental, not a holdout or target-budget guarantee','sources_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
for design in protocol['cohort']:
 root=base/'multiplier_moved_incremental_search_2026-10-06'/design;r=json.loads((root/'receipt.json').read_text());assert sha(root/'prediction.json')==r['prediction_sha256'] and r['paths_equal_full_moved_search'];assert all(sha(p)==h for p,h in r['inputs_sha256'].items());pred=json.loads((root/'prediction.json').read_text());prepared=base/'multiplier_family_length_switch_csr_2026-10-06'/design;pr=json.loads((prepared/'receipt.json').read_text());assert sha(prepared/'csr/manifest.json')==pr['manifest_sha256'];m,f=read(prepared/'csr',pred['physical_graph_sha256']);assert all(i==v for i,v in enumerate(f['node_ids']))
 pressure,proofs=rows(f,{int(n):v for n,v in pred['node_occupancy'].items()});assert pressure and sum(cap*(value-1) for cap,value in pressure.values())==sum(p['excess'] for p in proofs)
 case=out/design;case.mkdir();(case/'candidate.pressure').write_text(payload(m['nodes'],pred['physical_graph_sha256'],pressure));(case/'pool_proofs.json').write_text(json.dumps(proofs,indent=2)+'\n');receipt={'protocol_sha256':sha(out/'protocol.json'),'prediction_receipt_sha256':sha(root/'receipt.json'),'prediction_sha256':sha(root/'prediction.json'),'csr_receipt_sha256':sha(prepared/'receipt.json'),'pressure_rows':len(pressure),'active_pools':len(proofs),'exact_weighted_excess':sum(p['excess'] for p in proofs),'pressure_sha256':{'candidate.pressure':sha(case/'candidate.pressure')},'proofs_sha256':sha(case/'pool_proofs.json')};(case/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');results.append({'design':design,**receipt});print(json.dumps({'design':design,'rows':len(pressure),'pools':len(proofs),'excess':receipt['exact_weighted_excess']}),flush=True)
assert all(sha(out/'source'/name)==h for name,h in protocol['sources_sha256'].items())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results,'scope':protocol['scope']},indent=2)+'\n')

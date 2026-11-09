"""Apply structural union diagnostic to nine independently audited sketches."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from net_union_topology import diagnose
root=Path('experiments/frisc_topology_backgrounds_2026-10-05');out=Path('experiments/frisc_union_topology_diagnostic_2026-10-05')
if out.exists():raise ValueError('fresh output required')
a=json.loads((root/'independent_audit.json').read_text());ep=json.loads(Path('experiments/frisc_endpoints_2026-10-05/endpoints.json').read_text());entry=ep['inputs']['graph'];assert sha(entry['path'])==entry['sha256'];assert a['receipt_sha256']==sha(root/'receipt.json');start=time.monotonic();g=read_rr_graph(entry['path']);rows=[];hashes={str(root/'independent_audit.json'):sha(root/'independent_audit.json'),entry['path']:entry['sha256']}
for r in a['reports']:
 cid=r['candidate_id'];file=root/('baseline_prediction.json' if cid==0 else f'candidate_{cid}_prediction.json');assert sha(file)==r['prediction_sha256'] and r['physical_audit']['all_physical_and_union_checks_passed'];hashes[str(file)]=sha(file)
 report=diagnose(g,json.loads(file.read_text()));rows.append({'candidate_id':cid,'report':report})
assert all(sha(p)==h for p,h in hashes.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'net_union_topology.py').write_text(Path('tools/net_union_topology.py').read_text());receipt={'rows':rows,'input_sha256':hashes,'source_sha256':sha(__file__),'module_sha256':sha('tools/net_union_topology.py'),'wall_s':time.monotonic()-start,'limitations':['structural union only, no pin instance identity or complete VPR legality','SINK incoming multiplicity can represent distinct terminal occurrences']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps([{'candidate_id':r['candidate_id'],**{k:v for k,v in r['report'].items() if k not in ('nets','scope')}} for r in rows]))

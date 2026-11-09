"""Frozen Koios native full-branch audit and exact frontend endpoint join."""
import json,time,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from stream_native_route_audit import audit
out=Path('experiments/koios_spmv_native_path_audit_2026-10-04');cap=Path('experiments/koios_spmv_cost_binding_2026-10-04');front=Path('experiments/koios_spmv_endpoints_v2_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((cap/'protocol.json').read_text());r=json.loads((cap/'receipt.json').read_text());fr=json.loads((front/'receipt.json').read_text());assert r['exit_code']==0 and fr['outputs']['endpoints.json']==sha(front/'endpoints.json')
inputs={'graph':{'path':str((cap/'rr_graph.xml').resolve()),'sha256':r['outputs']['rr_graph.xml']},'route':p['inputs']['route'],'place':p['inputs']['place'],'endpoints':{'path':str((front/'endpoints.json').resolve()),'sha256':fr['outputs']['endpoints.json']}};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'all printed native branches, physical nodes/arcs/switches and unique-net occupancy; frontend exactendpoint multiset; not predictor accuracy/new routing QoR','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();result=audit(inputs['graph']['path'],inputs['route']['path']);frontend=json.loads(Path(inputs['endpoints']['path']).read_text());expected=Counter((v['net_id'],v['source'],v['sink']) for v in frontend['connections']);actual=Counter((v['net_id'],v['source'],v['sink']) for v in result['connections']);assert actual==expected
assert f"Placement_ID: SHA256:{inputs['place']['sha256']}" in Path(inputs['route']['path']).read_text().splitlines()[0];assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'native.json').write_text(json.dumps(result)+'\n');receipt={'protocol_sha256':sha(out/'protocol.json'),'exact_15138_endpoint_multiset':True,'all_printed_branch_arc_switch_and_union_checks_pass':True,'wall_s':time.monotonic()-start,'inputs_unchanged':True,'native_sha256':sha(out/'native.json'),'physical_edge_count':result['physical_edge_count'],'occupied_nodes':result['occupied_nodes'],'routed_nets':result['routed_nets'],'overflow_units':result['overflow_units']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

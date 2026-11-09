"""Frozen full stereo additive transport preparation; no route labels consumed."""
import json,time,resource,shutil,sys
from pathlib import Path
from pre_route_endpoints import sha
base=Path('experiments/stereo_prospective_validation_2026-10-05')
root=base/'streaming_csr_class_cache_v3'
if root.exists():raise ValueError('fresh output required')
clma=Path('experiments/clma_class_cache_csr_2026-10-05')
r=json.loads((clma/'receipt.json').read_text())
assert r['all_manifest_fields_exact'] and r['all_binary_bytes_exact']
assert r['protocol_sha256']==sha(clma/'protocol.json') and r['manifest_sha256']==sha(clma/'csr/manifest.json')
p=json.loads((base/'protocol.json').read_text());binding=json.loads((base/'cost_binding_audit/receipt.json').read_text())
assert binding['all_native_node_bindings_verified']
inputs={'graph':p['inputs']['graph'],'table':{'path':str((base/'native_cost_binding/rr_indexed_data.echo').resolve()),'sha256':binding['identity']['table_sha256']},'bindings':{'path':str((base/'native_cost_binding/routecast_node_cost_indices.csv').resolve()),'sha256':binding['identity']['bindings_sha256']}}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
root.mkdir();(root/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,root/'source'/f.name)
shutil.copyfile(__file__,root/'driver.py')
protocol={'inputs':inputs,'identity':binding['identity'],'scale':10**6,'class_cache':True,'clma_receipt_sha256':sha(clma/'receipt.json'),'source_sha256':{f.name:sha(f) for f in (root/'source').glob('*.py')},'scope':'full exact additive CSR preparation; not tree budget/free-pin mechanism, prediction, QoR or hardware validation'}
(root/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
sys.path.insert(0,str((root/'source').resolve()))
from streaming_bound_csr import convert
start=time.monotonic()
m=convert(inputs['graph']['path'],Path(inputs['table']['path']).read_text(),Path(inputs['bindings']['path']).read_text(),binding['identity'],root/'csr',class_cache=True)
audit=json.loads((base/'graph_readiness.json').read_text())
assert m['nodes']==audit['nodes'] and m['edges']==audit['edges']
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
assert all(sha(root/'source'/n)==h for n,h in protocol['source_sha256'].items())
result={'nodes':m['nodes'],'edges':m['edges'],'wall_s':time.monotonic()-start,'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'manifest_sha256':sha(root/'csr/manifest.json'),'protocol_sha256':sha(root/'protocol.json'),'payload_bytes':sum(f['bytes'] for f in m['files'].values()),'inputs_unchanged':True,'scope':protocol['scope']}
(root/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

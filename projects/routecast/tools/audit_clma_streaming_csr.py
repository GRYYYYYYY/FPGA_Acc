"""Real graph streaming conversion vs archived, previously roundtripped CSR."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from streaming_bound_csr import convert
root=Path('experiments/clma_streaming_csr_2026-10-05')
if root.exists():raise ValueError('fresh output required')
reference=Path('experiments/clma_prepared_csr_2026-10-04')
protocol=json.loads((reference/'protocol.json').read_text());receipt=json.loads((reference/'receipt.json').read_text())
assert receipt['complete_topology_rawID_switch_capacity_cost_roundtrip']
assert receipt['protocol_sha256']==sha(reference/'protocol.json')
assert receipt['manifest_sha256']==sha(reference/'csr/manifest.json')
manifest=json.loads((reference/'csr/manifest.json').read_text());inputs=protocol['inputs']
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
for spec in manifest['files'].values():assert sha(reference/'csr'/spec['file'])==spec['sha256']
root.mkdir();(root/'source').mkdir()
modules=['streaming_bound_csr','streaming_rr_nodes','streaming_cached_arc_cost','streaming_csr_builder','bound_indexed_cost','prepared_csr','path_rc','pre_route_endpoints']
for module in modules:shutil.copyfile(Path('tools')/(module+'.py'),root/'source'/(module+'.py'))
shutil.copyfile(__file__,root/'driver.py')
freeze={'inputs':inputs,'reference_manifest_sha256':sha(reference/'csr/manifest.json'),'reference_receipt_sha256':sha(reference/'receipt.json'),'source_sha256':{p.name:sha(p) for p in (root/'source').glob('*.py')},'scope':'full real clma fields vs archived old conversion; no search/QoR or speed comparison'}
(root/'protocol.json').write_text(json.dumps(freeze,indent=2)+'\n')
start=time.monotonic()
actual=convert(inputs['graph']['path'],Path(inputs['table']['path']).read_text(),Path(inputs['binding']['path']).read_text(),{'graph_sha256':inputs['graph']['sha256'],'table_sha256':inputs['table']['sha256'],'bindings_sha256':inputs['binding']['sha256']},root/'csr')
assert actual==manifest
# Compare bytes independently of both writers' manifests, using bounded chunks.
for spec in manifest['files'].values():
 with (root/'csr'/spec['file']).open('rb') as a,(reference/'csr'/spec['file']).open('rb') as b:
  while True:
   x=a.read(1<<20);y=b.read(1<<20);assert x==y,spec['file']
   if not x:break
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
result={'nodes':actual['nodes'],'edges':actual['edges'],'all_manifest_fields_exact':True,'all_binary_bytes_exact':True,'inputs_unchanged':True,'wall_s':time.monotonic()-start,'protocol_sha256':sha(root/'protocol.json'),'manifest_sha256':sha(root/'csr/manifest.json'),'scope':freeze['scope']}
(root/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

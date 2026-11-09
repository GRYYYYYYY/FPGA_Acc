"""Independent native endpoint multiset comparison; not an arc/path audit."""
import json,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
parent=Path('experiments/koios_spmv_endpoints_2026-10-04');out=Path('experiments/koios_spmv_endpoint_audit_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());assert r['protocol_sha256']==sha(parent/'protocol.json') and r['outputs']['endpoints.json']==sha(parent/'endpoints.json')
cap=json.loads(Path('experiments/koios_spmv_cost_binding_2026-10-04/protocol.json').read_text());inputs={'endpoints':{'path':str((parent/'endpoints.json').resolve()),'sha256':r['outputs']['endpoints.json']},'route':cap['inputs']['route'],'place':cap['inputs']['place']};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();(out/'source').mkdir()
for f in (Path(__file__),Path(__file__).with_name('audit_native_route.py'),Path(__file__).with_name('pre_route_endpoints.py')):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'native endpoint multiset only; no graph arc, tree, occupancy or predictor accuracy claim','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');frontend=json.loads(Path(inputs['endpoints']['path']).read_text());expected=Counter((v['net_id'],v['source'],v['sink']) for v in frontend['connections']);native=Counter();net=None;source=None;names={}
lines=Path(inputs['route']['path']).read_text().splitlines();assert f"Placement_ID: SHA256:{inputs['place']['sha256']}" in lines[0]
for line in lines:
 m=NET.match(line)
 if m:net=int(m[1]);source=None;names[net]=m[2]
 m=NODE.match(line)
 if m:
  if m[2]=='SOURCE':source=int(m[1])
  if m[2]=='SINK':
   if net is None or source is None:raise ValueError('sink without source/net')
   native[(net,source,int(m[1]))]+=1
 elif line.lstrip().startswith('Node:'):raise ValueError('unparsed native node')
missing=expected-native;extra=native-expected
report={'protocol_sha256':sha(out/'protocol.json'),'expected_connections':sum(expected.values()),'native_connections':sum(native.values()),'endpoint_multiset_exact':expected==native,'missing':[{ 'net_source_sink':k,'count':v,'native_name':names.get(k[0])} for k,v in missing.items()],'extra':[{ 'net_source_sink':k,'count':v,'native_name':names.get(k[0])} for k,v in extra.items()],'inputs_unchanged':all(sha(v['path'])==v['sha256'] for v in inputs.values()),'scope':'endpoints only; physical arc/path audit remains required'};(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('expected_connections','native_connections','endpoint_multiset_exact')}),flush=True)
if expected!=native:raise SystemExit(1)

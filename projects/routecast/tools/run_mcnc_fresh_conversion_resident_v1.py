"""Fresh packedNET/place/RR endpoint conversion plus one actual resident estimator process."""
import sys,json,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
out=R/'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07';out.mkdir();sources=closure([Path(__file__),R/'tools/run_resident_soft_demand_v1.py']);inputs={};names=['bigkey','dsip','misex3']
for name in names:
 ep=R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json';inputs[str(ep)]=sha(ep);inputs.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
(out/'protocol.json').write_text(json.dumps(dict(bindings={**sources,**inputs},order=names,rounds=2,price_unit_ns='1/20',scope='Serial fresh endpoint extraction from fixed packedNET/place/original RR, fresh floors and initial plus two feedback rounds in one model process. No archived floors/sketch/native labels in child estimator. Original endpoints used only by outer conversion identity check. Child whole process wall includes receipt finalization. Native routing, upstream pack/place/RR generation, compilation and independent post-audit excluded; not full workflow net-gain.'),indent=2)+'\n');rows=[]
for name in names:
 begin=time.perf_counter();w=out/name;w.mkdir();oldfile=R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json';old=json.loads(oldfile.read_text());tick=time.perf_counter();ep,mapping=extract(*(Path(old['inputs'][key]['path']) for key in ['net','place','graph']));assert ep['connections']==old['connections'] and ep['graph_sha256']==old['graph_sha256'] and ep['clock_policy']==old['clock_policy'] and ep['net_names']==old['net_names'];epfile=w/'endpoints.json';epfile.write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n');conversion=time.perf_counter()-tick;tick=time.perf_counter()
 with (w/'resident.log').open('w') as log:status=subprocess.run([sys.executable,str(R/'tools/run_resident_soft_demand_v1.py'),str(epfile),str(w/'resident')],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 row=dict(name=name,exit_code=status,connections=len(ep['connections']),fresh_conversion_seconds=conversion,resident_process_wall_seconds=time.perf_counter()-tick,conversion_plus_resident_wall_seconds=time.perf_counter()-begin);rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('FRESH RESIDENT',row,flush=True)
 if status:raise RuntimeError('Retained failed case; stopped before any benefit claim')
assert all(sha(k)==h for k,h in {**sources,**inputs}.items());(out/'receipt.json').write_text(json.dumps(dict(bindings={**sources,**inputs},rows=rows,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')

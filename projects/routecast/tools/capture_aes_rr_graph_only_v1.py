"""Build RR via analysis missing-route stop; extract all fixed-placement endpoints, no labels."""
import sys,json,time,subprocess,shutil,os,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
src=R/'experiments/aes_native_fixed_place_v1_2026-10-08';p=json.loads((src/'protocol.json').read_text());r=json.loads((src/'receipt.json').read_text());assert sha(src/'protocol.json')==r['protocol_sha256'] and all(sha(k)==v for k,v in r['bindings'].items());out=R/'experiments/aes_rr_graph_only_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(src/'receipt.json'):sha(src/'receipt.json')};cases=[]
for row in r['rows']:
 name=row['name'];assert row['exit_code']==0 and all(sha(k)==v for k,v in row['files'].items());w=out/name;w.mkdir()
 for f in ['design.blif','design.net','design.place']:shutil.copyfile(src/name/f,w/f)
 cmd=next(c['command'] for c in p['cases'] if c['name']==name).copy();cmd.remove('--pack');cmd[cmd.index('--place')]='--analysis';cmd.extend(['--route_file','missing.route','--write_rr_graph','rr_graph.xml','--check_route','full']);cases.append({'name':name,'command':cmd});net=ET.parse(w/'design.net').getroot();assert net.get('architecture_id')=='SHA256:'+sha(cmd[1]) and net.get('atom_netlist_id')=='SHA256:'+sha(w/'design.blif')
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'cases':cases,'scope':'RR generation then expected missing-route analysis error. No native route labels, QoR or heldout result. Original mappedHDL relation proof separate. width128/seed1/worker1 frozen; all siblings retained, no graph/width retuning.'},indent=2)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[]
for c in cases:
 w=out/c['name'];tick=time.perf_counter();row={'name':c['name']}
 with (w/'graph.log').open('w') as log:
  try:code=subprocess.run(c['command'],cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row.update(exit_code=code,seconds=time.perf_counter()-tick,graph_exists=(w/'rr_graph.xml').exists())
 try:
  assert code==1 and row['graph_exists'] and not (w/'missing.route').exists();log=(w/'graph.log').read_text();assert 'missing.route' in log
  ep,mapping=extract(w/'design.net',w/'design.place',w/'rr_graph.xml');(w/'endpoints.json').write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n');row.update(status='GRAPH_AND_ENDPOINTS_CAPTURED',connections=len(ep['connections']),graph_sha256=ep['graph_sha256'])
 except Exception as error:row.update(status='REJECTED',error=repr(error))
 row['files']={str(f):sha(f) for f in w.iterdir() if f.is_file()};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(c['name'],row['status'],row.get('connections'),row.get('error'),flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n')

"""Audit whole-search CU traces and final shared-memory connectivity."""
from pathlib import Path
import argparse,json,hashlib,re,time,zipfile,xml.etree.ElementTree as ET
p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('build',type=Path);a=p.parse_args();out=a.run;build=a.build
m=json.loads((out/'manifest.json').read_text());assert m['returncode']==0;r=json.loads((out/'result.json').read_text());assert r['status']=='passed' and (r['commit_calls'],r['seed_calls'],r['snapshot_calls'],r['authority_reuploads'])==(12,2,2,0) and r['observations']==6 and r['path_costs']==[4,7] and r['published_path_verified'] and r['stale_validation_rejected']
log=(out/'run.log').read_text();ops=[1,2,2,2,3,3,6,5,6,6,3,7];commits=[tuple(map(int,x)) for x in re.findall(r'XRT net_commit call=(\d+) op=(\d+) status=(\d+).*total_authority_uploads=(\d+)',log)];assert commits==[(i+1,op,4 if i==8 else 0,0) for i,op in enumerate(ops)]
searches=[tuple(map(int,x)) for x in re.findall(r'XRT snapshot call=(\d+) epoch=(\d+) cost=(\d+) expanded=(\d+) edges=(\d+) used=(\d+)',log)];assert searches==[(1,3,4,4,3,3),(2,4,7,4,3,6)]
inputs=json.loads((out/'inputs.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items());image_hash=hashlib.sha256((build/'joint.xclbin').read_bytes()).hexdigest();assert image_hash==m['xclbin_sha256'];assert 'All the simulator processes exited successfully' in (out/'stdout.log').read_text()
ip=json.loads((build/'ip_layout.json').read_text())['ip_layout']['m_ip_data'];mem=json.loads((build/'memory.json').read_text())['mem_topology']['m_mem_data'];connections=json.loads((build/'connectivity.json').read_text())['connectivity']['m_connection'];cfg=dict(re.findall(r'^sp=(\w+\.\w+):HBM\[(\d+)\]$',(build/'connectivity.cfg').read_text(),re.M));assert {v['m_name'].split(':')[1] for v in ip}=={'net_commit','search_worker','snapshot_search'}
args={}
for short in ['commit','worker','snapshot']:
 with zipfile.ZipFile(build/(short+'.xo')) as z:
  root=ET.fromstring(z.read(next(p for p in z.namelist() if p.endswith('/kernel.xml'))));name=next(root.iter('kernel')).attrib['name'];args[name]={int(v.attrib['id']):v.attrib['name'] for v in root.iter('arg')}
seen=set()
for c in connections:
 kernel,cu=ip[int(c['m_ip_layout_index'])]['m_name'].split(':');key=cu+'.'+args[kernel][int(c['arg_index'])];assert key not in seen;seen.add(key);memory=mem[int(c['mem_data_index'])];assert memory['m_used']=='1' and memory['m_tag']=='HBM['+cfg[key]+']'
assert len(seen)==35 and seen==set(cfg)
paths=[out/'result.json',out/'run.log',out/'stdout.log',out/'inputs.json',out/'host',build/'ip_layout.json',build/'memory.json',build/'connectivity.json'];report={'status':'passed','verified_ns':time.time_ns(),'actual_cu_calls':16,'complete_search_calls':2,'pointer_connections':35,'result':r,'xclbin_sha256':image_hash,'evidence_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Whole-search CU using actual commit-owned resources, device authority byte preservation checks, consumed-read invalidation and path publication; serialized small fixture with negotiated overuse, not legal full-design route, asynchronous protocol or board proof','board_result':False,'research_complete':False};(out/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','actual_cu_calls':16,'complete_search_calls':2,'pointer_connections':35}))

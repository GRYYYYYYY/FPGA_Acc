"""Audit actual three-bank joined commit/seed/whole-search fixture execution."""
from pathlib import Path
import json,re,hashlib,sys,zipfile,subprocess
import xml.etree.ElementTree as ET
run,build=map(Path,sys.argv[1:3])
m=json.loads((run/'manifest.json').read_text());assert m['returncode']==0 and m['inputs_unchanged'] and not m['production_kernel_cpp_linked']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in m['inputs'].items():assert sha(Path(p))==h
assert sha(build/'joint.xclbin')==m['xclbin_sha256']
values=[json.loads(s) for s in (run/'stdout.log').read_text().splitlines() if s.startswith('{')];assert len(values)==1;r=values[0];assert r==m['result']
assert r['status']=='passed' and (r['commit_calls'],r['seed_calls'],r['snapshot_calls'],r['authority_reuploads'])==(12,2,2,0)
assert r['observations']==6 and r['path_costs']==[4,7] and r['published_path_verified'] and r['stale_validation_rejected']
log=(run/'run.log').read_text();ops=[1,2,2,2,3,3,6,5,6,6,3,7]
actual=[tuple(map(int,v)) for v in re.findall(r'XRT net_commit call=(\d+) op=(\d+) status=(\d+).*total_authority_uploads=(\d+)',log)]
assert actual==[(i+1,op,4 if i==8 else 0,0) for i,op in enumerate(ops)]
searches=[tuple(map(int,v)) for v in re.findall(r'XRT snapshot call=(\d+) epoch=(\d+) cost=(\d+) expanded=(\d+) edges=(\d+) used=(\d+)',log)]
assert searches==[(1,3,4,4,3,3),(2,4,7,4,3,6)]
a=json.loads((build/'group_audit/audit.json').read_text());assert a['status']=='sharded_groups_verified_runtime_ownership_pending' and a['pointer_arguments']==39
assert a['axi_master_counts']=={'commit':6,'worker':2,'snapshot':6}
groups=a['argument_group_ids']['dieroute_net_commit_sharded_hbm:net_commit'];lines=[s for s in log.splitlines() if s.startswith('XRT net commit groups:')];assert len(lines)==1;actual_groups=list(map(int,lines[0].split(':',1)[1].split()))
with zipfile.ZipFile(build/'commit.xo') as z:
 root=ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('/kernel.xml'))));args={int(v.attrib['id']):v.attrib['name'] for v in root.iter('arg') if v.attrib['addressQualifier']=='1'}
assert len(actual_groups)==17 and actual_groups==[groups[args[i]] for i in range(17)]
assert len({actual_groups[i] for i in [0,1,8,9,10,11]})==6
assert [actual_groups[i] for i in [8,9,10]]==[a['allocation_role_group_ids']['owner'+str(i)] for i in range(3)]
assert re.search(r'All (?:the )?simulator processes exited successfully',(run/'stdout.log').read_text())
symbols=subprocess.check_output(['nm','--defined-only',str(run/'host')],text=True)
assert not re.search(r'\bT dieroute_(?:net_commit_sharded_hbm|native_snapshot_search_sharded_hbm|native_search_worker_hbm)$',symbols,re.M)
report=dict(status='passed',actual_cu_calls=16,result=r,runtime_owner_groups=actual_groups[8:11],image_sha256=m['xclbin_sha256'],
 hashes={str(p):sha(p) for p in [run/'manifest.json',run/'host',run/'run.log',run/'stdout.log',build/'group_audit/audit.json']},
 scope='Actual banked commit/seed/whole-search CUs, shared owner BOs, runtime group checks, full authority preservation assertions and stale-read rejection/path publication; serialized small fixture with negotiated overuse',
 limitations=['No asynchronous owner protocol','No native full graph or workload QoR','No physical implementation or board result'],board_result=False)
(run/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status='passed',actual_cu_calls=16,runtime_owner_groups=actual_groups[8:11])))

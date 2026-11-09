"""Audit complete runtime BO coverage, groups, bounds and cross-bank markers."""
import hashlib,json,re,sys,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

run,build=map(Path,sys.argv[1:3])
m=json.loads((run/'manifest.json').read_text());assert m['returncode']==0 and m['inputs_unchanged']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in m['inputs'].items():assert sha(Path(p))==h
a=json.loads((build/'group_audit/audit.json').read_text());assert a['status']=='group_metadata_verified_runtime_allocation_pending'
domains=[tuple(int(x,0) for x in m['command'][2+i*3:5+i*3]) for i in range(3)]
arg_names={};names=['dieroute_native_snapshot_search_hbm:snapshot_search','dieroute_native_search_worker_hbm:search_worker','dieroute_net_commit_hbm:net_commit']
for i,short in enumerate(['snapshot','worker','commit']):
 with zipfile.ZipFile(build/(short+'.xo')) as z:
  xml=ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('/kernel.xml'))))
  arg_names[i]={int(v.attrib['id']):v.attrib['name'] for v in xml.iter('arg') if v.attrib['addressQualifier']=='1'}
expected={};seen=set()
for line in Path(m['command'][1]).read_text().splitlines():
 fields=line.split();name=fields[0];size,role,count=map(int,fields[1:4]);assert len(fields)==4+count*2 and name not in expected
 for j in range(count):
  kernel,arg=map(int,fields[4+j*2:6+j*2]);assert (kernel,arg) not in seen;seen.add((kernel,arg));assert a['argument_group_ids'][names[kernel]][arg_names[kernel][arg]]==domains[role][0]
 expected[name]=(size,role)
assert len(expected)==26 and seen=={(k,i) for k,args in arg_names.items() for i in args} and len(seen)==35
text=(run/'stdout.log').read_text();rows=re.findall(r'^BO name=(\w+) bytes=(\d+) group=(\d+) address=(\d+) markers=(\d+)$',text,re.M);assert len(rows)==26
seen_names=set();ranges=[];total=checks=0
for name,size,group,address,markers in rows:
 size,group,address,markers=map(int,(size,group,address,markers));assert name not in seen_names;seen_names.add(name);want,role=expected[name];domain,base,capacity=domains[role]
 assert size==want and group==domain and base<=address<=base+capacity-size
 for lo,hi in ranges:assert address+size<=lo or hi<=address
 ranges.append((address,address+size));points={0,(size-64)//64*64};bank=256*(1<<20)
 for boundary in range((address//bank+1)*bank,address+size,bank):
  offset=boundary-address
  if offset>=64:points.add(offset-64)
  if offset<=size-64:points.add(offset)
 assert markers==len(points);total+=size;checks+=markers
assert seen_names==set(expected)
matches=re.findall(r'^SNAPSHOT_ALLOCATION_PASS buffers=26 pointer_arguments=35 total_bytes=(\d+) markers=(\d+) kernel_launches=0 native_graph_uploaded=0$',text,re.M)
assert matches==[(str(total),str(checks))]
assert re.search(r'All (?:the )?simulator processes exited successfully',text+(run/'run.log').read_text())
report=dict(status='passed',buffers=26,pointer_arguments=35,total_bytes=total,markers=checks,
    scope='Actual XRT runtime groups, simultaneous full bounded BO allocations and synthetic cross-bank readbacks; no native payload upload or CU execution',board_result=False)
(run/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

"""Audit actual three-CU snapshot image bank groups and bounded buffer capacities."""
import json,re,subprocess,hashlib,zipfile,sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
def verify_sections(mem,ips,connections,groups,group_connections,expected):
 physical={}
 for entry in mem:
  match=re.fullmatch(r'HBM\[(\d+)\]',entry['m_tag'])
  if match:
   index=int(match[1]);assert index not in physical;physical[index]=entry
 assert set(physical)==set(range(32)) and all(int(x['m_sizeKB'],0)==256*1024 for x in physical.values())
 def members(entry):
  match=re.fullmatch(r'(?:HBM|MBG)\[(\d+)(?::(\d+))?\]',entry['m_tag']);assert match,'non-HBM or HBM-allocation-group tag'
  lo=int(match[1]);hi=int(match[2] or match[1]);assert 0<=lo<=hi<32 and int(entry['m_used'])==1
  for i in range(lo,hi):assert int(physical[i]['m_base_address'],0)+int(physical[i]['m_sizeKB'],0)*1024==int(physical[i+1]['m_base_address'],0)
  assert int(entry['m_base_address'],0)==int(physical[lo]['m_base_address'],0)
  assert int(entry['m_sizeKB'],0)==sum(int(physical[i]['m_sizeKB'],0) for i in range(lo,hi+1))
  return set(range(lo,hi+1))
 names={name for name,index in expected};assert {x['m_name'] for x in ips if x['m_type']=='IP_KERNEL'}==names
 assert all(sum(x['m_name']==name for x in ips)==1 for name in names)
 def decode(entries,topology,unique=True):
  values=defaultdict(set);indices=defaultdict(set);seen=set()
  for c in entries:
   ip=int(c['m_ip_layout_index']);arg=int(c['arg_index']);memory=int(c['mem_data_index']);assert 0<=ip<len(ips) and 0<=memory<len(topology)
   triple=(ip,arg,memory)
   if unique:assert triple not in seen,'duplicate memory connection'
   seen.add(triple)
   key=(ips[ip]['m_name'],arg);assert key in expected;values[key]|=members(topology[memory]);indices[key].add(memory)
  assert set(values)==set(expected)
  for key,(banks,argname) in expected.items():assert values[key]==banks,(key,argname,values[key],banks)
  return indices
 raw=decode(connections,mem);all_group_ids=decode(group_connections,groups,False);group_ids={}
 # Vitis retains raw mappings and appends one allocation-group mapping per
 # argument. Singleton mappings therefore legitimately appear twice.
 for key,ids in all_group_ids.items():
  candidates={i for i in ids if members(groups[i])==expected[key][0]};assert len(candidates)==1
  group_ids[key]=candidates
 for ids in raw.values():
  for i in ids:assert members(groups[i])==members(mem[i])
 def triples(rows):return Counter((int(c['m_ip_layout_index']),int(c['arg_index']),int(c['mem_data_index'])) for c in rows)
 allocations=Counter((next(i for i,x in enumerate(ips) if x['m_name']==name),arg,next(iter(ids))) for (name,arg),ids in group_ids.items())
 assert triples(group_connections)==triples(connections)+allocations,'group mapping multiplicity differs from raw plus allocation mappings'
 graph=[next(iter(group_ids['dieroute_net_commit_sharded_hbm:net_commit',i])) for i in (1,2,3)];assert len(set(graph))==1
 return dict(pointer_arguments=len(expected),raw_connectivity_records=len(connections),group_connectivity_records=len(group_connections),resolved_bank_memberships=sum(len(v[0]) for v in expected.values()),graph_group_id=graph[0],graph_group=groups[graph[0]],argument_group_ids={name:{expected[name,i][1]:next(iter(group_ids[name,i])) for nn,i in expected if nn==name} for name in sorted(names)})

run=Path(sys.argv[1]).resolve();m=json.loads((run/'manifest.json').read_text());assert m['status']=='linked_requires_group_clock_ABI_and_runtime_review' and m['compile_returncode']==m['link_returncode']==0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protocol=json.loads((run/'protocol.json').read_text())
for field in ['source_sha256','prerequisite_sha256']:
 for p,h in protocol[field].items():assert sha(Path(p))==h
assert sha(run/'commit.xo')==m['commit_xo_sha256']
assert sha(run/'snapshot.xo')==m['snapshot_xo_sha256']
assert sha(run/'joint.xclbin')==m['xclbin_sha256']
cfg={}
for cu,arg,lo,hi in re.findall(r'^sp=(\w+)\.(\w+):HBM\[(\d+)(?::(\d+))?\]$',(run/'connectivity.cfg').read_text(),re.M):cfg[cu,arg]=set(range(int(lo),int(hi or lo)+1))
cu_map={'commit':'net_commit','worker':'search_worker','snapshot':'snapshot_search'};expected={};master_counts={}
for short,cu in cu_map.items():
 with zipfile.ZipFile(run/(short+'.xo')) as z:
  root=ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('/kernel.xml'))));kernel=next(root.iter('kernel')).attrib['name'];master_counts[short]=sum(v.attrib['mode']=='master' for v in root.iter('port'))
  for arg in root.iter('arg'):
   if arg.attrib['addressQualifier']=='1':expected[kernel+':'+cu,int(arg.attrib['id'])]=(cfg[cu,arg.attrib['name']],arg.attrib['name'])
assert len(expected)==39 and len(cfg)==39
out=run/'group_audit';out.mkdir(exist_ok=False)
tool='/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt/bin/xclbinutil'
for name in ['MEM_TOPOLOGY','IP_LAYOUT','CONNECTIVITY','GROUP_TOPOLOGY','GROUP_CONNECTIVITY']:
 with (out/(name.lower()+'.log')).open('w') as log:subprocess.run([tool,'--input',str(run/'joint.xclbin'),'--dump-section',name+':JSON:'+str(out/(name.lower()+'.json'))],check=True,stdout=log,stderr=subprocess.STDOUT)
def section(name,key):return json.loads((out/(name+'.json')).read_text())[name][key]
groups=section('group_topology','m_mem_data')
r=verify_sections(section('mem_topology','m_mem_data'),section('ip_layout','m_ip_data'),section('connectivity','m_connection'),groups,section('group_connectivity','m_connection'),expected)
capacity=json.loads((run/'capacity.json').read_text());roles={}
def role(arg):
 if arg in ['resources0','resources1','resources2']:return 'owner'+arg[-1]
 if arg in ['policy','offsets','arcs','potential']:return 'graph'
 if arg in ['trees','nets','control','authority_control']:return 'authority'
 return 'scratch'
canonical={'graph':set(range(16,32)),'authority':{12},'scratch':set(range(12)),'owner0':{13},'owner1':{14},'owner2':{15}}
assert master_counts=={'commit':6,'worker':2,'snapshot':6}
for (kernel,argid),(banks,argname) in expected.items():assert banks==canonical[role(argname)],(kernel,argname,'noncanonical physical role')
for name in canonical:
 ids={group for cu,args in r['argument_group_ids'].items() for arg,group in args.items() if role(arg)==name};assert len(ids)==1;index=ids.pop();actual=int(groups[index]['m_sizeKB'],0)*1024;assert actual==capacity['regions'][name]['capacity_bytes'] and actual>=capacity['regions'][name]['aligned_bytes'];roles[name]=index
assert len(set(roles.values()))==6
for owner in range(3):
 key='resources'+str(owner);writer=r['argument_group_ids']['dieroute_net_commit_sharded_hbm:net_commit'][key];reader=r['argument_group_ids']['dieroute_native_snapshot_search_sharded_hbm:snapshot_search'][key];assert writer==reader==roles['owner'+str(owner)]
r.update(status='sharded_groups_verified_runtime_ownership_pending',allocation_role_group_ids=roles,axi_master_counts=master_counts,xclbin_sha256=m['xclbin_sha256'],scope='Actual39-pointer/14-master final groups with three separate owner banks; two-phase commit plus unchanged higher-g worker and dualformat snapshot hw_emu image; actual shared BO usage and coherent handoff still require runtime proof; not physical bank or performance evidence',board_result=False)
r['source_sha256']={str(p):sha(p) for p in [run/'manifest.json',run/'protocol.json',run/'connectivity.cfg',run/'capacity.json',run/'joint.xclbin',*[run/(n+'.xo') for n in ['commit','worker','snapshot']],*out.glob('*.json'),Path(__file__).resolve()]}
(out/'audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'roles':roles,'pointer_arguments':len(expected)}))

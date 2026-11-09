"""Check full-graph bank groups, including the group IDs used by XRT."""
import argparse,hashlib,json,re,subprocess
from collections import defaultdict,Counter
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expectations(full=True):
 result={}
 for die in range(3):
  for kernel,cu,args in [('dieroute_summary_hbm','summary','commands topology owners shadows responses completion'.split()),('dieroute_owner_publish_hbm','owner','commands topology owners registry dirty_queue responses updates queue_control completion'.split())]:
   for index,arg in enumerate(args):
    if full:bank=die*4+(1 if arg in ('topology','dirty_queue','queue_control') else 2 if arg=='owners' else 3 if arg=='shadows' else 0)
    else:bank=die*8+(1 if arg in ('topology','dirty_queue','queue_control') else 2 if arg=='owners' else 3 if arg=='shadows' else 5 if arg=='registry' else 7 if arg=='updates' else 0)
    result[f'{kernel}:{cu}_die{die}',index]=({bank},arg)
 for index,arg in enumerate('command policy offsets arcs reads shadows branches paths resources trees nets control scratch deltas completion'.split()):
  bank=set(range(16,32)) if index in (1,2,3) else {12} if index in (8,9,10,11) else {13}
  if not full:bank={25} if index in (1,2,3) else {26} if index in (8,9,10,11) else {24}
  result['dieroute_net_commit_hbm:net_commit',index]=(bank,arg)
 return result

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
 graph=[next(iter(group_ids['dieroute_net_commit_hbm:net_commit',i])) for i in (1,2,3)];assert len(set(graph))==1
 for die in range(3):
  for i in (1,2):assert group_ids[f'dieroute_owner_publish_hbm:owner_die{die}',i]==group_ids[f'dieroute_summary_hbm:summary_die{die}',i]
 return dict(pointer_arguments=len(expected),raw_connectivity_records=len(connections),group_connectivity_records=len(group_connections),resolved_bank_memberships=sum(len(v[0]) for v in expected.values()),graph_group_id=graph[0],graph_group=groups[graph[0]],argument_group_ids={name:{expected[name,i][1]:next(iter(group_ids[name,i])) for nn,i in expected if nn==name} for name in sorted(names)})

def main():
 if not __debug__:raise RuntimeError('audit requires assertions')
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--capacity',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run=a.run.resolve();out=a.output.resolve();assert not out.exists()
 manifest=run/'manifest.json';m=json.loads(manifest.read_text());assert m['status']=='passed' and m['returncode']==0 and m['inputs_unchanged']
 for path,digest in m['inputs'].items():assert sha(path)==digest,path
 image=run/'joint.xclbin';assert sha(image)==m['xclbin_sha256'];budget=json.loads(a.capacity.read_text())
 for path,digest in budget['inputs'].items():assert sha(path)==digest,path
 out.mkdir();tool='/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt/bin/xclbinutil'
 for section in ('MEM_TOPOLOGY','IP_LAYOUT','CONNECTIVITY','GROUP_TOPOLOGY','GROUP_CONNECTIVITY','CLOCK_FREQ_TOPOLOGY'):
  with (out/(section.lower()+'.log')).open('w') as log:subprocess.run([tool,'--input',str(image),'--dump-section',f'{section}:JSON:{out/(section.lower()+".json")}'],check=True,stdout=log,stderr=subprocess.STDOUT)
 def section(name,key):return json.loads((out/(name+'.json')).read_text())[name][key]
 groups=section('group_topology','m_mem_data');result=verify_sections(section('mem_topology','m_mem_data'),section('ip_layout','m_ip_data'),section('connectivity','m_connection'),groups,section('group_connectivity','m_connection'),expectations())
 assert int(result['graph_group']['m_sizeKB'],0)*1024==4*1024**3 and budget['group_budgets']['16:31']['allocation_budget_bytes']<=int(result['graph_group']['m_sizeKB'],0)*1024
 result.update(schema='dieroute.full_graph_hbm_group_audit.v1',status='metadata_verified_runtime_allocation_pending',input_manifest_sha256=sha(manifest),xclbin_sha256=sha(image),capacity_ledger_sha256=sha(a.capacity),auditor_sha256=sha(__file__),clocks=json.loads((out/'clock_freq_topology.json').read_text()),runtime_group_ids_verified=False,bo_allocation_verified=False,full_graph_execution_verified=False,physical_timing=False,board_result=False)
 (out/'auditor.py').write_bytes(Path(__file__).read_bytes());(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='argument_group_ids'}))
if __name__=='__main__':main()

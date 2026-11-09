#!/usr/bin/env python3
"""Validate graph, authority and 341-net traffic allocation groups."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
from audit_native_joint_full_graph_platform import expectations,verify_sections


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()


def verify_341_sections(mem,ips,connections,groups,group_connections,capacity):
 expected=expectations();traffic={'command','reads','shadows','branches','paths','scratch','deltas','completion'}
 for key,(banks,name) in list(expected.items()):
  if key[0]=='dieroute_net_commit_hbm:net_commit' and name in traffic:expected[key]=({13,14,15},name)
 result=verify_sections(mem,ips,connections,groups,group_connections,expected)
 net=result['argument_group_ids']['dieroute_net_commit_hbm:net_commit'];roles={'graph':['policy','offsets','arcs'],'authority':['resources','trees','nets','control'],'traffic':sorted(traffic)};ids={}
 for role,names in roles.items():
  values={net[name] for name in names};assert len(values)==1,(role,'inconsistent allocation group')
  group=next(iter(values));ids[role]=group;actual=int(groups[group]['m_sizeKB'],0)*1024
  budget=capacity['regions'][role];assert actual==budget['candidate_capacity_bytes'] and budget['planning_budget_bytes']<=actual,(role,'capacity mismatch')
 assert len(set(ids.values()))==3,'allocation role alias'
 result.update(allocation_role_group_ids=ids,traffic_group=groups[ids['traffic']]);return result


def main():
 if not __debug__:raise RuntimeError('assertions required')
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['run','capacity','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();run=a.run.resolve();out=a.output.resolve();manifest=run/'manifest.json';m=json.loads(manifest.read_text());assert m['status']=='passed' and m['returncode']==0 and m['inputs_unchanged']
 for path,digest in m['inputs'].items():assert sha(path)==digest,path
 image=run/'joint.xclbin';assert sha(image)==m['xclbin_sha256'];capacity=json.loads(a.capacity.read_text());project=a.capacity.resolve().parent.parent;reference=project/capacity['source_run'];rm=json.loads((reference/'manifest.json').read_text());assert rm['status']=='passed'
 frames=reference/'route/net_commit_frames.bin';assert sha(frames)==rm['artifacts']['route/net_commit_frames.bin']==capacity['abi_frames_reference_sha256']
 with frames.open('rb') as f:f.seek(192);cfg=struct.unpack('<8Q',f.read(64))
 assert tuple(capacity['configuration'][k] for k in ['nodes','arcs','dies','shard','nets','trees','scratch','deltas'])==cfg
 peaks=[0]*4
 with frames.open('rb') as f:
  f.seek(64)
  while True:
   head=f.read(192)
   if not head:break
   assert len(head)==192
   h=struct.unpack_from('<16Q',head);assert struct.unpack_from('<8Q',head,128)==cfg and h[7]>=56
   peaks=[max(a,b) for a,b in zip(peaks,h[8:12])];f.seek(h[7]*8-192,1)
 assert tuple(capacity['observed_peaks'][k] for k in ['reads','shadows','branches','paths'])==tuple(peaks)
 sizes={'graph':[cfg[0]*8,(cfg[0]+1)*8,cfg[1]*8],'authority':[cfg[2]*cfg[3]*64,cfg[5]*64,cfg[4]*64,64],'traffic':[128,*[n*w for n,w in zip(peaks,[16,64,64,16])],cfg[6]*128,cfg[7]*64,64]}
 unit=2*(1<<20)
 for role,values in sizes.items():
  assert capacity['regions'][role]['payload_bytes']==sum(values)
  assert capacity['regions'][role]['planning_budget_bytes']==sum((v+unit-1)//unit*unit for v in values)

 out.mkdir(exist_ok=False);tool='/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt/bin/xclbinutil'
 for section in ['MEM_TOPOLOGY','IP_LAYOUT','CONNECTIVITY','GROUP_TOPOLOGY','GROUP_CONNECTIVITY','CLOCK_FREQ_TOPOLOGY']:
  with (out/(section.lower()+'.log')).open('w') as log:subprocess.run([tool,'--input',str(image),'--dump-section',f'{section}:JSON:{out/(section.lower()+".json")}'],stdout=log,stderr=subprocess.STDOUT,check=True)
 def section(name,key):return json.loads((out/(name+'.json')).read_text())[name][key]
 result=verify_341_sections(section('mem_topology','m_mem_data'),section('ip_layout','m_ip_data'),section('connectivity','m_connection'),section('group_topology','m_mem_data'),section('group_connectivity','m_connection'),capacity)
 helper=Path(__file__).with_name('audit_native_joint_full_graph_platform.py');shutil.copy2(helper,out/helper.name);shutil.copy2(__file__,out/'auditor.py')
 result.update(status='metadata_verified_runtime_allocation_pending',schema='dieroute.native_341net_group_audit.v1',input_manifest_sha256=sha(manifest),xclbin_sha256=sha(image),capacity_sha256=sha(a.capacity),auditor_sha256=sha(__file__),helper_sha256=sha(helper),runtime_allocation_verified=False,full_341net_execution_verified=False,physical_timing=False,board_result=False)
 (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'allocation_role_group_ids':result['allocation_role_group_ids']}))

if __name__=='__main__':main()

"""Verify the seven-CU emulation topology; never infer physical placement."""
import argparse,copy,hashlib,json,subprocess,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_sections(mem,ips,connections):
 hbm=[m for m in mem if m['m_tag'].startswith('HBM[')];assert len(hbm)==32
 assert {m['m_tag'] for m in hbm}=={f'HBM[{i}]' for i in range(32)}
 ranges=sorted((int(m['m_base_address'],0),int(m['m_sizeKB'],0)*1024) for m in hbm)
 assert all(size==256*1024*1024 for _,size in ranges) and all(a+size<=b for (a,size),(b,_) in zip(ranges,ranges[1:]))
 expected={}
 for die in range(3):
  for kernel,cu,args,offsets in [('dieroute_owner_publish_hbm','owner','commands topology owners registry dirty_queue responses updates queue_control completion'.split(),[0,1,2,5,1,0,7,1,0]),('dieroute_summary_hbm','summary','commands topology owners shadows responses completion'.split(),[0,1,2,3,0,0])]:
   expected[f'{kernel}:{cu}_die{die}']=(args,[8*die+x for x in offsets])
 expected['dieroute_net_commit_hbm:net_commit']=('command policy offsets arcs reads shadows branches paths resources trees nets control scratch deltas completion'.split(),[24,25,25,25,24,24,24,24,26,26,26,26,24,24,24])
 assert {x['m_name'] for x in ips if x['m_type']=='IP_KERNEL'}==set(expected)
 result={};used=set();count=0
 for name,(args,banks) in expected.items():
  match=[i for i,x in enumerate(ips) if x['m_name']==name];assert len(match)==1
  conn=[x for x in connections if int(x['m_ip_layout_index'])==match[0]];assert len(conn)==len(args)
  values={int(x['arg_index']):mem[int(x['mem_data_index'])] for x in conn};assert set(values)==set(range(len(args)))
  result[name]={}
  for i,(arg,bank) in enumerate(zip(args,banks)):
   value=values[i];assert value['m_tag']==f'HBM[{bank}]' and int(value['m_used'])==1
   result[name][arg]=value['m_tag'];used.add(value['m_tag']);count+=1
 assert len(connections)==count==60 and len(used)==21
 return dict(cu_banks=result,verified_pointer_connections=count,unique_hbm_banks=len(used),cus=7)

def main():
 if not __debug__:raise RuntimeError('audit requires assertions')
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args();run=a.run.resolve();out=a.output.resolve();out.mkdir()
 m=json.loads((run/'manifest.json').read_text());assert m['status']=='passed' and m['returncode']==0 and m['inputs_unchanged'];xclbin=run/'joint.xclbin';assert sha(xclbin)==m['xclbin_sha256']
 for path,digest in m['inputs'].items():assert sha(path)==digest,path
 tool='/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt/bin/xclbinutil'
 for section in ('MEM_TOPOLOGY','CONNECTIVITY','IP_LAYOUT','CLOCK_FREQ_TOPOLOGY'):
  with (out/(section.lower()+'.log')).open('w') as log:subprocess.run([tool,'--input',str(xclbin),'--dump-section',f'{section}:JSON:{out/(section.lower()+".json")}'],stdout=log,stderr=subprocess.STDOUT,check=True)
 mem=json.loads((out/'mem_topology.json').read_text())['mem_topology']['m_mem_data'];ips=json.loads((out/'ip_layout.json').read_text())['ip_layout']['m_ip_data'];conn=json.loads((out/'connectivity.json').read_text())['connectivity']['m_connection']
 result=verify_sections(mem,ips,conn)
 masters={}
 for role,record in m['kernel_inputs'].items():
  with zipfile.ZipFile(record['xo']) as z:
   name={'summary':'dieroute_summary_hbm','owner':'dieroute_owner_publish_hbm','net':'dieroute_net_commit_hbm'}[role];kernel=ET.fromstring(z.read(name+'/kernel.xml')).find('kernel')
   masters[role]={x.attrib['name']:int(x.attrib['dataWidth']) for x in kernel.find('ports') if x.attrib['mode']=='master'}
 assert masters['summary']==dict(M_AXI_INGRESS=512,M_AXI_DIRECTORY=64,M_AXI_OWNER_STATE=512,M_AXI_SHADOW_STATE=512)
 assert masters['owner']==dict(M_AXI_TRAFFIC=512,M_AXI_INDEX=512,M_AXI_OWNER_STATE=512,M_AXI_SUBSCRIPTIONS=512,M_AXI_PUBLICATIONS=512)
 assert masters['net']==dict(M_AXI_TRAFFIC=512,M_AXI_GRAPH=64,M_AXI_AUTHORITY=512)
 # Mutate the actual extracted topology: duplicates must not be silently
 # collapsed by dictionary construction, and bank aliases must be rejected.
 mutations=[]
 bad=copy.deepcopy(conn);bad[1]=copy.deepcopy(bad[0]);mutations.append(('duplicate_argument',mem,ips,bad))
 bad=copy.deepcopy(conn);bad[0]['mem_data_index']=str((int(bad[0]['mem_data_index'])+1)%len(mem));mutations.append(('wrong_bank',mem,ips,bad))
 mutations.append(('missing_connection',mem,ips,conn[:-1]))
 bad=copy.deepcopy(ips);bad.append(copy.deepcopy(next(x for x in ips if x['m_type']=='IP_KERNEL')));mutations.append(('duplicate_cu',mem,bad,conn))
 bad=copy.deepcopy(mem);slots=[i for i,x in enumerate(bad) if x['m_tag'].startswith('HBM[')];bad[slots[1]]['m_base_address']=bad[slots[0]]['m_base_address'];mutations.append(('overlapping_banks',bad,ips,conn))
 bad=copy.deepcopy(mem);bad[slots[0]]['m_sizeKB']='0x1';mutations.append(('wrong_bank_capacity',bad,ips,conn))
 for name,mm,ii,cc in mutations:
  try:verify_sections(mm,ii,cc)
  except (AssertionError,KeyError,IndexError):pass
  else:raise RuntimeError('accepted corrupt topology: '+name)
 result.update(schema='dieroute.native_joint_authority_platform_audit.v1',status='verified',target='hw_emu',kernel_master_ports=masters,kernel_master_instances=30,semantic_corruptions_rejected=[x[0] for x in mutations],xclbin_sha256=sha(xclbin),input_manifest_sha256=sha(run/'manifest.json'),clocks=json.loads((out/'clock_freq_topology.json').read_text()),auditor_sha256=sha(__file__),physical_placement=False,physical_timing=False,board_result=False,scope='Joint seven-CU bounded emulation platform; full graph BO placement and physical implementation remain unverified')
 (out/'auditor.py').write_bytes(Path(__file__).read_bytes());(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cu_banks'}))
if __name__=='__main__':main()

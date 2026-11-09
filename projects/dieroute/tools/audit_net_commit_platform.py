"""Check standalone hw_emu bank connectivity; never infer physical placement."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();run=a.run.resolve();out=a.out.resolve();out.mkdir()
 m=json.loads((run/'manifest.json').read_text());assert m['status']=='passed' and m['returncode']==0 and m['inputs_unchanged']
 xclbin=run/'net_commit.xclbin';assert sha(xclbin)==m['xclbin_sha256']
 for path,h in m['inputs'].items():assert sha(path)==h
 tool='/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt/bin/xclbinutil'
 for section in ('MEM_TOPOLOGY','CONNECTIVITY','IP_LAYOUT','CLOCK_FREQ_TOPOLOGY'):
  with (out/(section.lower()+'.log')).open('w') as f:subprocess.run([tool,'--input',str(xclbin),'--dump-section',f'{section}:JSON:{out/(section.lower()+".json")}'],stdout=f,stderr=subprocess.STDOUT,check=True)
 mem=json.loads((out/'mem_topology.json').read_text())['mem_topology']['m_mem_data'];ips=json.loads((out/'ip_layout.json').read_text())['ip_layout']['m_ip_data'];connections=json.loads((out/'connectivity.json').read_text())['connectivity']['m_connection']
 hbm=[x for x in mem if x['m_tag'].startswith('HBM[')];assert len(hbm)==32 and len({int(x['m_base_address'],0) for x in hbm})==32 and all(int(x['m_sizeKB'],0)==256*1024 for x in hbm)
 ranges=sorted((int(x['m_base_address'],0),int(x['m_sizeKB'],0)*1024) for x in hbm);assert all(a+size<=b for (a,size),(b,_) in zip(ranges,ranges[1:]))
 matches=[i for i,x in enumerate(ips) if x['m_name']=='dieroute_net_commit_hbm:net_commit'];assert len(matches)==1
 conn=[x for x in connections if int(x['m_ip_layout_index'])==matches[0]];assert len(conn)==15
 values={int(x['arg_index']):mem[int(x['mem_data_index'])] for x in conn};assert set(values)==set(range(15))
 names='command policy offsets arcs reads shadows branches paths resources trees nets control scratch deltas completion'.split();mapping={}
 for i,name in enumerate(names):
  expected=1 if i in (1,2,3) else 2 if i in (8,9,10,11) else 0
  assert values[i]['m_tag']==f'HBM[{expected}]' and int(values[i]['m_used'])==1;mapping[name]=values[i]['m_tag']
 result=dict(schema='dieroute.net_commit_platform_audit.v1',status='verified',target='hw_emu',pointer_connections=15,unique_banks=3,argument_banks=mapping,xclbin_sha256=sha(xclbin),input_manifest_sha256=sha(run/'manifest.json'),clocks=json.loads((out/'clock_freq_topology.json').read_text()),auditor_sha256=sha(__file__),physical_placement=False,physical_timing=False,board_result=False,scope='Standalone component with one logical-owner authority master; full graph and joint publisher/receiver integration remain unverified')
 (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()

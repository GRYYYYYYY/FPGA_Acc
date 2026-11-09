"""Owned native observer: load existing packing only, export actual masks/nets."""
import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'experiments/prince_native_packed_LUTs_v1_2026-10-20';P=R/'experiments/prince_direct_pn_pack_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False)
 old=R/'experiments/prospective_external_family_native_packed_LUTs_v1_2026-10-19';cmd=json.loads((old/'build_command.json').read_text());source=R/'tools/native_external_packed_LUTs_v1.cpp';text=source.read_text().replace('count!=6483','count!=2096')
 text=text.replace('if(ports.size()!=1)throw std::runtime_error("logical port");auto port=*ports.begin();','if(ports.size()>1)throw std::runtime_error("logical port");')
 text=text.replace('auto logical=pb->atom_pin_bit_index(pin);auto net=atom.nlist.port_net(port,logical);','if(ports.size()!=1)throw std::runtime_error("connected constant pin");auto port=*ports.begin();auto logical=pb->atom_pin_bit_index(pin);auto net=atom.nlist.port_net(port,logical);')
 own=O/'observer.cpp';own.write_text(text);cmd=[str(own) if a==str(source) else a for a in cmd];cmd[cmd.index('-o')+1]=str(O/'observer');save('build_command.json',cmd)
 inputs=[Path(a) for a in cmd if not a.startswith('-') and Path(a).is_file()];bindings={str(p):sha(p) for p in [*inputs,source,Path(__file__),old/'build_command.json',P/'design.blif',P/'design.net',R/'experiments/prince_packed_LUT_pins_v1_2026-10-20/verification.json']}
 save('build_protocol.json',{'command':cmd,'bindings':bindings,'scope':'Owned observer derived from pinned loader; adds zero-logical-input constant handling; VPR source and libraries read only. Expected all2096 LUTs. No new pack/place/route call.'})
 with (O/'build.log').open('x') as f:rc=subprocess.call(cmd,cwd=O,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0
 oldprotocol=json.loads((old/'protocol.json').read_text());arch=R/'experiments/prince_direct_pn_arch_v1_2026-10-20/architecture.xml';command=[str(O/'observer'),str(O/'loaded_LUTs.tsv'),str(arch),str(P/'design.blif'),'--pack','--net_file',str(P/'design.net'),'--route_chan_width','128','--num_workers','1','--seed','1']
 save('protocol.json',{'command':command,'bindings':{**bindings,str(arch):sha(arch),str(O/'observer'):sha(O/'observer')},'scope':'vpr_init plus vpr_load_packing only. Native loaded truth masks and physical signal identities; no pack/place/route flow or default writer invocation.'});start=time.perf_counter()
 with (O/'load.log').open('x') as f:rc=subprocess.call(command,cwd=O,stdout=f,stderr=subprocess.STDOUT)
 for n,h in bindings.items():assert sha(Path(n))==h
 save('receipt.json',{'exit_code':rc,'seconds':time.perf_counter()-start,'export_sha256':sha(O/'loaded_LUTs.tsv') if (O/'loaded_LUTs.tsv').exists() else None,'bindings':{'protocol.json':sha(O/'protocol.json'),'load.log':sha(O/'load.log')}});print('NATIVE_LOAD_TERMINAL',rc,flush=True)
 assert rc==0
if __name__=='__main__':main()

"""Read-only post-sync atom/cluster mapping exporter based on canonical observer."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/native_verbose_sync_v2_2026-10-08';D=R/'build/native_external_final_atom_mapping_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((B/'protocol.json').read_text());assert sha(B/'hook.cpp')==p['source_sha256'];assert all(sha(k)==h for k,h in p['bindings'].items());D.mkdir(exist_ok=False)
 s=(B/'hook.cpp').read_text();s='#include "clustered_netlist_utils.h"\n#include <cstdlib>\n#include <stdexcept>\n'+s
 a='real_sync(n,d,a,c,p,verbose);';assert s.count(a)==1
 code=r'''
 const char* path=std::getenv("ROUTECAST_FINAL_ATOM_MAPPING");
 if(path && *path) {
  FILE* f=std::fopen(path,"wx");if(!f)throw std::runtime_error("mapping open");
  IntraLbPbPinLookup intra(d.logical_block_types);
  ClusteredPinAtomPinsLookup lookup(c.clb_nlist,a.nlist,intra);
  std::fprintf(f,"atom_pin\tatom\tport\tbit\tatom_net\tcluster\tcluster_pin\tcluster_net\tlocal_pin\n");
  for(auto pin:a.nlist.pins()) {
   auto block=a.nlist.pin_block(pin);auto clb=a.lookup.atom_clb(block);auto net=a.nlist.pin_net(pin);auto cp=lookup.connected_clb_pin(pin);
   std::fprintf(f,"%zu\t%s\t%s\t%d\t%s\t%s\t",size_t(pin),a.nlist.block_name(block).c_str(),a.nlist.port_name(a.nlist.pin_port(pin)).c_str(),a.nlist.pin_port_bit(pin),net?a.nlist.net_name(net).c_str():"",clb?c.clb_nlist.block_name(clb).c_str():"");
   if(cp)std::fprintf(f,"%zu\t%s\t%d\n",size_t(cp),c.clb_nlist.net_name(c.clb_nlist.pin_net(cp)).c_str(),c.clb_nlist.pin_net_index(cp));
   else std::fprintf(f,"\t\t\n");
  }
  if(std::fclose(f))throw std::runtime_error("mapping close");
 }
'''
 (D/'hook.cpp').write_text(s.replace(a,a+code));compile=[x.replace(str(B),str(D)) for x in p['compile']];link=[x.replace(str(B),str(D)) for x in p['link']];bindings={str(B/'protocol.json'):sha(B/'protocol.json'),str(D/'hook.cpp'):sha(D/'hook.cpp'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Original verbose canonical sync executed unchanged then readonly native atom->cluster mapping. Runtime equivalence pending.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary=str(D/'verbose_sync_vpr'),binary_sha256=sha(D/'verbose_sync_vpr'),bindings=bindings),indent=2)+'\n');print('BUILT')
if __name__=='__main__':main()

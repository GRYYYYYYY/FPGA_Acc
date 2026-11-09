"""Relink graph-bound excess preload/trace router with qualified own-index/groupOR."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];OLD=R/'build/native_excess_preload_state_v2_2026-10-19';FIX=R/'build/native_shared_sink_contract_v3_2026-10-19';O=R/'build/wbuart_corrected_utility_native_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);br=json.loads((OLD/'receipt.json').read_text());assert sha(OLD/'sequence_vpr')==br['binary_sha256']
 for n,h in br['bindings'].items():assert sha(Path(n))==h
 proof=R/'experiments/native_shared_sink_contract_v3_2026-10-19/verification.json';v=json.loads(proof.read_text())
 for n,h in v['bindings'].items():assert sha(Path(n))==h
 p=json.loads((OLD/'protocol.json').read_text());link=p['link'].copy();link=[str(O/'sequence_vpr') if x==str(OLD/'sequence_vpr') else x for x in link];assert str(FIX/'group_or.o') not in link;link.insert(1,str(FIX/'group_or.o'));assert next(i for i,x in enumerate(link) if x.endswith('group_or.o'))<next(i for i,x in enumerate(link) if x.endswith('libvpr.a'))
 bindings={str(p):sha(p) for p in [Path(__file__),OLD/'receipt.json',OLD/'protocol.json',proof]}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(Path(x))
 (O/'protocol.json').write_text(json.dumps({'link':link,'bindings':bindings,'scope':'Existing opt-in graph-bound CHANNEL excess preload/all-node readback and owner trace, with qualified own-index IPIN lower bounds and perNET shared-SINK force reset/group OR object overriding archive definition. No vendor/sibling writes. Disabled/zero source parity and trace audits pending, no target labels.'},indent=2)+'\n')
 with (O/'link.log').open('x') as f:rc=subprocess.call(link,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0
 for n,h in bindings.items():assert sha(Path(n))==h
 (O/'receipt.json').write_text(json.dumps({'binary':str(O/'sequence_vpr'),'binary_sha256':sha(O/'sequence_vpr'),'own_index_and_group_OR_object_linked':True,'source_disabled_zero_parity_pending':True,'bindings':{**bindings,str(O/'protocol.json'):sha(O/'protocol.json'),str(O/'link.log'):sha(O/'link.log')}},indent=2)+'\n');print('CORRECTED_UTILITY_NATIVE_LINK_PASS',flush=True)
if __name__=='__main__':main()

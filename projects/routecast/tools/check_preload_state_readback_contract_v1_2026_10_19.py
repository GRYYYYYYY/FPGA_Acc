import pathlib,struct,json,hashlib
from preload_state_readback_contract_v1 import verify,ONE
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/preload_state_readback_contract_v1_2026-10-19';O.mkdir();digest='a'*64;rp=O/'valid.risk';rp.write_text(f'RCRISK1 {digest} 4 1\n2 1056964608\n');sp=O/'valid.bin';sp.write_bytes(b'RCACCBITS1 4\n'+struct.pack('<4I',ONE,ONE,1069547520,ONE));log='initial excess preload entries=1 changed=1 acc_fac=1';assert verify(sp,rp,digest,4,log)['all_nodes_checked']==4
errors=[]
for name,data,sha,n,text in [('wrong_unpriced',b'RCACCBITS1 4\n'+struct.pack('<4I',0,ONE,1069547520,ONE),digest,4,log),('wrong_priced',b'RCACCBITS1 4\n'+struct.pack('<4I',ONE,ONE,ONE,ONE),digest,4,log),('truncated',sp.read_bytes()[:-1],digest,4,log),('wrong_graph',sp.read_bytes(),'b'*64,4,log),('wrong_count',sp.read_bytes(),digest,5,log),('wrong_native_count',sp.read_bytes(),digest,4,log.replace('changed=1','changed=0'))]:
 p=O/(name+'.bin');p.write_bytes(data)
 try:verify(p,rp,sha,n,text)
 except AssertionError:errors.append(name)
 else:raise AssertionError(name)
files=[pathlib.Path(__file__).resolve(),R/'tools/preload_state_readback_contract_v1.py'];(O/'verification.json').write_text(json.dumps(dict(status='ALL_NODE_READBACK_POSITIVE_AND6_CORRUPTION_CHECKS_PASS',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},rejected_corruptions=errors,real_native_readback_pending=True),indent=2)+'\n');print('READBACK CONTRACT PASS')

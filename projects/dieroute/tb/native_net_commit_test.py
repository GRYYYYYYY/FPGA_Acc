"""Fresh online routing through the synthesizable complete-net authority."""
import argparse,csv,json,struct,subprocess,sys,tempfile
from pathlib import Path
from native_csr_test import table,FINGERPRINT
from native_search_graph_test import container
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from audit_native_parallel import verify as verify_native
from audit_native_net_commit import verify as verify_kernel
from audit_native_label_transport import crc64

def fixture(base,cross,builder):
 base.mkdir()
 for x in ('graph','search','footprint','mapping'):(base/x).mkdir()
 if cross:
  masks=[4,6,2,3,1,6,1,2,4,3,2,4,2,2,2]
  edges=[(0,1,2),(1,2,1),(2,3,1),(3,4,0),(8,5,2),(5,2,1),(3,6,0),(5,7,1),(7,10,1),(10,13,1),(13,14,1),(14,9,1),(9,6,0),(0,11,2)]
  tasks=[[0,0,0,4,2,0,0,0],[1,1,8,6,2,0,0,0]];owners=[(n,0) for n in (0,1,2,3,4)]+[(n,1) for n in (8,5,7,10,13,14,9,6)]
  exclusive=[0xffffffff]*len(masks)
  for n in (0,4):exclusive[n]=0
  for n in (8,6):exclusive[n]=1
 else:
  masks=[1]*9+[2,4,3];edges=[(s,d,0) for s,d in [(0,1),(0,2),(1,5),(1,6),(2,3),(3,5),(3,7),(4,1)]]
  tasks=[[0,0,0,5,0,0,0,0],[1,1,4,6,0,0,0,0],[2,0,0,7,0,0,0,0]];owners=[(n,net) for net,ns in [(0,[0,2,3,5,7]),(1,[4,1,6]),(2,[8,9,10])] for n in ns]
  exclusive=[0,0xffffffff,0xffffffff,0xffffffff,1,0,1,0,2,2,2,0xffffffff]
 n=len(masks)
 table(base/'graph/nodes.bin',[[i,i,0,i,0,masks[i],1,0,0,0,0,0,0,0,0,0] for i in range(n)])
 table(base/'graph/pips.bin',[[k,s,d,0,k,k,die,0] for k,(s,d,die) in enumerate(edges)])
 table(base/'mapping/footprint_node_map.bin',[[i] for i in range(n)])
 table(base/'footprint/tasks.bin',tasks);table(base/'footprint/nets.bin',[[0]*16 for _ in range(2 if cross else 3)]);table(base/'footprint/owners.bin',owners)
 offsets=[0];arcs=[]
 for i in range(n):arcs.extend(sorted((d,k*2) for k,(s,d,die) in enumerate(edges) if s==i));offsets.append(len(arcs))
 container(base/'search/offsets.bin',0x44520001,8,struct.pack('<'+'Q'*len(offsets),*offsets));container(base/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*x) for x in arcs));container(base/'search/node_protection.bin',0x4452000a,1,bytes(n));container(base/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<'+'I'*n,*exclusive))
 r=subprocess.run([str(builder),str(base/'graph'),str(base/'search'),FINGERPRINT,str(base/'quotient')],capture_output=True,text=True);assert r.returncode==0,r.stderr

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--router',required=True,type=Path);ap.add_argument('--quotient-builder',required=True,type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();tmp=None
 if a.output is None:tmp=tempfile.TemporaryDirectory();a.output=Path(tmp.name)/'cases'
 out=a.output.resolve();out.mkdir();results=[]
 for cross in (False,True):
  inputs=out/('cross' if cross else 'interior');fixture(inputs,cross,a.quotient_builder.resolve())
  for period in (1,3):
   cmd=[str(a.router.resolve()),*[str(inputs/x) for x in ('graph','search','footprint','mapping','quotient')],FINGERPRINT,'OUTPUT','100','2','10','3','0','3','0','0','1','1','1','1','1','2',str(period),'2']
   for mode in ('cpu','kernel'):
    case=out/f'{inputs.name}_{period}_{mode}';case.mkdir();command=list(cmd);command[7]=str(case/'route')
    if mode=='kernel':command.append('1')
    (case/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    r=subprocess.run(command,capture_output=True,text=True);(case/'run.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
    # The existing coordinator audit independently checks the old protocol;
    # the kernel-specific audit below binds its new command/result records.
    previous=verify_native(case,{'command':command});assert previous['passed']
    if mode=='kernel':assert previous['net_commit']['verified']
   baseline=out/f'{inputs.name}_{period}_cpu/route';case=out/f'{inputs.name}_{period}_kernel';command=json.loads((case/'command.json').read_text())
   equal=[]
   for p in baseline.iterdir():
    if p.name not in ('audit.json','execution.csv'):assert p.read_bytes()==(case/'route'/p.name).read_bytes(),p.name;equal.append(p.name)
   proof=verify_kernel(case,command);assert proof['op_counts'][4]>0 and proof['op_counts'][5]>0
   with (case/'route/transactions.csv').open() as f:tx=list(csv.DictReader(f))
   assert any(int(r['conflicts']) for r in tx)
   if cross:
    with (case/'route/persistent_shadow_checks.csv').open() as f:assert any(int(r['stale']) for r in csv.DictReader(f))
   # Mutate real online records and recompute CRC, leaving canonical route
   # results intact. The new audit must detect each semantic discrepancy.
   framepath=case/'route/net_commit_frames.bin';original=framepath.read_bytes();positions=[];pos=64
   while pos<len(original):
    h=struct.unpack_from('<16Q',original,pos);positions.append((pos,h));pos+=h[7]*8
   target,h=next((p,h) for p,h in positions if h[6]==3 and h[8] and struct.unpack_from('<Q',original,p+320)[0]==0)
   # Frame layout: prefix 128B, config 64B, command 128B, completion 64B,
   # control 64B, followed by reads/shadows/branches/paths/deltas/inventories.
   mutations=[('context',target+32),('observed_generation',target+192+40),('read_checks',target+320+16),('revision',target+384+8),('read_version',target+448+8)]
   payload=target+448+h[8]*16+h[9]*64
   if h[10]:mutations.append(('branch_cost',payload+40))
   delta=payload+h[10]*64+h[11]*16
   if h[12]:mutations.append(('delta_version',delta+32))
   resource=delta+h[12]*64
   if h[13]:mutations.append(('authority_version',resource+8+24))
   for name,offset in mutations:
    damaged=bytearray(original);value=struct.unpack_from('<Q',damaged,offset)[0];struct.pack_into('<Q',damaged,offset,value^1);struct.pack_into('<Q',damaged,48,crc64(damaged[64:]));framepath.write_bytes(damaged)
    try:
     try:verify_kernel(case,command)
     except (AssertionError,KeyError,IndexError):pass
     else:raise RuntimeError('accepted kernel corruption: '+name)
    finally:framepath.write_bytes(original)
   pubpath=case/'route/net_commit_publications.bin';raw=pubpath.read_bytes();assert len(raw)>64
   for offset in (64+48,64+64+24):
    damaged=bytearray(raw);value=struct.unpack_from('<Q',damaged,offset)[0];struct.pack_into('<Q',damaged,offset,value^1);struct.pack_into('<Q',damaged,48,crc64(damaged[64:]));pubpath.write_bytes(damaged)
    try:
     try:verify_kernel(case,command)
     except (AssertionError,KeyError,IndexError):pass
     else:raise RuntimeError('accepted detached/forged publication')
    finally:pubpath.write_bytes(raw)
   result=dict(case=case.name,kernel=proof,equal_outputs=equal,semantic_corruptions_rejected=len(mutations)+2);(case/'audit.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
 (out/'audit.json').write_text(json.dumps(dict(status='passed',cases=results),indent=2)+'\n');print('native kernel authority: fresh interior/cross-die congestion, exact output parity, independent kernel/publication replay and semantic corruptions passed')
if __name__=='__main__':main()

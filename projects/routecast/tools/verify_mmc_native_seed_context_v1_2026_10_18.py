"""Independent bulk binary lexer and complete per-CID seed count verification."""
import array,collections,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';root=E/'mmc_native_seed_context_replay_v1_2026-10-18';rp=root/'verification.json';r=json.loads(rp.read_text());source=E/'mmc_native_connection_seed_context_v1_2026-10-18';qp=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';inv={}
 for line in qp.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin=map(int,t[1:4]);inv[net,pin]=cid
 assert len(inv)==115572 and sha(qp)==r['bindings'][str(qp)];rows=[]
 with Cache().installed():
  assert all(sha(p)==h for p,h in r['bindings'].items())
  for row in r['rows']:
   case,arm=row['case'],row['arm'];folder=source/case/arm;attempts=[None];pending=None;calls=array.array('Q',[0])*115572
   with (folder/'connection_trace.tsv').open() as f:
    assert next(f)=='CONNECTION_TRACE 2\n'
    for line in f:
     t=line.split()
     if t[0]=='A':
      a=list(map(int,t[1:]));assert pending is None and a[0]==len(attempts);pending=a
     elif t[0] in ('C','F'):
      z=list(map(int,t[1:]));assert pending is not None and z[:4]==pending[:4];seq,it,net,pin,src,sink,before,pops=pending;cid=inv[net,pin];assert z[4]>=before;attempts.append((cid,sink,before,z[4]));calls[cid]+=1;pending=None
   assert pending is None and len(attempts)-1==row['attempts'];counts=array.array('Q',[0])*115572;uniques=array.array('Q',[0])*115572;records=inside=outside=lastseq=lastpush=0;seen=set();ended=False
   def flush():
    if lastseq:uniques[attempts[lastseq][0]]+=len(seen)
   with (folder/'seed_context.bin').open('rb') as f:
    assert f.readline()==b'RC_SEED_PUSH_LE64 1\n'
    while block:=f.read(1<<20):
     assert len(block)%32==0
     for seq,node,target,push in struct.iter_unpack('<QQQQ',block):
      assert not ended
      if seq==2**64-1:
       assert (node,target,push)==(records,inside,outside);ended=True;continue
      assert node<904438 and target<904438 and push>0;records+=1
      if not seq:outside+=1;continue
      assert lastseq<=seq<len(attempts);cid,sink,before,after=attempts[seq];assert target==sink and before<push<=after
      if seq!=lastseq:flush();seen=set();lastpush=before
      assert push>lastpush;lastpush=push;lastseq=seq;seen.add(node);counts[cid]+=1;inside+=1
   flush();assert ended and records==row['seed_records'] and inside==row['inside_seed_pushes'] and outside==row['outside_seed_pushes'];assert all(u<=c for u,c in zip(uniques,counts))
   for name,actual in [('seed_heap_pushes',counts),('sum_unique_seed_RRs_per_attempt',uniques),('attempts',calls)]:
    d=row['vectors'][name];assert sha(d['path'])==d['sha256'];expected=array.array('Q');expected.frombytes(Path(d['path']).read_bytes());assert expected==actual and len(actual)==115572 and d['byteorder']==sys.byteorder
   rows.append(dict(case=case,arm=arm,CIDs=115572,attempts=len(attempts)-1,seed_push_records=records,inside_seed_pushes=inside,outside_seed_pushes=outside));print('INDEPENDENT COMPLETE CID SEED COUNTS PASS',case,arm,inside,outside,flush=True)
  bindings={str(p):sha(p) for p in [rp,Path(__file__),qp]}
  with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all693432CID_seed_count_unique_sum_and_attempt_vectors_independently_verified',bindings=bindings,rows=rows,scope='Independent binary records, exact target/push-window/sequence joins and complete CID arrays. Uniqueness is per-attempt then summed, not distinct vertices over all calls. Initial setup versus internal retry is not separated; no prospective frontier or elapsed-time gain claim.'),f,indent=2)
if __name__=='__main__':main()

"""Independent raw phase lexer, original XML rectangle gaps and CID record join."""
import array,json,struct,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache
MAX=2**64-1

def main():
 E=R/'experiments';root=E/'mmc_initial_frontier_replay_v1_2026-10-18';rp=root/'verification.json';r=json.loads(rp.read_text());source=E/'mmc_native_connection_seed_phase_v1_2026-10-18';qp=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';inv={}
 for line in qp.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin=map(int,t[1:4]);inv[net,pin]=cid
 assert len(inv)==115572 and sha(qp)==r['bindings'][str(qp)];graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';rows=[]
 def gap(a0,a1,b0,b1):return b0-a1 if a1<b0 else a0-b1 if b1<a0 else 0
 with Cache().installed():
  assert all(sha(p)==h for p,h in r['bindings'].items());g=[None]*904438;stack=[];nseen=0
  for event,e in ET.iterparse(graph,events=['start','end']):
   if event=='start':stack.append(e);continue
   parent=stack[-2] if len(stack)>1 else None
   if e.tag=='node' and parent is not None and parent.tag=='rr_nodes':
    n=int(e.attrib['id']);assert g[n] is None;loc=e.find('loc').attrib;g[n]=tuple(int(loc[k]) for k in ['xlow','xhigh','ylow','yhigh'])+(int(loc.get('layer','0')),);nseen+=1;parent.remove(e);e.clear()
   if e.tag=='rr_nodes':break
   stack.pop()
  assert nseen==904438
  for row in r['rows']:
   case,arm=row['case'],row['arm'];folder=source/case/arm;attempts=[None];pending=None
   with (folder/'connection_trace.tsv').open() as f:
    assert next(f)=='CONNECTION_TRACE 2\n'
    for line in f:
     t=line.split()
     if t[0]=='A':assert pending is None;pending=list(map(int,t[1:]));assert pending[0]==len(attempts)
     elif t[0] in ['C','F']:
      v=list(map(int,t[1:]));assert pending[:4]==v[:4];seq,it,net,pin,src,sink,bpush,bpop=pending;attempts.append((inv[net,pin],src,sink,bpush,bpop,v[4],v[5]));pending=None
   assert pending is None;desc=row['frontier_file'];assert sha(desc['path'])==desc['sha256'];calls=array.array('Q',[0])*115572;records=seeds=begins=ends=outside=0;lastseq=0;state=None;active=None;verified=0;initial_seeds=0;undefined=closer=notcloser=0
   with (folder/'seed_phase.bin').open('rb') as phase,(folder/'seed_context.bin').open('rb') as legacy,open(desc['path'],'rb') as output:
    assert phase.readline()==b'RC_SEED_PHASE_LE64 1\n' and legacy.readline()==b'RC_SEED_PUSH_LE64 1\n' and output.readline()==b'RC_INITIAL_FRONTIER_LE64 1\n'
    def flush():
     nonlocal verified,initial_seeds,undefined,closer,notcloser
     if state is None:return
     cid,src,sink,bpush,bpop,apush,apop=attempts[lastseq];a,b=g[src],g[sink];assert a[0]==a[1] and a[2]==a[3] and b[0]==b[1] and b[2]==b[3] and a[4]==b[4];source_gap=abs(a[0]-b[0])+abs(a[2]-b[2]);expected=(lastseq,cid,state['mode'],state['initial_count'],state['initial_unique'],state['gap'],source_gap,apush-bpush,apop-bpop,state['total_seeds'],state['phases'],state['same_layer']);raw=output.read(96);assert len(raw)==96 and struct.unpack('<12Q',raw)==expected;calls[cid]+=1;verified+=1;initial_seeds+=state['initial_count'];undefined+=state['gap']==MAX;closer+=state['gap']!=MAX and state['gap']<source_gap;notcloser+=state['gap']!=MAX and state['gap']>=source_gap
    ended=False
    while block:=phase.read(48*(1<<14)):
     assert len(block)%48==0
     for tag,seq,node,target,push,pop in struct.iter_unpack('<6Q',block):
      assert not ended
      if tag==MAX:assert (seq,node,target,push,pop)==(records,seeds,begins,ends,outside) and active is None;ended=True;continue
      records+=1
      if tag==1:
       assert active is None and 0<seq<len(attempts) and target in [0,1]
       if seq!=lastseq:
        flush();assert seq==lastseq+1;lastseq=seq;state={'mode':target,'phases':0,'total_seeds':0,'last_push':attempts[seq][3],'last_pop':attempts[seq][4]}
       cid,src,sink,bpush,bpop,apush,apop=attempts[seq];assert node==state['phases']+1 and state['last_push']<=push<=apush and state['last_pop']<=pop<=apop
       if node==1:assert push==bpush and pop==bpop
       active=dict(ordinal=node,mode=target,begin_push=push,pop=pop,seeds=set(),count=0,last_push=push);begins+=1
      elif tag==2:
       old=legacy.read(32);assert len(old)==32 and struct.unpack('<4Q',old)==(seq,node,target,push);assert node<904438 and target<904438 and push>0;seeds+=1
       if seq==0:assert active is None;outside+=1;continue
       assert active is not None and seq==lastseq and target==attempts[seq][2] and pop==active['pop'] and push==active['last_push']+1;active['seeds'].add(node);active['count']+=1;active['last_push']=push
      elif tag==3:
       assert active is not None and seq==lastseq and node==active['ordinal'] and target==active['mode'] and push==active['last_push'] and pop==active['pop'] and push-active['begin_push']==active['count'];ends+=1;state['phases']+=1;state['total_seeds']+=active['count'];state['last_push']=push;state['last_pop']=pop
       if node==1:
        sink=attempts[seq][2];b=g[sink];same=[n for n in active['seeds'] if g[n][4]==b[4]];distance=min((gap(g[n][0],g[n][1],b[0],b[1])+gap(g[n][2],g[n][3],b[2],b[3]) for n in same),default=MAX);state.update(initial_count=active['count'],initial_unique=len(active['seeds']),gap=distance,same_layer=len(same))
       active=None
      else:raise AssertionError('unknown phase tag')
    flush();assert ended and not output.read(1);assert struct.unpack('<4Q',legacy.read(32))==(MAX,seeds,seeds-outside,outside) and not legacy.read(1)
   assert verified==len(attempts)-1==row['attempts'] and initial_seeds==row['initial_seed_pushes'] and undefined==row['initial_distance_undefined_attempts'] and closer==row['initial_min_gap_strictly_less_than_SOURCE_gap_attempts'] and notcloser==row['initial_min_gap_not_less_than_SOURCE_gap_attempts'];assert seeds==row['seed_pushes'] and begins==ends==row['phases'];d=row['attempt_vector'];assert sha(d['path'])==d['sha256'];a=array.array('Q');a.frombytes(Path(d['path']).read_bytes());assert a==calls and len(a)==115572 and sys.byteorder==d['byteorder'];rows.append(dict(case=case,arm=arm,attempt_records_verified=verified,phases_verified=begins,initial_seed_pushes=initial_seeds,later_seed_pushes=seeds-initial_seeds,initial_gap_undefined=undefined,initial_gap_strictly_less_than_SOURCE_gap=closer));print('INDEPENDENT INITIAL FRONTIER PASS',case,arm,verified,begins,closer,flush=True)
  bindings={str(p):sha(p) for p in [rp,Path(__file__),qp,root/'schema.json']}
  with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all6_initial_frontier_phase_CID_geometry_and_complete_attempt_records_independently_verified',bindings=bindings,rows=rows,scope='Independent original XML rectangle intervals, raw phase and legacy binary events, native call windows, complete CID vectors and every initial frontier record. Same-layer tile gaps are not directional path distances, source-only RouteCast integration or complete-time/quality gains.'),f,indent=2)
if __name__=='__main__':main()

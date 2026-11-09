"""Strict setup phase stream and exact projection to certified v1 seed events."""
import struct
from collections import Counter
from native_seed_context_replay_v1 import SeedStream,SeedError
MAX=2**64-1
class PhaseError(ValueError):pass

def replay(path,legacy,emit=None):
 old=SeedStream(legacy);records=seeds=begins=ends=outside=0;lastseq=ordinal=0;active=None;done=False;nodes=set();target=None;last_push=last_pop=0;mode_counts=Counter();retries=0
 try:
  with open(path,'rb') as f:
   if f.readline()!=b'RC_SEED_PHASE_LE64 1\n':raise PhaseError('header')
   while True:
    raw=f.read(48)
    if len(raw)!=48:raise PhaseError('truncated event/footer')
    tag,seq,node,mode,push,pop=struct.unpack('<QQQQQQ',raw)
    if tag==MAX:
     if active is not None or (seq,node,mode,push,pop)!=(records,seeds,begins,ends,outside) or begins!=ends or f.read(1):raise PhaseError('footer totals, active phase or trailing data')
     done=True;break
    records+=1
    if tag==1:
     if active is not None or not seq or mode>1:raise PhaseError('nested/invalid begin')
     if seq==lastseq:
      if node!=ordinal+1 or push<last_push or pop<last_pop:raise PhaseError('retry ordinal/counters')
     else:
      if seq!=lastseq+1 or node!=1:raise PhaseError('attempt sequence or first ordinal')
     lastseq,ordinal=seq,node;active=(seq,node,mode,push,pop);last_push,last_pop=push,pop;nodes=set();target=None;count=0;begins+=1;mode_counts[mode]+=1;retries+=node>1
    elif tag==2:
     if node>=904438 or mode>=904438 or push==0:raise PhaseError('seed bounds')
     if old.next()!=(seq,node,mode,push):raise PhaseError('legacy H projection mismatch')
     seeds+=1
     if seq:
      if active is None or seq!=active[0] or push!=last_push+1 or pop!=active[4] or (target is not None and target!=mode):raise PhaseError('seed outside phase or counter/target mismatch')
      target=mode;nodes.add(node);last_push=push;count+=1
     else:
      if active is not None:raise PhaseError('outside seed inside pending phase')
      outside+=1
    elif tag==3:
     if active is None or (seq,node,mode)!=active[:3] or push!=last_push or pop!=active[4] or push-active[3]!=count:raise PhaseError('phase end identity or counters')
     row=dict(sequence=seq,phase=node,mode=mode,target_RR=target,seed_pushes=count,unique_seed_RRs=len(nodes),begin_heap_pushes=active[3],end_heap_pushes=push,begin_heap_pops=active[4],end_heap_pops=pop)
     if emit is not None:emit(row,nodes)
     last_push,last_pop=push,pop;active=None;ends+=1
    else:raise PhaseError('unknown tag')
   if old.next() is not None or not old.done or not done:raise PhaseError('unconsumed legacy stream')
  return dict(attempts=lastseq,phase_records=records,seed_pushes=seeds,outside_seed_pushes=outside,phases=begins,additional_phases=retries,mode_phase_counts=dict(mode_counts),scope='Initial phase ordinal1 measured before heap build/search; later fallback phases distinct. Every seed push projected exactly to prior v1 stream; native attempt counter/target windows and CID identity require separate join.')
 finally:old.close()

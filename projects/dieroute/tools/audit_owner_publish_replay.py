#!/usr/bin/env python3
"""Independent owner/subscription/dirty-queue replay, bound to audited input."""
import argparse,csv,hashlib,json,mmap,struct
from collections import defaultdict,deque
from pathlib import Path
from contextlib import ExitStack
from audit_native_label_transport import crc64
from run_native_case import sha256
NONE=(1<<32)-1

def rows(p):
 with p.open() as f:return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(f)]
def verify(run,source,lanes):
 assert 1<=lanes<=8
 with ExitStack() as stack:
  def mapped(p):
   f=stack.enter_context(p.open('rb'));return stack.enter_context(mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ))
  original=mapped(source/'summary_hbm_frames.bin');directory=mapped(source/'summary_hbm_topology.bin');data=mapped(run/'events.bin')
  def header(d,t,width,crc=True):
   magic,major,minor,kind,count,size,arch,checksum,flags=struct.unpack_from('<8sHHIQQ16sQQ',d)
   assert (magic,major,minor,kind,flags)==(b'FPGAACCP',0,1,t,1) and size==count*width==len(d)-64
   if crc:
    view=memoryview(d)[64:];assert crc64(view)==checksum;view.release()
   return count,arch
  source_count,arch=header(original,0x44520024,384,False);n,topo_arch=header(directory,0x44520023,8);assert topo_arch==arch
  count,event_arch=header(data,0x44520025,384);assert event_arch==arch
  topo=[v[0] for v in struct.iter_unpack('<Q',directory[64:])];capacity=1
  while capacity<n:capacity*=2
  source_commands=set();groups={};source_starts={};prev=None
  for i in range(source_count):
   w=struct.unpack_from('<48Q',original,64+i*384);key=w[:6];source_starts.setdefault(w[0],i);op=w[16]&NONE
   if w[5]==2:
    if key!=prev:start=i;groups[start]=[]
    if op==3:groups[start].append((tuple(w[8:13]),w[17],w[16]>>32))
   elif op in (1,2,5):source_commands.add(i)
   prev=key
  assert (run/'owners.csv').read_bytes()==(source/'summary_hbm_owners.csv').read_bytes()
  assert (run/'caches.csv').read_bytes()==(source/'summary_hbm_caches.csv').read_bytes()
  inventories=defaultdict(dict);subscriptions=defaultdict(dict)
  for r in rows(run/'owners.csv'):key=r['owner'],r['node'];assert key not in inventories[r['repeat']];inventories[r['repeat']][key]=(r['occupancy'],r['history'],r['version'])
  for r in rows(run/'subscriptions.csv'):key=r['owner'],r['node'];assert key not in subscriptions[r['repeat']];subscriptions[r['repeat']][key]=(r['subscribers'],r['pending'],r['queued'])
  expected_bits=defaultdict(int)
  for r in rows(source/'summary_hbm_caches.csv'):expected_bits[r['repeat'],r['node']]|=1<<(r['worker']*8+r['lane'])
  controllers=[[0]*8 for _ in range(3)];rep=-1;call=0;states={};queues=[deque() for _ in range(3)];tickets=[0]*3;ur=[0]*3;uw=[0]*3;delivered=defaultdict(list);pump_dies=defaultdict(set);totals=defaultdict(int);digests=[];digest=None
  def finish():
   if rep<0:return
   actual={};subs={}
   for slot,t in enumerate(topo):
    node,mask=t&NONE,t>>32;owner=(mask&-mask).bit_length()-1;value,bits,pending=states[owner,slot]
    actual[owner,node]=value;subs[owner,node]=(bits,pending,int(bool(pending)));assert not pending and bits==expected_bits[rep,node]
   assert actual==inventories[rep] and subs==subscriptions[rep] and all(not q for q in queues)
   digests.append(digest.hexdigest())
  def normalize(w):
   w=list(w);w[0]=0;w[1]-=source_starts[rep]
   if w[5]==0:w[8]=w[24]=w[47]=1
   elif w[5]==1:
    w[16]=0 if w[16]==rep else 1;w[24]=w[39]=1
   else:w[8]=1
   digest.update(struct.pack('<48Q',*w))
  i=0
  while i<count:
   w=list(struct.unpack_from('<48Q',data,64+i*384));meta=w[:8];newrep,source_index,actor,reason,die,kind,callid,ordinal=meta
   if newrep!=rep:
    finish();assert newrep==rep+1;rep=newrep;states={};queues=[deque() for _ in range(3)];tickets=[0]*3;ur=[0]*3;uw=[0]*3;call=0;digest=hashlib.sha256()
   assert callid==call and ordinal==0 and die<3 and kind in (0,1)
   original_words=struct.unpack_from('<48Q',original,64+source_index*384)
   assert (rep,actor,reason)==(original_words[0],original_words[3],original_words[5])
   p,d,r,ack,done=[w[x:x+8] for x in (8,16,24,32,40)]
   if kind==0:
    assert source_index in source_commands;source_commands.remove(source_index)
    assert die==original_words[7] and p==list(original_words[8:16])
    original_descriptor=list(original_words[16:24]);op=original_descriptor[0]&NONE
    if op==2:original_descriptor[0]=6|(actor<<32)
    assert d==original_descriptor and r==list(original_words[24:32])
    if controllers[die][0]!=rep+1:controllers[die]=[rep+1,0,0,0,0,0,0,0]
    ctl=controllers[die];slot=d[1];node,mask=topo[slot]&NONE,topo[slot]>>32;worker=p[1]>>40&255;lane=d[0]>>32
    assert node==p[1]&NONE and die==(mask&-mask).bit_length()-1 and mask&(1<<worker) and worker!=die and lane<lanes
    old,bits,pending=states.get((die,slot),(None,0,0));value=tuple(p[2:5]);reply=list(p);status=0;write=0
    if op==1:
     assert d[2]==(old[2] if old else 0)
     if old and value[2]<=old[2]:status=2 if value[2]<old[2] else 1 if value==old else 8
     else:
      if bits and not pending:queues[die].append(slot);ctl[2]+=1
      pending|=bits;old=value;write=1
    else:
     assert old is not None
     if op==5:status=int(value!=old)*2
     else:
      assert op==2;bit=1<<(worker*8+lane);write=int(not bits&bit);bits|=bit;reply[1]=(reply[1]&~(255<<48))|(2<<48);reply[2:5]=old
    states[die,slot]=(old,bits,pending);ticket=tickets[die];tickets[die]+=1
    assert r==reply and ack==[status,ticket,d[0],slot,write,0,0,0] and done==[ticket+1,ticket+1,uw[die],1,0,0,0,rep+1]
    totals['owner_commands']+=1;totals['stale_validations']+=int(status==2);normalize(w);i+=1
   else:
    assert reason==2 and source_index in groups and actor<lanes;config,before,after,completion,reserved=p,d,r,ack,done
    filter_mask=sum(1<<(worker*8+actor) for worker in range(3));assert config==[filter_mask,8,capacity*65,ur[die],uw[die],tickets[die],0,0] and reserved==[0]*8
    assert before==controllers[die]
    if before[0]!=rep+1:controllers[die]=[rep+1,0,0,0,0,0,0,0]
    ctl=controllers[die];q=queues[die];initial=len(q);retired=visits=0;expected=[]
    while retired<initial and visits<config[2] and len(expected)<8:
     slot=q[0];value,bits,pending=states[die,slot];eligible=pending&filter_mask
     if not eligible:q.rotate(-1);ctl[1]+=1;ctl[2]+=1;retired+=1;visits+=1;continue
     bit=(eligible&-eligible).bit_length()-1;worker,lane=divmod(bit,8)
     packet=[rep+1,(topo[slot]&NONE)|(die<<32)|(worker<<40)|(3<<48),*value,uw[die]+1,0,0];metadata=[lane,slot,value[2],0,0,0,0,0];expected.append((packet,metadata));uw[die]+=1;visits+=1;pending&=~(1<<bit);states[die,slot]=(value,bits,pending)
     if not pending:q.popleft();ctl[1]+=1;retired+=1
    assert after==ctl and completion==[tickets[die],tickets[die],uw[die],0,len(expected),visits,0,rep+1]
    normalize(w);i+=1
    for ordinal,(packet,metadata) in enumerate(expected):
     update=list(struct.unpack_from('<48Q',data,64+i*384));assert update[:8]==[rep,source_index,actor,reason,die,2,callid,ordinal] and update[8:16]==packet and update[16:24]==metadata and update[24:]==[0]*24
     delivered[source_index].append((tuple(packet[:5]),metadata[1],metadata[0]));normalize(update);i+=1
    ur[die]=uw[die];pump_dies[source_index].add(die);totals['pump_launches']+=1;totals['dirty_queue_visits']+=visits;totals['published_updates']+=len(expected)
   assert len(queues[die])==controllers[die][2]-controllers[die][1] and len(set(queues[die]))==len(queues[die]);call+=1
  finish();assert not source_commands and set(pump_dies)==set(groups) and all(v=={0,1,2} for v in pump_dies.values())
  for source_index,expected in groups.items():assert sorted(delivered[source_index])==sorted(expected),'push values differ from independently audited scan publications'
  assert len(set(digests))==1 and len(digests)==len(inventories)
  return dict(passed=True,repeats=len(digests),boundary_slots=n,events=count,totals=dict(totals),normalized_repeat_sha256=digests,all_source_owner_commands_bound=True,changed_publications_equal_source=True,final_owner_and_cache_files_equal_source=True,subscriptions_match_actual_cached_records=True,scope='Independent replay of replacement owner/subscription/publisher state machine against previously audited native input; not a fresh router execution or board result')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists()
 manifest=json.loads((a.run/'manifest.json').read_text());assert manifest['status']=='passed' and manifest['inputs_unchanged'];source=Path(manifest['source_run'])/'route'
 for p,h in manifest['inputs'].items():assert sha256(p)==h,p
 for p,h in manifest['artifacts'].items():assert sha256(a.run/p)==h,p
 result=verify(a.run/'replay',source,manifest['lanes'])
 for p,h in manifest['inputs'].items():assert sha256(p)==h,p
 result['inputs']=dict(manifest['inputs']);result['inputs'][str((a.run/'manifest.json').resolve())]=sha256(a.run/'manifest.json');result['inputs_unchanged']=True;result['auditor_sha256']=sha256(__file__)
 a.output.mkdir();import shutil;shutil.copy2(__file__,a.output/Path(__file__).name);(a.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
if __name__=='__main__':main()

"""Independent live publisher replay and binding to native observations/commits."""
import hashlib,mmap,struct
from collections import defaultdict,deque
from pathlib import Path
from audit_native_summary_hbm import rows,header,NONE

def replay_push(route,command):
    assert len(command)==24 and int(command[23])==2 and int(command[22])>0
    lanes,repeats,arch=int(command[21]),int(command[11]),command[6]
    raw=(route/'summary_hbm_topology.bin').read_bytes();header(raw,0x44520023,8,arch)
    topo=[x[0] for x in struct.iter_unpack('<Q',raw[64:])];ids=[t&NONE for t in topo];assert ids==sorted(set(ids))
    with (Path(command[1])/'nodes.bin').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as nodes:
        expected=[];domain=0
        for n in range(len(nodes)//64):
            mask=struct.unpack_from('<I',nodes,n*64+20)[0];domain|=mask
            if mask&(mask-1):expected.append(n|(mask<<32))
        assert topo==expected,'publisher directory differs from complete native boundary set'
    dies=domain.bit_length();assert 1<=dies<=8 and 1<=lanes<=8
    capacity=1
    while capacity<len(topo):capacity*=2
    def key(r):return tuple(r[x] for x in ('repeat','iteration','wave','slot','attempt'))
    reads=defaultdict(list)
    for r in rows(route/'persistent_shadow_reads.csv'):reads[key(r)].append((r['worker'],r['node'],r['occupancy'],r['history'],r['version'],r['hit']))
    checks={key(r):(r['queries'],r['stale']) for r in rows(route/'persistent_shadow_checks.csv')}
    refresh_keys=[key(r) for r in rows(route/'persistent_shadow_publications.csv')];assert len(set(refresh_keys))==len(refresh_keys)
    owners_csv=defaultdict(dict);cache_csv=defaultdict(dict);subs_csv=defaultdict(dict);native={}
    for r in rows(route/'summary_hbm_owners.csv'):
        assert r['node'] not in owners_csv[r['repeat']];owners_csv[r['repeat']][r['node']]=(r['owner'],r['occupancy'],r['history'],r['version'])
    for r in rows(route/'summary_hbm_caches.csv'):
        k=r['worker'],r['lane'],r['node'];assert k not in cache_csv[r['repeat']];cache_csv[r['repeat']][k]=(r['occupancy'],r['history'],r['version'])
    for r in rows(route/'summary_hbm_subscriptions.csv'):
        assert r['node'] not in subs_csv[r['repeat']];subs_csv[r['repeat']][r['node']]=(r['owner'],r['subscribers'],r['pending'],r['queued'])
    for r in rows(route/'owner_usage.csv'):
        u=native.setdefault((r['repeat'],r['node']),[set(),r['history'],r['version']]);assert u[1:]==[r['history'],r['version']]
        if r['net']!=NONE:u[0].add(r['net'])
    logical_query=defaultdict(list);logical_updates=defaultdict(list)
    raw=(route/'worker_shadow_messages.bin').read_bytes();header(raw,0x44520022,128,arch)
    for off in range(64,len(raw),128):
        m=struct.unpack_from('<8Q',raw,off);p=tuple(struct.unpack_from('<8Q',raw,off+64))
        if m[5]==0:logical_query[m[:5]].append(p)
        else:assert m[5] in (1,2,3) and p[1]>>48&255==3;logical_updates[m[:5]].append(p)
    publications=defaultdict(list);totals=defaultdict(int);op_counts=defaultdict(int);digests=[]
    seen_reads=defaultdict(list);validations=defaultdict(list);cold={};observed_query=defaultdict(list);observed_updates=defaultdict(list);generated=defaultdict(list);pumped=defaultdict(set)
    controllers=[[0]*8 for _ in range(dies)];owners={};cache={};bits={};pending={};queues=[deque() for _ in range(dies)];uw=[0]*dies;tickets=defaultdict(int)
    rep=-1;sequence=0;digest=None;expected_updates=deque()
    def touch(die):
        if controllers[die][0]!=rep+1:controllers[die]=[rep+1,0,0,0,0,0,0,0];queues[die].clear()
        return controllers[die]
    def finish():
        if rep<0:return
        assert not expected_updates and not cold and set(owners)==set(ids)
        actual={n:((topo[s]>>32&-(topo[s]>>32)).bit_length()-1,*owners[n]) for s,n in enumerate(ids)}
        assert actual==owners_csv[rep] and cache==cache_csv[rep]
        expected_bits=defaultdict(int)
        for (worker,lane,n),value in cache.items():assert value==owners[n];expected_bits[n]|=1<<(worker*8+lane)
        actual_subs={}
        for s,n in enumerate(ids):
            nets,h,v=native.get((rep,n),(set(),0,0));assert owners[n]==(len(nets),h,v)
            assert bits.get(n,0)==expected_bits[n] and pending.get(n,0)==0
            actual_subs[n]=(actual[n][0],bits.get(n,0),0,0)
        assert actual_subs==subs_csv[rep] and all(not q for q in queues)
        digests.append(digest.hexdigest())
    path=route/'summary_hbm_frames.bin'
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
        count=header(data,0x44520024,384,arch)
        for off in range(64,len(data),384):
            w=list(struct.unpack_from('<48Q',data,off));newrep,epoch,wave,actor,attempt,reason,seq,die=w[:8];p,d,r,ack,done=[w[i:i+8] for i in (8,16,24,32,40)];k=(newrep,epoch,wave,actor,attempt)
            if newrep!=rep:
                finish();assert newrep==rep+1 and newrep<repeats;rep=newrep;sequence=0;digest=hashlib.sha256();owners={};cache={};bits={};pending={};queues=[deque() for _ in range(dies)];uw=[0]*dies;tickets=defaultdict(int)
            assert seq==sequence and actor<=lanes and die<dies and reason<=5;sequence+=1;w[0]=0
            if reason==5:
                assert expected_updates;expected_key,expected_die,packet,metadata=expected_updates.popleft()
                assert k==expected_key and die==expected_die and p==packet and d==metadata and r==ack==done==[0]*8
                generated[k].append(tuple(p));w[8]=1;digest.update(struct.pack('<48Q',*w));continue
            assert not expected_updates,'publisher output records missing before next call'
            if reason==4:
                assert actor<lanes and k in refresh_keys
                config,before,after,completion,reserved=p,d,r,ack,done
                assert config==[sum(1<<(worker*8+actor) for worker in range(dies)),8,capacity*65,uw[die],uw[die],tickets[actor,die],0,0] and reserved==[0]*8
                assert before==controllers[die];ctl=touch(die);q=queues[die];initial=len(q);retired=visits=0;produced=[]
                while retired<initial and visits<config[2] and len(produced)<8:
                    slot=q[0];n=ids[slot];eligible=pending[n]&config[0]
                    if not eligible:q.rotate(-1);ctl[1]+=1;ctl[2]+=1;retired+=1;visits+=1;continue
                    bit=(eligible&-eligible).bit_length()-1;worker,lane=divmod(bit,8)
                    packet=[rep+1,n|(die<<32)|(worker<<40)|(3<<48),*owners[n],uw[die]+1,0,0];metadata=[lane,slot,owners[n][2],0,0,0,0,0]
                    produced.append((packet,metadata));uw[die]+=1;visits+=1;pending[n]&=~(1<<bit)
                    if not pending[n]:q.popleft();ctl[1]+=1;retired+=1
                assert after==ctl and completion==[tickets[actor,die],tickets[actor,die],uw[die],0,len(produced),visits,0,rep+1]
                expected_updates.extend((k,die,packet,metadata) for packet,metadata in produced);pumped[k].add(die)
                totals['pump_launches']+=1;totals['dirty_queue_visits']+=visits;totals['published_updates']+=len(produced)
                w[16]=0 if before[0]==rep else 1;w[24]=w[39]=1;digest.update(struct.pack('<48Q',*w));continue
            assert p[0]==rep+1 and p[1]>>56==0 and p[5]>0 and p[6:]==[0,0] and p[3]<(1<<64)-1
            op,lane=d[0]&NONE,d[0]>>32;slot=d[1];assert slot<len(topo) and lane<lanes and d[3:]==[0]*5 and (op==1 or d[2]==0)
            n,owner,worker,kind=p[1]&NONE,p[1]>>32&255,p[1]>>40&255,p[1]>>48&255;mask=topo[slot]>>32
            assert n==ids[slot] and owner==(mask&-mask).bit_length()-1 and worker!=owner and mask&(1<<worker)
            local=op in (1,5,6);assert op in (1,3,4,5,6) and die==(owner if local else worker) and (lane==(actor if op in (3,4,6) else 0))
            assert (kind==1 and p[2:5]==[0,0,0]) if op in (4,6) else kind in (2,3)
            old=owners.get(n) if local else cache.get((worker,lane,n));value=tuple(p[2:5]);reply=list(p);status=write=0
            if local:ctl=touch(die)
            if op==1 and d[2]!=(old[2] if old else 0):status=7
            elif op in (1,3):
                if old and value[2]<old[2]:status=2
                elif old and value[2]==old[2]:status=1 if value==old else 8
                else:
                    write=1
                    if local:
                        if bits.get(n,0) and not pending.get(n,0):queues[die].append(slot);ctl[2]+=1
                        pending[n]=pending.get(n,0)|bits.get(n,0);owners[n]=value
                    else:cache[worker,lane,n]=value
            elif old is None:status=6
            elif op==5:status=0 if value==old else 2
            else:
                reply[1]=(p[1]&~(255<<48))|(2<<48);reply[2:5]=old
                if op==6:
                    bit=1<<(worker*8+lane);write=int(not bits.get(n,0)&bit);bits[n]=bits.get(n,0)|bit
            ticket=tickets[actor,die];tickets[actor,die]+=1
            assert r==reply and ack==[status,ticket,d[0],slot,write,0,0,0]
            assert done==([ticket+1,ticket+1,uw[die],1,0,0,0,rep+1] if local else [ticket+1,ticket+1,1,0,write,int(status not in (0,1)),rep+1,0])
            op_counts[op]+=1;totals['commands']+=1;totals['writes']+=write;totals['rejections']+=int(status not in (0,1))
            if reason==1:
                assert op==1 and actor==lanes and status==0;publications[rep,epoch,wave,attempt].append((n,value))
            elif reason==0:
                assert actor<lanes and status==0
                if op==6:assert k not in cold;cold[k]=list(r);observed_query[k].extend((tuple(p),tuple(r)))
                elif op==3:assert cold.pop(k)==p;seen_reads[k].append((worker,n,*value,0))
                else:assert op==4 and k not in cold;seen_reads[k].append((worker,n,*r[2:5],1))
            elif reason==3:
                assert op==5 and actor<lanes and status in (0,2);validations[k].append((worker,n,*value,int(status==2)))
            else:
                assert reason==2 and actor<lanes and op==3 and status==0 and kind==3;observed_updates[k].append(tuple(p))
            assert len(queues[die])==controllers[die][2]-controllers[die][1] and len(queues[die])<=capacity
            w[8]=w[24]=1;w[47 if local else 46]=1;digest.update(struct.pack('<48Q',*w))
        finish();assert count==totals['commands']+totals['pump_launches']+totals['published_updates']
    assert len(digests)==repeats and len(set(digests))==1
    assert dict(seen_reads)=={k:v for k,v in reads.items() if v} and dict(observed_query)==dict(logical_query)
    for k,(queries,stale) in checks.items():
        v=validations.pop(k,[]);assert len(v)==queries and sum(x[-1] for x in v)==stale and [x[:-1] for x in v]==[x[:-1] for x in reads.get(k,[])]
    assert not validations and dict(observed_updates)==dict(logical_updates)
    assert set(pumped)==(set(refresh_keys) if topo else set()) and all(v==set(range(dies)) for v in pumped.values())
    for k in refresh_keys:
        produced=sorted(generated.pop(k,[]),key=lambda p:(p[1]>>40&255,p[1]&NONE));delivered=observed_updates.get(k,[])
        assert len(produced)==len(delivered)
        for a,b in zip(produced,delivered):assert a[:5]+a[6:]==b[:5]+b[6:],'hardware update differs from actual received value'
    assert not generated
    return dict(publications=publications,totals=totals,digests=digests,op_counts=dict(op_counts),slots=len(topo),publisher=dict(enabled=True,host_polling_scans=0,raw_updates_bound_to_logical_delivery=True,subscription_and_pending_inventory_verified=True,queue_model_replayed=True))

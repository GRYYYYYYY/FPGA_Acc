"""Replay live endpoint commands and bind owner installations to CPU commits."""
import csv,hashlib,mmap,struct
from collections import defaultdict
from pathlib import Path
from audit_native_label_transport import crc64
NONE=(1<<32)-1

def rows(path):
    with path.open() as f:return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(f)]
def header(data,kind,width,arch):
    m,major,minor,t,n,size,a,crc,flags=struct.unpack_from('<8sHHIQQ16sQQ',data)
    assert (m,major,minor,t,flags)==(b'FPGAACCP',0,1,kind,1) and a.hex()==arch and size==n*width==len(data)-64
    view=memoryview(data)[64:];assert crc64(view)==crc;view.release();return n
class SummaryEndpointAudit:
    def __init__(self,route,command):
        self.enabled=len(command)==24 and int(command[23]) in (1,2);self.publications=defaultdict(list);self.totals=defaultdict(int);self.digests=[]
        if not self.enabled:return
        if int(command[23])==2:
            from audit_native_owner_publish import replay_push
            self.__dict__.update(replay_push(route,command));return
        assert int(command[22])>0;lanes=int(command[21]);repeats=int(command[11]);arch=command[6]
        topo_data=(route/'summary_hbm_topology.bin').read_bytes();header(topo_data,0x44520023,8,arch);topo=[x[0] for x in struct.iter_unpack('<Q',topo_data[64:])];ids=[v&NONE for v in topo];assert ids==sorted(set(ids))
        with (Path(command[1])/'nodes.bin').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as nodes:
            expected=[]
            for n in range(len(nodes)//64):
                mask=struct.unpack_from('<I',nodes,n*64+20)[0]
                if mask&(mask-1):expected.append(n|(mask<<32))
            assert topo==expected,'endpoint directory is not the complete native boundary set'
        reads=defaultdict(list)
        for r in rows(route/'persistent_shadow_reads.csv'):reads[tuple(r[x] for x in ('repeat','iteration','wave','slot','attempt'))].append((r['worker'],r['node'],r['occupancy'],r['history'],r['version'],r['hit']))
        checks={tuple(r[x] for x in ('repeat','iteration','wave','slot','attempt')):(r['queries'],r['stale']) for r in rows(route/'persistent_shadow_checks.csv')}
        expected_owners=defaultdict(dict);expected_caches=defaultdict(dict)
        for r in rows(route/'summary_hbm_owners.csv'):key=r['node'];assert key not in expected_owners[r['repeat']];expected_owners[r['repeat']][key]=(r['owner'],r['occupancy'],r['history'],r['version'])
        for r in rows(route/'summary_hbm_caches.csv'):key=(r['worker'],r['lane'],r['node']);assert key not in expected_caches[r['repeat']];expected_caches[r['repeat']][key]=(r['occupancy'],r['history'],r['version'])
        native_uses={}
        for r in rows(route/'owner_usage.csv'):
            u=native_uses.setdefault((r['repeat'],r['node']),[set(),r['history'],r['version']]);assert u[1:]==[r['history'],r['version']]
            if r['net']!=NONE:u[0].add(r['net'])
        seen_reads=defaultdict(list);validations=defaultdict(list);pending={};op_counts=defaultdict(int)
        owners={};cache={};tickets=defaultdict(int);rep=-1;sequence=0;digest=None
        def finish():
            if rep<0:return
            assert set(owners)==set(ids)
            actual={n:((topo[slot]>>32&-(topo[slot]>>32)).bit_length()-1,*owners[n]) for slot,n in enumerate(ids)}
            assert actual==expected_owners[rep] and cache==expected_caches[rep]
            for n,value in owners.items():
                nets,h,v=native_uses.get((rep,n),(set(),0,0));assert value==(len(nets),h,v)
            assert all(value==owners[n] for (worker,lane,n),value in cache.items())
            self.digests.append(digest.hexdigest())
        path=route/'summary_hbm_frames.bin'
        with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
            count=header(data,0x44520024,384,arch)
            for off in range(64,len(data),384):
                w=list(struct.unpack_from('<48Q',data,off));meta=w[:8];p,d,r,ack,done=[w[i:i+8] for i in (8,16,24,32,40)]
                newrep,epoch,wave,actor,attempt,reason,seq,die=meta
                if newrep!=rep:
                    finish();assert newrep==rep+1 and newrep<repeats;rep=newrep;sequence=0;owners={};cache={};tickets=defaultdict(int);digest=hashlib.sha256()
                assert seq==sequence;sequence+=1;assert actor<=lanes and reason in (0,1,2,3)
                assert p[0]==rep+1 and p[1]>>56==0 and p[5]>0 and p[6:]==[0,0] and p[3]<(1<<64)-1
                op,lane=d[0]&NONE,d[0]>>32;slot=d[1];assert slot<len(topo) and lane<lanes and d[3:]==[0]*5 and (op==1 or d[2]==0)
                n=p[1]&NONE;owner=(p[1]>>32)&255;worker=(p[1]>>40)&255;kind=(p[1]>>48)&255;mask=topo[slot]>>32
                assert n==ids[slot] and owner==(mask&-mask).bit_length()-1 and worker!=owner and mask&(1<<worker)
                local=op in (1,2,5);assert die==(owner if local else worker) and (local or lane==actor)
                assert op in range(1,6) and (kind==1 and p[2:5]==[0,0,0] if op in (2,4) else kind in (2,3))
                old=owners.get(n) if local else cache.get((worker,lane,n));value=tuple(p[2:5]);reply=list(p);status=0;write=0
                if op==1 and d[2]!=(old[2] if old else 0):status=7
                elif op in (1,3):
                    if old and value[2]<old[2]:status=2
                    elif old and value[2]==old[2]:status=1 if value==old else 8
                    else:
                        write=1
                        if local:owners[n]=value
                        else:cache[worker,lane,n]=value
                elif old is None:status=6
                elif op==5:status=0 if value==old else 2
                else:reply[1]=(p[1]&~(255<<48))|(2<<48);reply[2:5]=old
                ticket=tickets[actor,die];tickets[actor,die]+=1
                assert r==reply and ack==[status,ticket,d[0],slot,write,0,0,0]
                assert done==[ticket+1,ticket+1,1,0,write,int(status not in (0,1)),rep+1,0]
                key=(rep,epoch,wave,actor,attempt);op_counts[op]+=1;self.totals['commands']+=1;self.totals['writes']+=write;self.totals['rejections']+=int(status not in (0,1))
                if reason==1:
                    assert op==1 and actor==lanes and status==0;self.publications[rep,epoch,wave,attempt].append((n,value))
                elif reason==0:
                    assert actor<lanes and status==0
                    if op==2:assert key not in pending;pending[key]=list(r)
                    elif op==3:assert pending.pop(key)==p;seen_reads[key].append((worker,n,*value,0))
                    else:assert op==4 and key not in pending;seen_reads[key].append((worker,n,*tuple(r[2:5]),1))
                elif reason==3:
                    assert op==5 and status in (0,2);validations[key].append((worker,n,*value,int(status==2)))
                else:assert op in (2,3,4) and actor<lanes and status==0
                w[0]=0;w[8]=w[24]=w[46]=1;digest.update(struct.pack('<48Q',*w))
            finish();assert count==self.totals['commands']
        assert len(self.digests)==repeats and len(set(self.digests))==1 and not pending
        assert dict(seen_reads)=={k:v for k,v in reads.items() if v}
        for key,(queries,stale) in checks.items():
            declared=validations.pop(key,[]);assert len(declared)==queries and sum(x[-1] for x in declared)==stale
            assert [x[:-1] for x in declared]==[x[:-1] for x in reads.get(key,[])]
        assert not validations
        self.op_counts=dict(op_counts);self.slots=len(topo)
    def publication(self,key,uses):
        for n,value in self.publications.pop(key,[]):
            nets,h,v=uses.get(n,(frozenset(),0,0));assert value==(len(nets),h,v),'owner install does not match actual coordinator state'
    def finish(self):
        assert not self.publications
        return dict(enabled=self.enabled,totals=dict(self.totals),operation_counts=getattr(self,'op_counts',{}),boundary_slots=getattr(self,'slots',0),repeat_sha256=self.digests,owner_installations_match_coordinator=self.enabled,actual_query_and_validation_values_bound=self.enabled,final_hardware_tables_match_authority=self.enabled,owner_publisher=getattr(self,'publisher',None),scope='Live endpoint command/state and native transaction replay; CPU still owns full net sets and atomic commits; no asynchronous hardware or timing claim')

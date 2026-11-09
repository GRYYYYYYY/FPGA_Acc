"""Independent per-lane persistent-summary delivery and consumption replay."""
import csv,hashlib,struct
from collections import defaultdict
from bisect import bisect_left
from audit_native_label_transport import crc64
NONE=(1<<32)-1

def grouped(path,fields):
    if not path.exists():return {}
    out=defaultdict(list)
    with path.open() as f:
        for r in csv.DictReader(f):
            r={k:int(v) for k,v in r.items()};assert all(v>=0 for v in r.values());out[tuple(r[k] for k in fields)].append(r)
    return dict(out)

class PersistentShadowAudit:
    def __init__(self,route,command):
        self.push=len(command)==24 and int(command[23])==2
        self.period=int(command[22]) if len(command)>=23 else 0
        self.workers=int(command[21]);self.repeats=int(command[11]);self.messages=defaultdict(list);self.total=defaultdict(int)
        key=('repeat','iteration','wave','slot','attempt')
        self.reads=grouped(route/'persistent_shadow_reads.csv',key)
        self.checks=grouped(route/'persistent_shadow_checks.csv',key)
        self.branches=grouped(route/'persistent_shadow_branches.csv',key)
        self.publications=grouped(route/'persistent_shadow_publications.csv',(*key,'reason'))
        for table in (self.reads,self.checks,self.branches,self.publications):
            flat=[r for records in table.values() for r in records]
            reference=[{k:v for k,v in r.items() if k!='repeat'} for r in flat if r['repeat']==0]
            for rep in range(1,self.repeats):assert [{k:v for k,v in r.items() if k!='repeat'} for r in flat if r['repeat']==rep]==reference
        path=route/'worker_shadow_messages.bin'
        if not path.exists():assert not self.period;return
        data=path.read_bytes();magic,major,minor,kind,count,size,arch,crc,flags=struct.unpack_from('<8sHHIQQ16sQQ',data)
        assert (magic,major,minor,kind,flags)==(b'FPGAACCP',0,1,0x44520022,1)
        assert arch.hex()==command[6] and size==128*count==len(data)-64 and crc64(memoryview(data)[64:])==crc
        digests=[hashlib.sha256() for _ in range(self.repeats)]
        for off in range(64,len(data),128):
            prefix=struct.unpack_from('<8Q',data,off);p=struct.unpack_from('<8Q',data,off+64);key=prefix[:6];rep=key[0]
            assert rep<self.repeats and prefix[7]==0 and prefix[6]==len(self.messages[key])
            assert p[0]==rep+1 and p[1]>>56==0 and p[5]>0 and p[6:]==(0,0)
            self.messages[key].append(p)
            digests[rep].update(struct.pack('<7Q',*prefix[1:]));digests[rep].update(struct.pack('<7Q',*p[1:]))
        assert len({h.digest() for h in digests})==1
        self.normalized_sha256=digests[0].hexdigest();self.packet_count=count
        if not self.period:assert not count and not any((self.reads,self.checks,self.branches,self.publications))
    @staticmethod
    def value(uses,n):
        nets,h,v=uses.get(n,(frozenset(),0,0));return len(nets),h,v
    def start(self,rep,member):
        self.rep=rep;self.member=member;self.cache=[{} for _ in range(self.workers)];self.serial=[0]*self.workers
    def check_packet(self,p,slot,n,worker,kind,value):
        owner=(self.member(n)&-self.member(n)).bit_length()-1
        assert p[1]==n|(owner<<32)|(worker<<40)|(kind<<48)
        assert p[2:5]==value and p[5]==self.serial[slot]
    def refresh(self,key,window,uses):
        if not self.period:return
        row,=self.publications.pop(key);slot=key[3];cache=self.cache[slot]
        assert row['window']==window and row['retained']==len(cache) and row['scans']==(0 if self.push else len(cache))
        packets=self.messages.pop(key,[])
        changed=[(worker,n) for worker,n in sorted(cache) if cache[worker,n]!=self.value(uses,n)]
        assert len(packets)==row['messages']==len(changed)
        for p,(worker,n) in zip(packets,changed):
            value=self.value(uses,n);assert value[2]>cache[worker,n][2]
            self.serial[slot]+=1;self.check_packet(p,slot,n,worker,3,value);cache[worker,n]=value
        self.total['publications']+=1;self.total['publication_scans']+=row['scans'];self.total['updates']+=len(changed)
        if key[-1]==3:self.total['tail_updates']+=len(changed)
        if key[-1]==2:self.total['forced_refreshes']+=1
    def window(self,rep,epoch,wave,window,uses):
        if self.period and window%self.period==0:
            for slot in range(self.workers):self.refresh((rep,epoch,wave,slot,0,1),window,uses)
    def replay(self,key,window,uses):
        if self.period:self.refresh((*key,2),window,uses)
    def proposal(self,key,snapshot,current,footprint,branch_count):
        self.observed={};self.flags={}
        if not self.period:return 0
        slot=key[3];cache=self.cache[slot];packets=self.messages.pop((*key,0),[]);cursor=0
        rows=self.reads.pop(key,[]);checks,=self.checks.pop(key);assert [r['query'] for r in rows]==list(range(len(rows)))
        previous_branch=0;stale=0;snapshot_stale=0
        for r in rows:
            worker,n=r['worker'],r['node'];mask=self.member(n);owner=(mask&-mask).bit_length()-1
            assert worker<8 and worker!=owner and mask&(1<<worker) and mask&(mask-1)
            assert previous_branch<=r['branch']<=branch_count;previous_branch=r['branch']
            index=bisect_left(footprint,n);assert index<len(footprint) and footprint[index]==n
            seen=r['occupancy'],r['history'],r['version']
            entry=(worker,n);assert r['hit']==int(entry in cache)
            if entry not in cache:
                assert cursor+2<=len(packets);request,reply=packets[cursor:cursor+2];cursor+=2
                self.serial[slot]+=1;self.check_packet(request,slot,n,worker,1,(0,0,0))
                value=self.value(snapshot,n);self.check_packet(reply,slot,n,worker,2,value);cache[entry]=value;self.total['fetches']+=1
            else:self.total['hits']+=1
            assert seen==cache[entry], 'search read differs from delivered persistent summary'
            observed_key=(r['branch'],worker,n)
            assert observed_key not in self.observed or self.observed[observed_key]==seen
            self.observed[observed_key]=seen;stale+=seen!=self.value(current,n);snapshot_stale+=seen!=self.value(snapshot,n)
        assert cursor==len(packets) and checks['queries']==len(rows) and checks['stale']==stale
        flags=self.branches.pop(key,[]);assert [r['branch'] for r in flags]==list(range(branch_count))
        for r in flags:assert r['shadow_path'] in (0,1);self.flags[r['branch']]=r['shadow_path']
        self.total['queries']+=len(rows);self.total['stale_observations']+=stale;self.total['stale_proposals']+=bool(stale)
        self.total['snapshot_stale_observations']+=snapshot_stale;self.total['cache_stale_proposals']+=bool(snapshot_stale)
        return stale
    def edge_cost(self,branch,node,die,present):
        if not self.period or not self.flags[branch]:return None
        owner=(self.member(node)&-self.member(node)).bit_length()-1
        if die==owner:return None
        occupancy,history,version=self.observed[branch,die,node]
        # A new branch destination cannot already be in this net's input tree.
        return 1+history+present*occupancy
    def end(self,rep,window,uses):
        if not self.period:return
        for slot in range(self.workers):
            self.refresh((rep,NONE,window,slot,0,3),window,uses)
            assert all(value==self.value(uses,n) for (worker,n),value in self.cache[slot].items()),'undrained summary tail'
            self.total['retained_entries']+=len(self.cache[slot])
    def finish(self):
        assert not any((self.messages,self.reads,self.checks,self.branches,self.publications))
        packets=2*self.total['fetches']+self.total['updates'];assert packets==getattr(self,'packet_count',0)
        return dict(enabled=bool(self.period),period=self.period,totals=dict(self.total),packets=packets,payload_bytes=packets*64,
                    normalized_repeat_sha256=getattr(self,'normalized_sha256',None),complete_tail_verified=bool(self.period),
                    limits='Per-lane caches persist across CPU proposals; publication occurs between joined phases. Captured traffic includes fetch request/reply and updates; validation traffic, HBM latency and physical framing are not modeled.')

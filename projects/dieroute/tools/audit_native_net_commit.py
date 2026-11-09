"""Replay online kernel authority, bind proposals and unchanged publisher deltas."""
import copy,csv,mmap,struct,os,subprocess,hashlib
from collections import defaultdict,Counter
from pathlib import Path
from contextlib import ExitStack
from audit_net_commit import decode,MAX,NONE,owner
from audit_native_label_transport import crc64

class SparseWords:
    def __init__(self,rows,count):self.rows=rows;self.count=count*8
    def __len__(self):return self.count
    def __getitem__(self,key):
        if isinstance(key,slice):return tuple(self[i] for i in range(*key.indices(self.count)))
        assert 0<=key<self.count
        return self.rows.get(key//8,(0,)*8)[key%8]

def rows(path):
    with Path(path).open() as f:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
def groups(records,fields):
    out=defaultdict(list)
    for r in records:out[tuple(r[x] for x in fields)].append(r)
    return out

def verify(run,command):
    assert len(command)==25 and command[23:]==['2','1'];route=Path(run)/'route';arch=bytes.fromhex(command[6]);repeats=int(command[11]);actors=int(command[21])
    keys=('repeat','iteration','wave','slot','attempt')
    tx={tuple(r[k] for k in keys):r for r in rows(route/'transactions.csv')}
    branches=groups(rows(route/'proposals.csv'),keys);paths=groups(rows(route/'proposal_paths.csv'),(*keys,'branch'));shadows=groups(rows(route/'persistent_shadow_reads.csv'),keys)
    selection=rows(route/'selection.csv');order=sorted({r['net'] for r in selection},key=lambda n:min(r['task'] for r in selection if r['net']==n));roots={r['net']:r['source'] for r in selection};slots={net:i for i,net in enumerate(order)}
    expected_ripups={(r['repeat'],r['iteration'],r['net']) for r in tx.values() if r['iteration'] and not r['attempt']};seen_ripups=set();seen_proposals=set();seen_negotiations=set();proposal_sequence={};publication_groups=[];tail_sequence={}
    iterations={(r['repeat'],r['iteration']):r for r in rows(route/'iterations.csv')};expected_negotiations={(rep,epoch) for rep,epoch in iterations if (rep,epoch+1) in iterations}
    state=dict(resources={},nets={});revision=0;present=1;rep=-1;pending={};initialized=False;counts=Counter();max_reads=0;published=defaultdict(list);finals={}
    with ExitStack() as stack:
        def mapped(path):
            f=stack.enter_context(Path(path).open('rb'));m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);return m
        def container(path,kind,width):
            m=mapped(path);h=struct.unpack_from('<8sHHIQQ16sQQ',m);assert h[:4]==(b'FPGAACCP',0,1,kind) and h[6]==arch and h[8]==1 and h[4]*width==h[5]==len(m)-64
            checker=os.environ.get('DIEROUTE_NATIVE_CRC64')
            value=int(subprocess.run([checker,str(path),'64'],check=True,capture_output=True,text=True).stdout.strip(),16) if checker else crc64(memoryview(m)[64:])
            assert value==h[7],'net authority container CRC';return m
        node_data=mapped(Path(command[1])/'nodes.bin');protection=mapped(Path(command[2])/'node_protection.bin');exclusive=mapped(Path(command[2])/'exclusive_net.bin')
        offsets=mapped(Path(command[2])/'offsets.bin');arcs=mapped(Path(command[2])/'arcs.bin');node_count=len(node_data)//64
        policy=container(route/'net_commit_policy.bin',0x44520026,8);assert len(policy)==64+8*node_count
        frozen=set();mapping=mapped(Path(command[4])/'footprint_node_map.bin');footprint=mapped(Path(command[3])/'owners.bin')
        for old,net in struct.iter_unpack('<II',footprint):
            if net not in slots:frozen.add(struct.unpack_from('<I',mapping,old*4)[0])
        boundary=[];die_mask=0
        for n in range(node_count):
            mask=struct.unpack_from('<I',node_data,n*64+20)[0];die_mask|=mask
            expected=struct.unpack_from('<I',exclusive,64+n*4)[0]|(mask<<32)|(int(bool(protection[64+n]) or n in frozen)<<40)
            assert struct.unpack_from('<Q',policy,64+n*8)[0]==expected and mask and mask<256,'policy differs from native graph/permissions'
            if mask&(mask-1):boundary.append(n)
        policy_words=memoryview(policy)[64:].cast('Q');offset_words=memoryview(offsets)[64:].cast('Q');arc_words=memoryview(arcs)[64:].cast('Q')
        def allowed(n,net):return n<node_count and not(policy_words[n]&(1<<40)) and policy_words[n]&NONE in (NONE,net)
        def edge(a,b,pip):
            lo=offset_words[a];end=offset_words[a+1];hi=end
            while lo<hi:
                mid=(lo+hi)//2;v=arc_words[mid]
                if (v&NONE,v>>32)<(b,pip):lo=mid+1
                else:hi=mid
            return lo<end and arc_words[lo]==b|(pip<<32)
        frames=container(route/'net_commit_frames.bin',0x44520025,8);pubs=container(route/'net_commit_publications.bin',0x44520027,128);readsets=mapped(route/'readsets.bin');pubpos=64;position=64;sequence=0;config=None
        while position<len(frames):
            start=position;h=struct.unpack_from('<16Q',frames,position);position+=128;cfg=struct.unpack_from('<8Q',frames,position);position+=64
            assert h[0]==sequence and h[6] in (1,2,3,4,5) and h[7]>=56 and h[1]<repeats
            if config is None:config=cfg
            assert cfg==config and cfg[:3]==(node_count,len(arc_words),die_mask.bit_length()) and cfg[4]==len(order)
            c=struct.unpack_from('<8Q',frames,position);z=struct.unpack_from('<8Q',frames,position+64);done=struct.unpack_from('<8Q',frames,position+128);ctl=struct.unpack_from('<8Q',frames,position+192);position+=256
            assert c[1]==h[6] and z[:4]==h[8:12] and done[7]==h[12] and ctl[3]==h[14] and done[0] in (0,4) and done[6]<=cfg[6]
            def take(count):
                nonlocal position
                result=memoryview(frames)[position:position+count*8].cast('Q');assert len(result)==count;position+=count*8;return result
            reads=take(h[8]*2);shadow=take(h[9]*8);branch=take(h[10]*8);path=take(h[11]*2);delta=take(h[12]*8)
            def indexed(count,capacity):
                records={};previous=-1
                for _ in range(count):
                    w=struct.unpack_from('<9Q',frames,position+len(records)*72);index=w[0];assert previous<index<capacity;previous=index;records[index]=w[1:]
                return records
            res=indexed(h[13],cfg[2]*cfg[3]);position+=h[13]*72;trees=indexed(h[14],cfg[5]);position+=h[14]*72;netrows=indexed(h[15],cfg[4]);position+=h[15]*72
            assert position-start==h[7]*8 and position<=len(frames)
            raw=dict(resources=SparseWords(res,cfg[2]*cfg[3]),trees=SparseWords(trees,cfg[5]),nets=SparseWords(netrows,cfg[4]),control=ctl)
            v=dict(header=(0,0,0,cfg[0],cfg[1],cfg[2],cfg[3],cfg[4],cfg[5]),policy=policy_words,offsets=offset_words,arcs=arc_words)
            actual=decode(v,raw,res.keys());old=copy.deepcopy(state);op=c[1];key=tuple(h[1:6]);counts[op]+=1
            assert c[2]==revision and z[5:]==(0,0,0)
            if op==1:
                if rep>=0:finals[rep]=copy.deepcopy(state);tail_sequence[rep]=sequence
                assert h[1]==rep+1 and key[1:]==(NONE,0,NONE,0) and c[0]==h[1]+1 and c[3:]==(0,0,0,1,0) and z==(0,)*8
                rep=h[1];state=dict(resources={},nets={});revision=0;present=1;pending={};initialized=False
            else:
                assert h[1]==rep and c[0]==rep+1 and c[6]==present
                slot,net=c[3:5];r=state['resources'];ns=state['nets']
                if op!=5:assert slots[net]==slot
                def insert(n,parent,pip,depth):
                    u=r.setdefault(n,dict(history=0,version=0,members=set()));assert slot not in u['members'];u['members'].add(slot);u['version']+=1;ns[slot]['tree'][n]=(parent,pip,depth)
                if op==2:
                    assert key[1:]==(NONE,0,net,0) and slot not in ns and c[7]==roots[net] and not c[5] and z==(0,)*8 and allowed(c[7],net)
                    assert not r.get(c[7],{}).get('members');ns[slot]=dict(id=net,root=c[7],generation=1,tree={});insert(c[7],NONE,NONE,0)
                elif op==3:
                    assert key in tx and key not in seen_proposals;seen_proposals.add(key);proposal_sequence[key]=sequence;transaction=tx[key];assert transaction['net']==net and transaction['reads']==h[8] and transaction['committed']==int(done[0]==0)
                    begin=64+transaction['read_begin']*16;assert reads.cast('B')==memoryview(readsets)[begin:begin+h[8]*16],'kernel read footprint differs from actual proposal'
                    expected_shadows=[(x['node'],x['worker'],x['occupancy'],x['history'],x['version'],0,0,0) for x in shadows[key]]
                    assert list(struct.iter_unpack('<8Q',shadow))==expected_shadows
                    expected_branches=[];expected_paths=[]
                    for b in branches[key]:
                        if b['status']!=0:continue
                        pathrows=paths[key+(b['branch'],)];expected_branches.append((b['attachment'],b['sink'],len(expected_paths),len(pathrows),b['hops'],b['cost'],0,0));expected_paths.extend((x['destination']|(x['pip_key']<<32),0) for x in pathrows)
                    assert list(struct.iter_unpack('<8Q',branch))==expected_branches and list(struct.iter_unpack('<2Q',path))==expected_paths
                    observed_conflicts=0;previous=-1
                    for node,version in struct.iter_unpack('<2Q',reads):
                        assert previous<node<node_count;previous=node;observed_conflicts+=version!=r.get(node,{}).get('version',0)
                    stale=0
                    for n,worker,occ,hist,version,*unused in expected_shadows:
                        u=r.get(n,dict(history=0,version=0,members=set()));assert worker!=owner(policy_words[n]) and policy_words[n]>>32&(1<<worker)
                        stale+=(occ,hist,version)!=(len(u['members']),u['history'],u['version'])
                    changed=int(c[5]!=ns[slot]['generation']);assert done[2:6]==(h[8],observed_conflicts,stale,changed)
                    assert bool(done[0])==bool(observed_conflicts or stale or changed) and transaction['conflicts']==observed_conflicts and transaction['tree_changed']==changed and not c[7] and not z[4]
                    max_reads=max(max_reads,h[8])
                    if not done[0]:
                        added=0
                        for anchor,sink,offset,length,depth,cost,_,_ in expected_branches:
                            tree=ns[slot]['tree'];assert anchor in tree and allowed(anchor,net);parent=anchor;hops=tree[anchor][2];computed=0
                            for encoded,zero in expected_paths[offset:offset+length]:
                                n,pip=encoded&NONE,encoded>>32;assert n not in tree and allowed(n,net) and edge(parent,n,pip)
                                u=r.get(n,dict(history=0,version=0,members=set()));computed+=1+u['history']+present*len(u['members']);hops+=1;assert computed<MAX and hops<=NONE
                                insert(n,parent,pip,hops);parent=n;added+=1
                            assert (parent,hops,computed)==(sink,depth,cost)
                        if added:ns[slot]['generation']+=1
                elif op==4:
                    rk=(rep,h[2],net);assert rk in expected_ripups and rk not in seen_ripups and key[2:]==(NONE,net,0);seen_ripups.add(rk)
                    assert c[5]==ns[slot]['generation'] and not c[7] and z==(0,)*8
                    tree=ns[slot]['tree'];remove=[n for n in tree if n!=ns[slot]['root']]
                    for n in remove:del tree[n];r[n]['members'].remove(slot);r[n]['version']+=1
                    if remove:ns[slot]['generation']+=1
                elif op==5:
                    nk=(rep,h[2]);assert nk in expected_negotiations and nk not in seen_negotiations and key[2:]==(NONE,NONE,0);seen_negotiations.add(nk)
                    assert c[3:6]==(0,0,0) and c[7]==1 and z==(0,0,0,0,present*2,0,0,0) and iterations[nk]['present']==present
                    for u in r.values():
                        if len(u['members'])>1:u['history']+=len(u['members'])-1;u['version']+=1
                    present*=2
                if not done[0]:revision+=1
            if op!=3:assert done[2:6]==(0,0,0,0) and done[0]==0
            if done[0]:assert state==old and not h[12]
            assert actual['resources']==state['resources'] and actual['nets']==state['nets'],'exported hardware authority differs from independently applied commands'
            assert ctl[:3]==(rep+1,revision,present) and done[1]==revision
            expected_delta={}
            if op!=1 and not done[0]:
                for n,u in state['resources'].items():
                    if old['resources'].get(n)!=u:expected_delta[n]=(rep+1,n|(owner(policy_words[n])<<32),len(u['members']),u['history'],u['version'],revision,policy_words[n]>>32&255,0)
            observed={d[1]&NONE:d for d in struct.iter_unpack('<8Q',delta)};assert len(observed)==h[12] and observed==expected_delta
            for n,d in observed.items():
                if d[6]&(d[6]-1):pending[n]=d
            sequence+=1
            while pubpos<len(pubs):
                prefix=struct.unpack_from('<8Q',pubs,pubpos)
                assert prefix[6]>=sequence,'publication precedes its actual hardware state'
                if prefix[6]!=sequence:break
                context=prefix;values=[];publication_groups.append(context)
                while pubpos<len(pubs) and struct.unpack_from('<8Q',pubs,pubpos)==context:
                    values.append(struct.unpack_from('<8Q',pubs,pubpos+64));pubpos+=128
                assert context[0]==rep and context[3]==actors and not context[7] and context[5]==int(not initialized)
                expected=[]
                if not initialized:
                    for n in boundary:
                        u=state['resources'].get(n,dict(history=0,version=0,members=set()));expected.append((rep+1,n|(owner(policy_words[n])<<32),len(u['members']),u['history'],u['version'],revision,policy_words[n]>>32&255,0))
                else:expected=[pending[n] for n in sorted(pending)]
                assert values==expected,'publisher values are not unchanged hardware deltas/snapshot projection';pending={};initialized=True
                pk=(context[0],context[1],context[2],context[4]);published[pk].extend((d[1]&NONE,tuple(d[2:5])) for d in values)
        finals[rep]=copy.deepcopy(state);tail_sequence[rep]=sequence
        for context in publication_groups:
            rr,epoch,wave,actor,attempt,initial,source,reserved=context
            if epoch==NONE:expected_source=tail_sequence[rr];assert attempt==0
            elif attempt==0:expected_source=proposal_sequence[rr,epoch,wave,0,0]
            else:
                assert attempt>=2;expected_source=proposal_sequence[rr,epoch,wave,attempt//2-1,attempt%2]
            assert source==expected_source,'publication assigned to the wrong kernel boundary'
        assert rep+1==repeats and pubpos==len(pubs) and not pending and seen_proposals==set(tx) and seen_ripups==expected_ripups and seen_negotiations==expected_negotiations
        endpoint=mapped(route/'summary_hbm_frames.bin');installed=defaultdict(list)
        for pos in range(64,len(endpoint),384):
            w=struct.unpack_from('<48Q',endpoint,pos)
            if w[5]==1:installed[w[0],w[1],w[2],w[4]].append((w[9]&NONE,tuple(w[10:13])))
        assert dict(installed)==dict(published),'hardware publication detached from endpoint install'
        usage=groups(rows(route/'owner_usage.csv'),('repeat','node'));tree_rows=groups(rows(route/'trees.csv'),('repeat','net'))
        for rep,model in finals.items():
            assert {n for rr,n in usage if rr==rep}==set(model['resources'])
            for n,u in model['resources'].items():
                rs=usage[rep,n];assert all((x['history'],x['version'])==(u['history'],u['version']) for x in rs);assert {x['net'] for x in rs if x['net']!=NONE}=={model['nets'][s]['id'] for s in u['members']}
            for t in model['nets'].values():assert {x['node']:(x['parent'],x['pip_key'],x['depth']) for x in tree_rows[rep,t['id']]}==t['tree']
        # Release exported mmap views before ExitStack closes the mappings.
        del reads,shadow,branch,path,delta,policy_words,offset_words,arc_words,v
    checker=os.environ.get('DIEROUTE_NATIVE_CRC64')
    checker_sha256=hashlib.sha256(Path(checker).read_bytes()).hexdigest() if checker else None
    return dict(crc_checker_sha256=checker_sha256,verified=True,kernel_calls=sequence,op_counts=dict(counts),max_checked_reads=max_reads,proposals_bound=len(seen_proposals),ripups_bound=len(seen_ripups),negotiations_bound=len(seen_negotiations),publisher_values_bound=sum(map(len,published.values())),authority_transitions_replayed=True,scope='Online synthesizable kernel execution with hardware-derived snapshots and deltas; execution substrate must be established separately, not a board claim')

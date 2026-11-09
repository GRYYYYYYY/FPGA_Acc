"""Replay captured net-commit calls with an independent dictionary/tree model.

Accepted transitions, read/shadow conflict diagnostics, complete resource/tree
inventories, output deltas and rejection atomicity are independently checked.
Other negative status categories are checked by the directed C++ tests; this
replayer deliberately does not duplicate the kernel's malformed-input decoder.
Physical hash/journal placement is not used to calculate expected transitions.
"""
import argparse,copy,hashlib,json,struct,sys
from collections import Counter
from pathlib import Path

MAX=(1<<64)-1
NONE=(1<<32)-1
MAGIC=0x3130544d434e5244

def frames(path):
    assert sys.byteorder=='little'
    with Path(path).open('rb') as f:
        seq=0
        while True:
            raw=f.read(128)
            if not raw:break
            assert len(raw)==128,'truncated frame header'
            h=struct.unpack('<16Q',raw)
            assert h[0]==MAGIC and h[2]==seq and h[15]==0 and h[1]>=128,'frame header'
            body=f.read(h[1]-128);assert len(body)==h[1]-128,'truncated frame body'
            words=memoryview(body).cast('Q');pos=0
            def take(n):
                nonlocal pos
                a=words[pos:pos+n];assert len(a)==n;pos+=n;return a
            n,arcs,dies,shard,nets,trees,reads,shadows,branches,paths,scratch,deltas=h[3:15]
            assert n and 1<=dies<=8 and shard and shard&(shard-1)==0
            def state():return dict(resources=take(dies*shard*8),trees=take(trees*8),nets=take(nets*8),control=take(8))
            v=dict(header=h,policy=take(n),offsets=take(n+1),arcs=take(arcs),command=take(16),reads=take(reads*2),shadows=take(shadows*8),branches=take(branches*8),paths=take(paths*2))
            v['before']=state();v['after']=state();v['completion']=take(8);v['deltas']=take(deltas*8)
            assert pos==len(words),'frame section lengths'
            yield v
            seq+=1

def word(a,i):return tuple(a[i*8:i*8+8])
def owner(p):
    mask=p>>32&255
    assert mask
    return (mask&-mask).bit_length()-1

def decode(v,raw,resource_indices=None):
    h=v['header'];n,_,dies,shard,ncap,tcap=h[3:9];ctl=tuple(raw['control']);session=ctl[0]
    if not session:
        assert all(not x for a in raw.values() for x in a),'nonzero initial authority'
        return dict(control=ctl,resources={},nets={})
    assert ctl[5:]==(n|(dies<<32),shard|(ncap<<32),tcap) and ctl[3]<=tcap
    live=set();members={};nets={};resource={};net_ids=set()
    for s in range(ncap):
        net=word(raw['nets'],s)
        if net[0]!=session:continue
        assert net[1]<NONE and net[2]<n and 0<net[4]<=tcap and net[5] and net[6:]==(0,0)
        assert net[1] not in net_ids,'duplicate net identity';net_ids.add(net[1])
        nodes={};cursor=net[3]
        for _ in range(net[4]):
            assert cursor<ctl[3] and cursor not in live,'tree pool alias'
            live.add(cursor);e=word(raw['trees'],cursor)
            assert e[0]==session and e[1]<n and e[2]==s and e[1] not in nodes and max(e[3:6])<=NONE
            nodes[e[1]]=e[3:6];members.setdefault(e[1],{})[s]=cursor;cursor=e[6]
        assert cursor==MAX and net[2] in nodes
        for node,(parent,pip,depth) in nodes.items():
            if node==net[2]:assert (parent,pip,depth)==(NONE,NONE,0)
            else:
                assert parent in nodes and nodes[parent][2]+1==depth
                assert edge(v,parent,node,pip),'tree PIP not in graph'
        nets[s]=dict(id=net[1],root=net[2],generation=net[5],tree=nodes)
    for idx in (range(dies*shard) if resource_indices is None else resource_indices):
        r=word(raw['resources'],idx)
        if r[0]!=session:continue
        node=r[4]&NONE;assert node<n and node not in resource
        p=v['policy'][node];mask=p>>32&255
        assert not p>>41 and mask and not mask>>dies and r[4]==node|(mask<<32) and idx//shard==owner(p)
        assert r[2]<MAX and r[3] and r[6:]==(0,0)
        expected=members.get(node,{})
        assert r[1]==len(expected),'resource occupancy differs from exact membership'
        cursor=r[5];seen={}
        for _ in range(r[1]):
            assert cursor in live;entry=word(raw['trees'],cursor)
            assert entry[1]==node and entry[2] not in seen
            seen[entry[2]]=cursor;cursor=entry[7]
        assert cursor==MAX and seen==expected,'resource membership chain differs from net trees'
        resource[node]=dict(history=r[2],version=r[3],members=set(seen))
        hashed=(node*2654435761&NONE)&(shard-1)
        for probe in range(shard):
            pos=idx//shard*shard+((hashed+probe)&(shard-1))
            assert raw['resources'][pos*8]==session,'unreachable resource behind empty hash slot'
            if pos==idx:break
    assert set(members)<=set(resource),'tree membership has no resource'
    free=set();cursor=ctl[4]
    while cursor!=MAX:
        assert cursor<ctl[3] and cursor not in live|free,'free-list alias/cycle'
        free.add(cursor);e=word(raw['trees'],cursor);assert e[:7]==(0,)*7;cursor=e[7]
    assert len(live|free)==ctl[3],'lost tree pool entry'
    return dict(control=ctl,resources=resource,nets=nets)

def edge(v,parent,node,pip):
    begin,end=v['offsets'][parent:parent+2]
    assert begin<=end<=len(v['arcs'])
    # Independent scan of tiny component fixtures. Large footprint test has
    # no graph arcs. Native full-graph replay will require a bounded index.
    return any(x==(node|(pip<<32)) for x in v['arcs'][begin:end])

def audit(path):
    counts=Counter();opcounts=Counter();maxreads=0;previous=None;continuity=0
    for v in frames(path):
        k=v['header'][2];c=tuple(v['command'][:8]);z=tuple(v['command'][8:]);done=tuple(v['completion']);before=v['before'];after=v['after'];session,op,revision,slot,netid,generation,present,arg=c
        try:
            assert done[0]<=8 and done[6]<=v['header'][13] and done[7]<=v['header'][14]
            counts[done[0]]+=1;opcounts[op]+=1;maxreads=max(maxreads,done[2])
            if previous==b''.join(bytes(before[x]) for x in ('resources','trees','nets','control')):continuity+=1
            previous=b''.join(bytes(after[x]) for x in ('resources','trees','nets','control'))
            if done[0]:
                assert all(bytes(before[x])==bytes(after[x]) for x in before),'rejected call changed authority'
                assert done[1]==before['control'][1] and done[7]==0,'rejection completion'
                if done[0]!=4:continue
            old=decode(v,before);state=copy.deepcopy(old);resources=state['resources'];nets=state['nets'];ctl=list(state['control'])
            if op in (3,6):
                assert z[0]<=v['header'][9] and z[1]<=v['header'][10]
                conflicts=0;last=-1
                for i in range(z[0]):
                    node,version=v['reads'][i*2:i*2+2];assert last<node<len(v['policy']);last=node
                    conflicts+=version!=resources.get(node,{}).get('version',0)
                stale=0
                for i in range(z[1]):
                    sh=word(v['shadows'],i);r=resources.get(sh[0],dict(history=0,version=0,members=set()))
                    assert sh[1]!=owner(v['policy'][sh[0]]) and (v['policy'][sh[0]]>>32)&(1<<sh[1])
                    stale+=sh[2:5]!=(len(r['members']),r['history'],r['version'])
                changed=nets[slot]['generation']!=generation
                assert done[2:6]==(z[0],conflicts,stale,int(changed)),'read/shadow/tree conflict diagnostics'
                assert bool(done[0]==4)==bool(conflicts or stale or changed),'conflict acceptance'
                if done[0]:continue
            else:assert done[2:6]==(0,0,0,0)
            assert op in range(1,8)
            if op==1:
                assert session>ctl[0] and revision==ctl[1] and c[3:]==(0,0,0,1,0) and z==(0,)*8
                state=dict(resources={},nets={},control=(session,0,1,0,MAX,*ctl[5:]))
                actual=decode(v,after);assert actual['resources']=={} and actual['nets']=={}
                assert actual['control']==(session,0,1,0,MAX,len(v['policy'])|(v['header'][5]<<32),v['header'][6]|(v['header'][7]<<32),v['header'][8])
                assert done[1]==0 and done[7]==0;continue
            assert session==ctl[0] and revision==ctl[1] and present==ctl[2]
            if op!=5:
                if op==2:assert slot not in nets
                else:assert nets[slot]['id']==netid
            def allowed(node):
                p=v['policy'][node];return not(p&(1<<40)) and (p&NONE) in (NONE,netid)
            def insert(node,parent,pip,depth):
                r=resources.setdefault(node,dict(history=0,version=0,members=set()))
                assert slot not in r['members'] and r['version']<MAX
                r['members'].add(slot);r['version']+=1;nets[slot]['tree'][node]=(parent,pip,depth)
            if op==2:
                assert z==(0,)*8 and not generation and allowed(arg)
                assert netid not in {net['id'] for net in nets.values()},'duplicate net identity'
                assert not resources.get(arg,{}).get('members',set())
                nets[slot]=dict(id=netid,root=arg,generation=1,tree={});insert(arg,NONE,NONE,0)
            elif op==3:
                assert not arg and not z[4] and not z[5] and z[6:]==(0,0)
                readset=set(v['reads'][i*2] for i in range(z[0]));cursor=0;added=0
                for i in range(z[2]):
                    b=word(v['branches'],i);anchor,sink,offset,length,depth,cost,unused0,unused1=b
                    assert offset==cursor and length<=z[3]-cursor and not unused0 and not unused1
                    tree=nets[slot]['tree'];assert anchor in tree and allowed(anchor)
                    parent=anchor;hops=tree[anchor][2];computed=0
                    for j in range(length):
                        encoded,zero=v['paths'][(cursor+j)*2:(cursor+j)*2+2];node,pip=encoded&NONE,encoded>>32
                        assert not zero and node in readset and node not in tree and allowed(node) and edge(v,parent,node,pip)
                        r=resources.get(node,dict(history=0,version=0,members=set()))
                        computed+=1+r['history']+present*len(r['members']);hops+=1
                        assert computed<MAX and hops<=NONE
                        insert(node,parent,pip,hops);added+=1;parent=node
                    assert (parent,hops,computed)==(sink,depth,cost)
                    cursor+=length
                assert cursor==z[3]
                if added:nets[slot]['generation']+=1;assert nets[slot]['generation']<=MAX
            elif op==4:
                assert z==(0,)*8 and not arg and generation==nets[slot]['generation']
                tree=nets[slot]['tree'];root=nets[slot]['root'];removed=[n for n in tree if n!=root]
                for node in removed:
                    del tree[node];r=resources[node];r['members'].remove(slot);r['version']+=1;assert r['version']<=MAX
                if removed:nets[slot]['generation']+=1
            elif op==5:
                assert c[3:6]==(0,0,0) and z[:4]==(0,)*4 and z[4] and z[5:]==(0,)*3
                for r in resources.values():
                    if len(r['members'])>1 and arg:
                        r['history']+=arg*(len(r['members'])-1);r['version']+=1
                        assert r['history']<MAX and r['version']<=MAX
                ctl[2]=z[4]
            elif op==6:
                assert not arg and z[2:]==(0,)*6
            elif op==7:
                assert z==(0,)*8 and arg<len(v['policy'])
            if op not in (6,7):ctl[1]+=1;assert ctl[1]<=MAX
            actual=decode(v,after)
            assert actual['resources']==resources,'accepted resource state differs from abstract model'
            assert actual['nets']==nets,'accepted tree state differs from abstract model'
            assert actual['control'][:3]==tuple(ctl[:3]) and actual['control'][5:]==tuple(ctl[5:])
            if op in (6,7):assert all(bytes(before[x])==bytes(after[x]) for x in before),'read-only operation changed authority'
            assert done[1]==ctl[1]
            expected={}
            changed=[arg] if op==7 else [n for n,r in resources.items() if old['resources'].get(n)!=r]
            for n in changed:
                r=resources.get(n,dict(history=0,version=0,members=set()));p=v['policy'][n]
                expected[n]=(session,n|(owner(p)<<32),len(r['members']),r['history'],r['version'],ctl[1],p>>32&255,int(slot in r['members']) if op==7 else 0)
            observed={}
            for i in range(done[7]):
                d=word(v['deltas'],i);n=d[1]&NONE;assert n not in observed;observed[n]=d
            assert observed==expected,'delta differs from abstract committed authority'
        except (AssertionError,KeyError,IndexError) as e:
            raise AssertionError(f'frame {k}, op {op}, status {done[0]}: {e}') from e
    assert counts,'empty trace'
    digest=hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):digest.update(block)
    sha=digest.hexdigest()
    return dict(schema='dieroute.net_commit_audit.v1',status='verified',frames=sum(counts.values()),status_counts=dict(sorted(counts.items())),op_counts=dict(sorted(opcounts.items())),max_checked_reads=maxreads,consecutive_authority_handoffs=continuity,trace_sha256=sha,board_result=False,limits=['Non-conflict negative status categories are asserted by directed C++ tests, not independently reclassified here','Per-call evidence permits fixture resets and explicit boundary-state injections; this is not live native routing'])

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();result=audit(a.trace);text=json.dumps(result,indent=2)+'\n'
    if a.out:a.out.write_text(text)
    print(text,end='')
if __name__=='__main__':main()

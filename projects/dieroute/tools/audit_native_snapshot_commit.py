"""Check complete net trees and resources after exported native path publication."""
import json
import struct
import sys
from pathlib import Path

snap, art, out = map(Path,sys.argv[1:4])
meta=json.loads((snap/'snapshot.json').read_text())
slot=meta['net_slot']
def rows(directory,name):return list(struct.iter_unpack('<8Q',(directory/(name+'.raw')).read_bytes()))
before={k:rows(snap,k) for k in ('resources','trees','nets','control')}
after={k:rows(out,k) for k in before}
oldctl,newctl=before['control'][0],after['control'][0]
assert newctl[:3]==(oldctl[0],oldctl[1]+1,oldctl[2]) and newctl[5:]==oldctl[5:]
completion=struct.unpack('<8Q',(out/'proposal_completion.raw').read_bytes())
assert completion[0]==0 and completion[3:5]==(0,0)
observed={}
for o in struct.iter_unpack('<8Q',(art/'observations.raw').read_bytes()):
    assert o[0] not in observed or observed[o[0]]==o[1]
    observed[o[0]]=o[1]
actual_reads=list(struct.iter_unpack('<2Q',(out/'canonical_reads.raw').read_bytes()))
assert actual_reads==sorted(observed.items()) and completion[2]==len(observed)
nodes=[r[0] for r in struct.iter_unpack('<I',(art/'path_nodes.raw').read_bytes())]
pips=[r[0] for r in struct.iter_unpack('<I',(art/'path_pips.raw').read_bytes())]
anchor,=struct.unpack('<Q',(art/'attachment.raw').read_bytes())
goal=struct.unpack('<8Q',(art/'goal.raw').read_bytes())
assert len(nodes)==len(pips) and len(set(nodes))==len(nodes)
def trees(state):
    result={}
    for i,net in enumerate(state['nets']):
        if net[0]!=oldctl[0]:continue
        tree={};index=net[3];visited=set()
        for _ in range(net[4]):
            assert index<state['control'][0][3] and index not in visited
            visited.add(index);r=state['trees'][index]
            assert r[0]==oldctl[0] and r[2]==i and r[1] not in tree
            tree[r[1]]=(r[3],r[4],r[5]);index=r[6]
        assert index==(1<<64)-1
        result[i]=tree
    return result
expected=trees(before);actual=trees(after)
assert anchor in expected[slot]
parent,depth=anchor,expected[slot][anchor][2]
for node,pip in zip(nodes,pips):
    assert node not in expected[slot]
    depth+=1;expected[slot][node]=(parent,pip,depth);parent=node
assert actual==expected and parent==goal[3] and depth==goal[4]
for i,(a,b) in enumerate(zip(before['nets'],after['nets'])):
    if i!=slot:assert a==b
    else:assert b[:3]==a[:3] and b[4]==a[4]+len(nodes) and b[5]==a[5]+1 and b[6:]==a[6:]
def resources(state):
    result={}
    for r in state['resources']:
        if r[0]!=oldctl[0]:continue
        node=r[4]&0xffffffff;assert node not in result
        index=r[5];members=set()
        for _ in range(r[1]):
            assert index<len(state['trees'])
            t=state['trees'][index];assert t[0]==oldctl[0] and t[1]==node and t[2] not in members
            members.add(t[2]);index=t[7]
        assert index==(1<<64)-1
        result[node]=(r[1],r[2],r[3],members)
    return result
expected=resources(before);actual=resources(after)
for node in nodes:
    occupancy,history,version,members=expected.get(node,(0,0,0,set()))
    assert slot not in members
    expected[node]=(occupancy+1,history,version+1,members|{slot})
assert actual==expected
report=dict(status='passed',published_nodes=len(nodes),all_net_trees_checked=len(trees(after)),
    scope='Independent complete tree/membership, resource occupancy/history/version and revision replay of native path commit; no concurrency or board claim',board_result=False)
(out/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

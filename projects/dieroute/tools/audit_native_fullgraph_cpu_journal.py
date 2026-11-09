"""Reconstruct every exported CPU observation from the immutable owner shards."""
from pathlib import Path
import collections,hashlib,json,mmap,struct
R=Path(__file__).resolve().parents[1];P=R/'work/native_fullgraph_cpu_full_search_20261015'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def main():
 p=json.loads((P/'protocol.json').read_text());parent=json.loads((P/'independent_audit.json').read_text());cmd=p['command'];snap=Path(cmd[1]);files=[snap/'resources.raw',snap/'control.raw',Path(cmd[3]),P/'artifacts/observations.raw',P/'artifacts/path_nodes.raw',P/'artifacts/attachment.raw']
 binding=R/'work/native_sharded_large_workspace_budget1_diagnostic_20261015/launch_protocol.json'
 frozen=json.loads(binding.read_text())['source_sha256'];expected=dict(frozen);expected.update(parent['source_sha256'])
 for f in files:assert sha(f)==expected[str(f.resolve())],f
 control=struct.unpack('<8Q',(snap/'control.raw').read_bytes());nodes=control[5]&0xffffffff;dies=control[5]>>32;shard=control[6]&0xffffffff;tree=control[7];session=control[0];assert dies==3 and shard&(shard-1)==0
 handles=[files[i].open('rb') for i in [0,2]];resources,policy=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];cache={};owners=collections.Counter();present=absent=0
 for o in struct.iter_unpack('<8Q',files[3].read_bytes()):
  node=o[0];assert node<nodes
  if node not in cache:
   pol=struct.unpack_from('<Q',policy,64+node*8)[0];mask=pol>>32&255;assert mask and not pol>>41 and not mask>>dies;owner=(mask&-mask).bit_length()-1;hashed=node*2654435761&(shard-1);expected=None
   for probe in range(shard):
    r=struct.unpack_from('<8Q',resources,(owner*shard+((hashed+probe)&(shard-1)))*64);assert r[0]<=session
    if r[0]!=session:expected=(node,0,0,0,session,1,owner,0);absent+=1;break
    assert not r[4]>>40 and r[4]&0xffffffff<nodes and r[2]!=2**64-1 and not r[6] and not r[7] and r[1]<=tree and (r[1]==0)==(r[5]==2**64-1)
    if r[4]&0xffffffff==node:
     assert r[4]==node|(mask<<32);expected=(node,r[3],r[1],r[2],session,1,owner,0);present+=1;break
   if expected is None:expected=(node,0,0,0,session,1,owner,0);absent+=1
   cache[node]=expected;owners[owner]+=1
  assert o==cache[node],node
 attachment=struct.unpack('<Q',files[5].read_bytes())[0];path=[attachment]+[n[0] for n in struct.iter_unpack('<I',files[4].read_bytes())];masks=[struct.unpack_from('<Q',policy,64+n*8)[0]>>32&255 for n in path];dp={d:0 for d in range(dies) if masks[0]>>d&1}
 for mask in masks[1:]:dp={d:min(c+(prev!=d) for prev,c in dp.items()) for d in range(dies) if mask>>d&1}
 result=dict(status='all862428_cpu_journal_records_match_immutable_owner_shards',records=files[3].stat().st_size//64,unique_observed_nodes=len(cache),present_unique_nodes=present,absent_unique_nodes=absent,owner_histogram=dict(owners),source_mask=masks[0],sink_mask=masks[-1],path_membership_histogram=dict(collections.Counter(masks)),minimum_membership_die_changes=min(dp.values()),source_sha256={str(f.resolve()):sha(f) for f in [*files,binding,P/'independent_audit.json',Path(__file__).resolve()]},scope='Every exported observation checked against exact hashed immutable owner shard and policy. Path begins mask4 and ends mask2 through shared mask6, requiring one abstract die change; not physical SLL usage. Does not prove all actual implementation reads are journaled, native API census, XRT or commit correctness.',board_result=False,research_complete=False)
 with (P/'journal_authority_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()

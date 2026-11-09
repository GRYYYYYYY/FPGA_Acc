"""Review frozen XRT/CPU commit argument contract and declared memory bounds."""
import hashlib,json,re,struct,xml.etree.ElementTree as E
from pathlib import Path
from zipfile import ZipFile
R=Path(__file__).resolve().parents[1];P=R/'work/native_XRT_commit_argument_contract_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(f):
  f=Path(f).resolve();key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with f.open('rb') as v:
    for b in iter(lambda:v.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 run=R/'work/native_identity_higher_g_xrt_pipeline_20261015';protocol=json.loads((run/'protocol.json').read_text());snap=Path(protocol['command'][1]);search=Path(protocol['command'][2]);art=run/'artifacts';host=run/'source/tb/host.cpp';source=host.read_text()
 def words(f):return struct.unpack('<8Q',Path(f).read_bytes())
 ctl=words(snap/'control.raw');nodes=ctl[5]&0xffffffff;dies=ctl[5]>>32;shard=ctl[6]&0xffffffff;netcap=ctl[6]>>32;tree=ctl[7];slot=int(protocol['command'][5])
 net=struct.unpack_from('<8Q',(snap/'nets.raw').read_bytes(),slot*64)
 def header(f,t):
  with Path(f).open('rb') as v:h=v.read(64)
  assert h[:8]==b'FPGAACCP' and struct.unpack_from('<I',h,12)[0]==t
  count,payload=struct.unpack_from('<2Q',h,16);assert count*8==payload==Path(f).stat().st_size-64;return count,payload
 offsetcount,offsetbytes=header(search/'offsets.bin',0x44520001);arcs,arcbytes=header(search/'arcs.bin',0x44520002);policycount,policybytes=header(Path(protocol['command'][3]),0x44520026)
 assert offsetcount==nodes+1 and policycount==nodes and (snap/'nets.raw').stat().st_size==netcap*64 and (snap/'trees.raw').stat().st_size==tree*64
 journal=(art/'observations.raw').read_bytes();assert len(journal)%64==0;consumed={}
 for off in range(0,len(journal),64):
  node,version=struct.unpack_from('<2Q',journal,off);assert node not in consumed or consumed[node]==version;consumed[node]=version
 canonical=b''.join(struct.pack('<2Q',n,v) for n,v in sorted(consumed.items()));gold=R/'work/native_identity_higher_g_commit_differential_20261015/artifacts/canonical_reads.raw';assert canonical==gold.read_bytes()
 hops=(art/'path_nodes.raw').stat().st_size//4;assert (art/'path_pips.raw').stat().st_size==hops*4 and hops==42 and len(consumed)==256
 scratch=max(256,hops*4+16);delta=max(64,hops)
 def call(text,token):
  start=text.index(token)+len(token);depth=1;end=start
  while depth:
   if text[end]=='(':depth+=1
   if text[end]==')':depth-=1
   end+=1
  body=text[start:end-1];out=[];depth=0;begin=0
  for i,c in enumerate(body):
   if c in '([{':depth+=1
   if c in ')]}':depth-=1
   if c==',' and depth==0:out.append(body[begin:i].strip());begin=i+1
  out.append(body[begin:].strip());return out
 actual=call(source,'auto transaction=commit(')
 pointer_names='command policy offsets arcs reads shadows branches paths resources0 resources1 resources2 trees nets control scratch deltas completion'.split()
 scalar_names='node_count arc_count dies shard_capacity net_capacity tree_capacity read_capacity shadow_capacity branch_capacity path_capacity scratch_capacity delta_capacity'.split()
 scalar_expr=['nodes','arcs.count','dies','shard','unsigned(nm.bytes/64)','tree','unsigned(consumed.size())','1u','1u','unsigned(published_path.size())','scratch_cap','delta_cap']
 assert actual==[f'c[{i}]' for i in range(17)]+scalar_expr
 cpu=R/'work/native_two_phase_XRT_path_CPU_commit_20261015/commit.cpp';cpuargs=call(cpu.read_text(),'dieroute_net_commit_hbm(')
 assert cpuargs[15:]==['policy.count','arcs.count','oldctl.w[5]>>32','std::uint32_t(oldctl.w[6])','nets.size()','trees.size()','reads.size()/2','1','1','paths.size()/2','scratch_cap','delta_cap']
 scalar_values=[nodes,arcs,dies,shard,netcap,tree,len(consumed),1,1,hops,scratch,delta]
 image=R/'work/native_higher_g_hw_emu_link_20261015';xo=image/'commit.xo'
 with ZipFile(xo) as z:k=E.fromstring(z.read('dieroute_net_commit_sharded_hbm/kernel.xml')).find('kernel')
 args=list(k.find('args'));assert [v.get('name') for v in args]==pointer_names+scalar_names and k.get('hwControlProtocol')=='ap_ctrl_chain'
 for i,v in enumerate(args):assert int(v.get('id'))==i and int(v.get('size'),0)==(8 if i<17 or i==18 else 4)
 for i,value in enumerate(scalar_values,17):assert 0<=value<2**(64 if i==18 else 32)
 alias=dict((int(a),int(b)) for a,b in re.findall(r'c\[(\d+)\]=b\[(\d+)\];',source));assert alias=={1:2,2:0,3:1,8:3,9:4,10:5,13:6}
 assert 'c[11]=trees;c[12]=nets;' in source
 ga=json.loads((image/'group_audit/audit.json').read_text());groups=ga['argument_group_ids']['dieroute_net_commit_sharded_hbm:net_commit'];top=json.loads((image/'group_audit/group_topology.json').read_text())['group_topology']['m_mem_data']
 cap=int(protocol['command'][7]);qcap=max(1024,cap*4);jcap=max(1024,cap*16)
 sizes=[offsetbytes,arcbytes,policybytes,shard*64,shard*64,shard*64,64,nodes*8,cap*64,qcap*64,jcap*64,64,128,64,64]
 extra=[128,len(canonical),64,64,hops*16,scratch*128,delta*64,64]
 pointer_sizes=[128,policybytes,offsetbytes,arcbytes,len(canonical),64,64,hops*16,shard*64,shard*64,shard*64,tree*64,netcap*64,64,scratch*128,delta*64,64]
 snapshot_names='offsets arcs policy resources0 resources1 resources2 authority_control potential labels queue journal metadata configuration result_words goal_words'.split();snapshot_groups=ga['argument_group_ids']['dieroute_native_snapshot_search_sharded_hbm:snapshot_search']
 log=(run/'run.log').read_text();bo={int(i):(int(g),int(n),int(a)) for i,g,n,a in re.findall(r'DIAG BO index=(\d+) group=(\d+) bytes=(\d+) address=(\d+)',log)};assert set(bo)==set(range(15));intervals=[]
 totals={}
 for i,name in enumerate(snapshot_names):
  group,bytecount,address=bo[i];assert group==snapshot_groups[name] and bytecount==sizes[i];mem=top[group];base=int(mem['m_base_address'],0);limit=int(mem['m_sizeKB'],0)*1024;assert base<=address and address+bytecount<=base+limit;intervals.append((group,address,address+bytecount));totals[group]=totals.get(group,0)+bytecount
 for i,(group,start,end) in enumerate(intervals):
  for other,a,b in intervals[:i]:assert group!=other or end<=a or b<=start
 # Other host BOs: trees,nets plus seed parent/observation/frontier; commit buffers use scratch group.
 totals[groups['trees']]=totals.get(groups['trees'],0)+tree*64+netcap*64;totals[groups['command']]=totals.get(groups['command'],0)+3*64+sum(extra)
 capacity=[]
 for group,used in sorted(totals.items()):
  maximum=int(top[group]['m_sizeKB'],0)*1024;assert used<=maximum;capacity.append(dict(group_id=group,tag=top[group]['m_tag'],declared_bytes=used,group_capacity_bytes=maximum,logical_unused_bytes=maximum-used))
 for f in [host,cpu,xo,image/'group_audit/audit.json',image/'group_audit/group_topology.json',run/'protocol.json',run/'run.log',snap/'control.raw',snap/'nets.raw',art/'observations.raw',art/'path_nodes.raw',art/'path_pips.raw',gold,Path(__file__).resolve()]:sha(f)
 for f in [search/'offsets.bin',search/'arcs.bin',Path(protocol['command'][3])]:assert sha(f)==protocol['source_sha256'][str(f)]
 result=dict(status='frozen_XRT29argument_order_scalar_capacity_and15recorded_BO_ranges_reviewed',scalar_arguments=[dict(id=i+17,name=n,value=v,host_expression=e) for i,(n,v,e) in enumerate(zip(scalar_names,scalar_values,scalar_expr))],pointer_arguments=[dict(id=i,name=n,declared_bytes=v,group_id=groups[n]) for i,(n,v) in enumerate(zip(pointer_names,pointer_sizes))],declared_group_capacity=capacity,recorded_nonoverlapping_snapshot_BOs=15,canonical_readset_byte_matches_CPU=True,source_sha256=refs,scope='Frozen host call expressions and compiled XO ABI align with CPU reference scalar values for this original task. Fifteen recorded initial BO intervals fit and do not overlap; aggregate logical bytes fit group capacities, excluding unknown allocator padding. Commit graph/authority aliases are intentional. No claim of actual commit enqueue, delivery/coherence, deadlock absence, full pipeline success, physical bank behavior or board timing.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ['status','declared_group_capacity']}))
if __name__=='__main__':main()

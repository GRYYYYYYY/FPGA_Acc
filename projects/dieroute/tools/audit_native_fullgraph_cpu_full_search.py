"""Validate the CPU reference's complete selected CSR path and authority charges."""
from pathlib import Path
import hashlib,json,mmap,struct
R=Path(__file__).resolve().parents[1];P=R/'work/native_fullgraph_cpu_full_search_20261015';cache={}
def sha(q):
 q=str(Path(q).resolve())
 if q not in cache:
  h=hashlib.sha256()
  with Path(q).open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[q]=h.hexdigest()
 return cache[q]
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='terminal_requires_review' and m['returncode']==0
 for field in ['source_sha256','input_source_sha256']:
  for f,h in p[field].items():assert sha(f)==h,f
 cmd=p['command'];original=json.loads((R/'work/native_snapshot_sharded_native_xrt_v2_20261014/cross_die/manifest.json').read_text())['command'];assert cmd[1:9]==original[1:9] and cmd[10:]==original[10:]
 a=P/'artifacts';result=struct.unpack('<8Q',(a/'result.raw').read_bytes());meta=struct.unpack('<8Q',(a/'metadata.raw').read_bytes());goal=struct.unpack('<8Q',(a/'goal.raw').read_bytes());assert result[0]==0 and result[1]<=2097152 and meta[:3]==result[4:7]
 path=[v[0] for v in struct.iter_unpack('<I',(a/'path_nodes.raw').read_bytes())];pips=[v[0] for v in struct.iter_unpack('<I',(a/'path_pips.raw').read_bytes())];attachment=struct.unpack('<Q',(a/'attachment.raw').read_bytes())[0];assert path and len(path)==len(pips)==len(set(path)) and attachment not in path and path[-1]==int(cmd[6])==goal[3]
 snap=Path(cmd[1]);control=struct.unpack('<8Q',(snap/'control.raw').read_bytes());net=struct.unpack_from('<8Q',(snap/'nets.raw').read_bytes(),int(cmd[5])*64);seeds={v[1]:v[5] for v in struct.iter_unpack('<8Q',(snap/'tree_seeds.raw').read_bytes())};assert attachment in seeds and goal[0]==1 and goal[4]==seeds[attachment]+len(path)
 selected=set(path);observations={};journal=a/'observations.raw';assert journal.stat().st_size==meta[1]*64
 for o in struct.iter_unpack('<8Q',journal.read_bytes()):
  if o[0] in selected:
   assert o[4]==control[0] and o[5]==1 and o[7]==0
   if o[0] in observations:assert observations[o[0]]==o
   observations[o[0]]=o
 assert observations.keys()==selected
 handles=[];maps=[]
 for f in [Path(cmd[2])/'offsets.bin',Path(cmd[2])/'arcs.bin',Path(cmd[3])]:
  h=f.open('rb');handles.append(h);maps.append(mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ))
 offsets,arcs,policy=maps;previous=attachment;cost=0;owner_transitions=0;previous_mask=struct.unpack_from('<Q',policy,64+attachment*8)[0]>>32&255
 for node,pip in zip(path,pips):
  begin,end=struct.unpack_from('<QQ',offsets,64+previous*8);assert any(struct.unpack_from('<II',arcs,64+i*8)==(node,pip) for i in range(begin,end))
  pol=struct.unpack_from('<Q',policy,64+node*8)[0];mask=pol>>32&255;assert mask and not pol>>41 and not pol&(1<<40) and pol&0xffffffff in [0xffffffff,net[1]]
  o=observations[node];assert o[6]==(mask&-mask).bit_length()-1;cost+=1+o[3]+control[2]*o[2];owner_transitions+=not bool(previous_mask&mask);previous_mask=mask;previous=node
 assert cost==goal[1] and goal[5]==(path[-2] if len(path)>1 else attachment) and goal[6]==pips[-1]
 for f in [P/'protocol.json',P/'manifest.json',P/'stdout.log',P/'stderr.log',*a.glob('*.raw'),Path(__file__).resolve()]:sha(f)
 report=dict(status='original_bound_fullgraph_cpu_search_found_path_CSR_policy_and_cost_verified',result_words=result,goal_words=goal,path_edges=len(path),attachment=attachment,selected_path_cost=cost,selected_path_observed_nodes=len(observations),disjoint_membership_transitions=owner_transitions,source_sha256=cache,scope='Original full CSR/source/sink/quotient/2M expansion and label bounds, same-source CPU search. Independent selected-path CSR/PIP, protection, attachment/depth and journal-derived cost checked. Does not prove all journal reads against authority here, full search optimality, XRT execution, commit closure or board performance.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()

"""Independent full-XML final paths plus chronological branch-resource audit."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
from array import array
from collections import Counter,defaultdict
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_prior_budget_branch_wire_pilot_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text())
 for p,h in result['bindings'].items():assert sha(pathlib.Path(p))==h
 # Parser graph identity comes from authenticated actual context receipt.
 protocol['bindings']=result['bindings']
 graph=next(pathlib.Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');spans=array('I');kinds=[];us=array('I');vs=array('I');weights=array('Q');switches={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));loc=e.find('loc');kind=e.get('type');spans.append(int(loc.get('xhigh'))-int(loc.get('xlow'))+1 if kind=='CHANX' else (int(loc.get('yhigh'))-int(loc.get('ylow'))+1 if kind=='CHANY' else 0));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert e.get('type') in ['buffer','mux','tristate'] and Fraction(t.get('Cinternal','0'))==0;w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;switches[int(e.get('id'))]=int(w)
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));weights.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(us)==8097539 and len(caps)==904438;source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';frame=json.loads(source.read_text());records={q['connection_id']:q for q in frame['records']};events=[json.loads(line) for line in (O/'events.jsonl').read_text().splitlines()];assert [e['connection_id'] for e in events]==protocol['connection_ids'];assert len(events)==80;nets=set(protocol['NETs']);updated={n:json.loads((O/f'net_{n}_tree.json').read_text()) for n in nets};parents=defaultdict(dict);unions=defaultdict(set);selected_paths={};old_selected_paths={};newdelays={};before_RC=0;after_RC=0
 def audit(q,ids):
  u=q['source'];seen={u};value=0;arcs=[];assert kinds[u]=='SOURCE' and caps[u]>0
  for eid in ids:
   assert type(eid) is int and 0<=eid<len(us);a,b,w=us[eid],vs[eid],weights[eid];assert a==u and b not in seen and caps[b]>0 and kinds[a]!='SINK' and kinds[b]!='SOURCE';arcs.append((b,a,eid));seen.add(b);u=b;value+=w
  assert u==q['sink'] and kinds[u]=='SINK';return seen,value,arcs
 for cid,q in records.items():
  n=q['net_id'];old=q['answer']['physical_edge_ids'];ids=updated[n]['paths'][str(q['sink'])] if n in nets else old;nodes,value,arcs=audit(q,ids);assert value<=q['answer']['delay'];unions[n].update(nodes)
  for v,u,eid in arcs:
   if v in parents[n]:assert parents[n][v]==(u,eid)
   parents[n][v]=(u,eid)
  if n in nets:
   assert updated[n]['source']==q['source'] and updated[n]['sink_costs'][str(q['sink'])]==value;selected_paths[cid]=(nodes,ids);old_nodes,oldvalue,_=audit(q,old);assert oldvalue==q['answer']['delay'];old_selected_paths[cid]=old_nodes;before_RC+=oldvalue;after_RC+=value;newdelays[cid]=value
 final=Counter(v for ns in unions.values() for v in ns);assert {str(v):n for v,n in final.items()}==json.loads((O/'final_unique_NET_occupancy.json').read_text());assert all(n<=caps[v] for v,n in final.items()) and len(unions)==55300
 oldrefs=defaultdict(Counter)
 for cid,nodes in old_selected_paths.items():oldrefs[records[cid]['net_id']].update(nodes)
 chronological=Counter({int(v):n for v,n in frame['ledger'].items()});current=dict(old_selected_paths);changed={};prior_span=sum(sum(spans[v] for v in ref) for ref in oldrefs.values());accepts=0
 for e in events:
  cid=e['connection_id'];q=records[cid];net=q['net_id'];refs=oldrefs[net];oldnodes=current[cid];before=sum(spans[v] for v in refs);released=sum(spans[v] for v in oldnodes if refs[v]==1);assert e['prior_RC_budget']==q['answer']['delay'] and e['wire_before']==before and e['released_unique_span']==released
  assert e['committed']==(e['status']=='FOUND')
  if e['committed']:
   assert e['physical_edge_ids'] is not None;newnodes,value,_=audit(q,e['physical_edge_ids']);assert value<=q['answer']['delay'];kept={v for v,c in refs.items() if c>int(v in oldnodes)};assert sum(spans[v] for v in newnodes-kept)==e['cost']<released
   for v in oldnodes:
    refs[v]-=1
    if refs[v]==0:del refs[v];chronological[v]-=1
   for v in newnodes:
    if refs[v]==0:chronological[v]+=1
    refs[v]+=1;assert chronological[v]<=caps[v]
   current[cid]=newnodes;changed[cid]=e['physical_edge_ids'];accepts+=1
  else:assert e['physical_edge_ids'] is None
  assert e['wire_after']==sum(spans[v] for v in refs) and e['wire_after']<=before
 for cid,q in records.items():
  if q['net_id'] in nets:assert updated[q['net_id']]['paths'][str(q['sink'])]==changed.get(cid,q['answer']['physical_edge_ids'])
 assert Counter({v:n for v,n in chronological.items() if n})==final;after_span=sum(sum(spans[v] for v in ref) for ref in oldrefs.values());assert result['accepted']==accepts and result['prior_selected_NET_CHAN_span']==prior_span and result['new_selected_NET_CHAN_span']==after_span and result['prior_sum_sink_RC']==before_RC and result['new_sum_sink_RC']==after_RC
 allnodes=set.union(*(unions[n] for n in nets),*old_selected_paths.values());spanfile=O/'candidate_CHAN_spans.json';spanfile.write_text(json.dumps({v:spans[v] for v in allnodes if spans[v]})+'\n');bindings={str(p):sha(p) for p in [source,O/'protocol.json',O/'results.json',O/'events.jsonl',O/'final_unique_NET_occupancy.json',spanfile,graph,pathlib.Path(__file__).resolve()]+[O/f'net_{n}_tree.json' for n in nets]}
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='FULL115572_CONNECTION_XML_RC_CAPACITY_AND_ALL80_RESOURCE_TRANSACTIONS_PASS',connections=len(records),NETs=len(unions),tested_branches=80,committed=accepts,selected_NET_connections=len(selected_paths),prior_selected_NET_CHAN_span=prior_span,new_selected_NET_CHAN_span=after_span,prior_sum_sink_RC=before_RC,new_sum_sink_RC=after_RC,bindings=bindings,scope='One fixed80-branch pilot in old-source55300-NET state. Physical/additive RC and owner-union resource checks only; not new target layout, native FULL/STA, unseen-family, original prediction quality or end-to-end speedup.'),f,indent=2)
 print('INDEPENDENT PASS',accepts,'span',prior_span,after_span,flush=True)
if __name__=='__main__':main()

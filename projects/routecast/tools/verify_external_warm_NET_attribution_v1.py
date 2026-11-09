"""Alternate streaming XML edge lookup and perNET attribution replay, original3cases."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_corrected_warm_NET_attribution_v1_2026-10-19';I=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19';G=E/'prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 diagnosis=read(D/'diagnosis.json');assert all(sha(k)==h for k,h in diagnosis['bindings'].items());frames={};sourcepath=I/'source_checkpoint/initial.json';frames['source']=read(sourcepath);needed=set();bindings={str(D/'diagnosis.json'):sha(D/'diagnosis.json'),str(G):sha(G),str(Path(__file__).resolve()):sha(__file__)}
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';p=I/'warm'/case/'native_retained/initial.json';frames[case]=read(p)
 for f in frames.values():
  for r in f['records']:needed.update(r['answer']['physical_edge_ids'])
 edges={};types={};eid=0;stack=[]
 for event,el in ET.iterparse(G,events=('start','end')):
  if event=='start':stack.append(el);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if el.tag=='node' and parent=='rr_nodes':types[int(el.get('id'))]=el.get('type');stack[-2].remove(el);el.clear()
  elif el.tag=='edge' and parent=='rr_edges':
   if eid in needed:edges[eid]=(int(el.get('src_node')),int(el.get('sink_node')))
   eid+=1;stack[-2].remove(el);el.clear()
  stack.pop()
 assert edges.keys()==needed
 def owners(frame):
  nets=defaultdict(dict);support=defaultdict(set)
  for r in frame['records']:
   n=r['net_id'];cid=r['connection_id'];assert cid not in nets[n];nets[n][cid]=r;u=r['source'];support[n].add(u)
   for e in r['answer']['physical_edge_ids']:a,b=edges[e];assert a==u;support[n].add(b);u=b
   assert u==r['sink']
  assert dict(Counter(n for ns in support.values() for n in ns))=={int(n):v for n,v in frame['ledger'].items()};return nets,support
 src,old=owners(frames['source']);rows=[]
 for summary in diagnosis['rows']:
  case=summary['case'];warm,new=owners(frames[case]);out=D/case/'dirty_NETs.json';stored={r['net_id']:r for r in read(out)};assert src.keys()==warm.keys();delta=Counter();changed=0
  for n in src:
   a,b=src[n],warm[n];assert a.keys()==b.keys();root=any(a[c]['source']!=b[c]['source'] for c in a);sink=any(a[c]['sink']!=b[c]['sink'] for c in a);dirty=root or sink;plus=new[n]-old[n];minus=old[n]-new[n];delta.update(plus);delta.subtract(minus);count=sum(a[c]['answer']['physical_edge_ids']!=b[c]['answer']['physical_edge_ids'] for c in a);changed+=count
   if dirty:
    r=stored[n];assert r['category']==('source_moved' if root else 'sink_only')+'/retained_expand';assert r['added_nodes']==sorted(plus) and r['removed_nodes']==sorted(minus) and r['changed_paths']==count and r['fallback_reason'] is None
   else:assert n not in stored and a==b and not plus and not minus
  allnodes=set(frames['source']['ledger'])|set(frames[case]['ledger']);assert all(delta[int(n)]==frames[case]['ledger'].get(n,0)-frames['source']['ledger'].get(n,0) for n in allnodes);assert changed==sum(c['changed_paths'] for c in summary['categories'].values());bindings[str(out)]=sha(out);rows.append(dict(case=case,dirty_NETs=len(stored),changed_paths=changed,all_uniqueNET_resource_sets_and_signed_ledger_changes_equal=True))
 assert all(sha(k)==h for k,h in bindings.items());(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_ALTERNATE_XML_EDGE_STREAM_OWNERSHIP_AND_ATTRIBUTION_REPLAY_PASS',used_original_XML_edges=len(edges),rows=rows,bindings=bindings,scope='Alternate original XML parser and all NET perpath node union reconstruction; independently checks exact add/remove ownership sets and complete ledger delta. Inclusive-bin aggregation and exact topK ties remain separate audits. No causal attribution or scoring acceptance.'),indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()

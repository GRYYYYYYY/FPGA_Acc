"""Independent original XML/Fraction proof of staged native-state placement update."""
import json,hashlib,xml.etree.ElementTree as ET,copy,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_native_state_staged_update_v1_2026-10-18'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(frame,old,newmeta,oldmeta,nodes,edges,weights,initial,certs):
 a={q['connection_id']:q for q in oldmeta['connections']};b={q['connection_id']:q for q in newmeta['connections']};assert a.keys()==b.keys()
 changed={cid for cid in a if a[cid]!=b[cid]};nets={q['net_id'] for cid in changed for q in [a[cid],b[cid]]};sources={q['source'] for cid in changed for q in [a[cid],b[cid]]}
 while True:
  nn=set(nets);ss=set(sources)
  for q in list(a.values())+list(b.values()):
   if q['net_id'] in nets or q['source'] in sources:nets.add(q['net_id']);sources.add(q['source'])
  if nn==nets and ss==sources:break
 dirty={cid for cid,q in b.items() if q['net_id'] in nets};prior={r['connection_id']:r for r in old['records']};records={r['connection_id']:r for r in frame['records']};assert len(records)==len(frame['records'])==len(b)==2450 and records.keys()==b.keys();assert frame['required_connections']==frame['completed_connections']==2450;assert frame['scale']==old['scale'];scale=frame['scale'];assert scale%10**9==0
 unions=defaultdict(set);parents=defaultdict(dict);pathvalues={}
 for cid,rec in records.items():
  q=b[cid];assert all(rec[k]==v for k,v in q.items());assert q['net_id']==a[cid]['net_id']
  if cid not in dirty:assert rec==prior[cid]
  node=q['source'];assert nodes[node][0]=='SOURCE';value=initial[node];seen={node};used={node}
  for eid in rec['answer']['physical_edge_ids']:
   assert type(eid) is int and 0<=eid<len(edges);u,v,s=edges[eid];assert u==node and v not in seen and nodes[v][1]>0;seen.add(v);used.add(v);value+=weights[eid];node=v
   if nodes[v][0]!='SINK':
    assert nodes[v][0]!='SOURCE';parent=(u,s);assert v not in parents[q['net_id']] or parents[q['net_id']][v]==parent;parents[q['net_id']][v]=parent
  assert node==q['sink'] and nodes[node][0]=='SINK';assert value==F(rec['answer']['delay'],scale);assert value<=F(rec['budget_integer'],scale);pathvalues[cid]=value;unions[q['net_id']].update(used)
  if cid in dirty:
   assert rec['answer']['delay']==rec['floor_integer'];assert rec['budget_integer']==rec['proxy_budget_integer']==max(scale//10**9,(3*rec['floor_integer']+1)//2)
 occupancy=Counter(n for used in unions.values() for n in used);overflow=sum(max(0,v-nodes[n][1]) for n,v in occupancy.items());assert {str(n):v for n,v in occupancy.items()}==frame['ledger'];assert overflow==frame['overflow_units'];assert frame['history']=={};assert {str(n):int(n in nets) for n in unions}==frame['epochs']
 bysource=defaultdict(list)
 for cid in dirty:bysource[b[cid]['source']].append(cid)
 assert set(certs)==set(bysource);checks=0
 # Every edge from a default-clip source satisfies the inequality automatically: w>=0.
 adj=defaultdict(list)
 for eid,(u,v,s) in enumerate(edges):
  if nodes[u][1]>0 and nodes[v][1]>0:adj[u].append((v,weights[eid]))
 for source,c in certs.items():
  clip=F(c['clip'],scale);pot={int(n):F(v,scale) for n,v in c['potentials'].items()};assert all(n in nodes and nodes[n][1]>0 and 0<=value<clip for n,value in pot.items());assert pot.get(source,clip)<=initial[source]
  for u,value in pot.items():
   for v,w in adj[u]:assert pot.get(v,clip)<=value+w;checks+=1
  assert {int(t) for t in c['witnesses']}=={b[cid]['sink'] for cid in bysource[source]}
  for cid in bysource[source]:
   rec=records[cid];assert c['witnesses'][str(rec['sink'])]==rec['answer']['physical_edge_ids'];assert pathvalues[cid]==pot.get(rec['sink'],clip)
 return dict(connections=len(records),dirty_connections=len(dirty),preserved_connections=len(records)-len(dirty),dirty_nets=len(nets),floor_certificates=len(certs),overflow_units=overflow,nontrivial_edge_inequalities=checks)
def main():
 start=time.perf_counter();rp=D/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items());base=R/'experiments/xtea_native_state_bootstrap_v1_2026-10-18';old=json.loads((base/'initial.json').read_text());priorproof=json.loads((base/'independent_xml_verification_v1.json').read_text());assert all(sha(p)==h for p,h in priorproof['bindings'].items());newpath=R/'experiments/xtea_native_state_new_swap_v1_2026-10-18/demand/endpoints.json';oldpath=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';meta=json.loads(newpath.read_text());oldmeta=json.loads(oldpath.read_text());assert meta['graph_sha256']==oldmeta['graph_sha256'];graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];xml=ET.parse(graph).getroot();nodes={};initial={};rc={}
 for n in xml.find('rr_nodes'):
  nid=int(n.get('id'));assert nid not in nodes;t=n.find('timing');r=F(t.get('R'));c=F(t.get('C'));assert r>=0 and c>=0;nodes[nid]=(n.get('type'),int(n.get('capacity')));initial[nid]=r*c/2;rc[nid]=(r,c)
 switches={}
 for s in xml.find('switches'):
  sid=int(s.get('id'));assert sid not in switches and s.get('type') in {'buffer','mux','tristate'};t=s.find('timing');assert F(t.get('Cinternal','0'))==0;switches[sid]=(F(t.get('R','0')),F(t.get('Tdel','0')))
 edges=[];weights=[];cache={}
 for e in xml.find('rr_edges'):
  u,v,s=(int(e.get(k)) for k in ['src_node','sink_node','switch_id']);edges.append((u,v,s));key=(rc[v],switches[s])
  if key not in cache:
   (r,c),(sr,td)=key;cache[key]=(sr+r/2)*c+td;assert cache[key]>=0
  weights.append(cache[key])
 certs={}
 for spec in receipt['certificates']:
  assert sha(spec['path'])==spec['sha256'];c=json.loads(Path(spec['path']).read_text());assert c['source'] not in certs;certs[c['source']]=c
 frame=json.loads((D/'initial.json').read_text());result=verify(frame,old,meta,oldmeta,nodes,edges,weights,initial,certs);negative=[]
 for mode in ['missing_connection','changed_retained_budget','wrong_ledger','wrong_epoch']:
  bad=copy.deepcopy(frame)
  if mode=='missing_connection':bad['records'].pop()
  elif mode=='changed_retained_budget':
   prior={x['connection_id']:x for x in old['records']};rec=next(x for x in bad['records'] if x==prior[x['connection_id']]);rec['budget_integer']+=1
  elif mode=='wrong_ledger':key=next(iter(bad['ledger']));bad['ledger'][key]+=1
  else:key=next(iter(bad['epochs']));bad['epochs'][key]+=1
  try:verify(bad,old,meta,oldmeta,nodes,edges,weights,initial,certs)
  except AssertionError:negative.append(mode)
  else:raise AssertionError('Invalid staged state accepted '+mode)
 bindings={**receipt['bindings'],str(rp):sha(rp),str(Path(__file__)):sha(__file__),str(base/'independent_xml_verification_v1.json'):sha(base/'independent_xml_verification_v1.json')};bindings.update({s['path']:s['sha256'] for s in receipt['certificates']});assert all(sha(p)==h for p,h in bindings.items())
 with (D/'independent_xml_verification_v1.json').open('x') as f:json.dump(dict(bindings=bindings,result=result,negative_cases=negative,all_paths_original_XML_fraction_and_singleparent_pass=True,all_unaffected_native_records_exact=True,all_dirty_floors_certified=True,all_uniqueNET_occupancy_budget_epoch_checks_pass=True,verification_seconds=time.perf_counter()-start,scope='Staged estimator state correctness only. Predicted overflow237 is permitted as a forecast and is not legal native routing. Canonical packed-pin/native FULL/STA and feedback/native utility remain pending.'),f,indent=2);f.write('\n')
 print('PASS independent staged state',result,flush=True)
if __name__=='__main__':main()

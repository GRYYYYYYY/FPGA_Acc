"""Full-physical-tree and channel-union change census; original labels untouched."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from collections import Counter
from audit_native_route import NET,NODE
from native_route_ledger_import_compact import physical_paths
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def geom(p):
 rows=[]
 for line in p.read_text().splitlines():
  t=line.split()
  if len(t)>=5 and not t[0].startswith('#'):
   try:coords=tuple(map(int,t[1:5]))
   except ValueError:continue
   rows.append((t[0],coords))
 assert rows and len(rows)==len({r[0] for r in rows});return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()
def stream(p,names,channels):
 out={};name=None;nodes=set();edges=set();previous=None;switch=None
 def finish():
  if name in names:
   assert name not in out;out[name]=(nodes & channels,frozenset(edges))
  else:assert not nodes & channels
 with p.open() as f:
  for line in f:
   m=NET.match(line)
   if m:finish();name=m[2];nodes=set();edges=set();previous=None;switch=None
   m=NODE.match(line)
   if not m:continue
   node=int(m[1]);kind=m[2]
   if kind=='SOURCE':assert not nodes
   elif node not in nodes:
    assert previous in nodes;edges.add((previous,node,switch))
   nodes.add(node);previous=node;switch=int(m[3])
 finish();assert set(out)==names
 # Independent branch expansion must reconstruct the same complete physical arcs.
 expanded=physical_paths(p);effective={n:paths for n,paths in expanded.items() if paths};assert set(effective)==names
 for n,paths in effective.items():
  es={(path[i-1][0],path[i][0],path[i][1]) for path in paths for i in range(1,len(path))};cs={u for path in paths for u,s in path if u in channels};assert out[n]==(cs,frozenset(es))
 return out

def main():
 O=R/'experiments/mmc_unchanged_NET_route_churn_v1_2026-10-19';O.mkdir(exist_ok=False);M=R/'experiments/mmc_reference_budget_incremental_astar_v2_2026-10-19';protocol=json.loads((M/'protocol.json').read_text());ip=M/'independent_verification_v1.json';proof=json.loads(ip.read_text());assert all(c['full_state_complete'] for c in proof['cases']);G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';gp=json.loads(G.read_text());source=pathlib.Path(gp['previous_native_route']);old_ep=pathlib.Path(gp['previous_endpoint']);oldmeta=json.loads(old_ep.read_text());oldqs={q['connection_id']:q for q in oldmeta['connections']};names={oldmeta['net_names'][str(q['net_id'])] for q in oldqs.values()};assert len(names)==55300;graph=pathlib.Path(json.loads((M/'common_context.json').read_text())['graph']);bindings={str(p):sha(p) for p in [ip,M/'protocol.json',G,source,old_ep,graph,pathlib.Path(__file__).resolve(),R/'tools/native_route_ledger_import_compact.py']}
 assert gp['bindings'][str(source)]==sha(source);channels=set();stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:channels.add(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720;original=stream(source,names,channels);old_occ=Counter(n for cs,es in original.values() for n in cs);sourceframe=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';frame=json.loads(sourceframe.read_text());assert old_occ==Counter({int(n):v for n,v in frame['ledger'].items() if int(n) in channels});bindings[str(sourceframe)]=sha(sourceframe);rows=[]
 for plan in protocol['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);assert proof['bindings'][str(ep)]==sha(ep);meta=json.loads(ep.read_text());queries={q['connection_id']:q for q in meta['connections']};changed={cid for cid,q in queries.items() if (q['source'],q['sink'])!=(oldqs[cid]['source'],oldqs[cid]['sink'])};assert changed==set(plan['changed_CIDs']);dirty={meta['net_names'][str(queries[cid]['net_id'])] for cid in changed};ids={meta['net_names'][str(q['net_id'])]:q['net_id'] for q in queries.values()};assert set(ids)==names;B=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case;vp=B/'verification.json';v=json.loads(vp.read_text());route=B/'cold/output.route';audit=B/'cold/physical_audit.json';assert v['all_native_physical_and_canonical_pass'];assert v['bindings'][str(route)]==sha(route) and v['bindings'][str(audit)]==sha(audit);current=stream(route,names,channels);occ=Counter(n for cs,es in current.values() for n in cs);actual=json.loads(audit.read_text());assert occ==Counter({int(n):x for n,x in actual['node_occupancy'].items() if int(n) in channels});dirty_delta=Counter();stable_delta=Counter();stats={};netrows=[]
  for name in sorted(names):
   a,ae=original[name];b,be=current[name];dirty_flag=name in dirty;delta=dirty_delta if dirty_flag else stable_delta
   for n in b-a:delta[n]+=1
   for n in a-b:delta[n]-=1
   netrows.append(dict(net_id=ids[name],endpoint_changed=dirty_flag,physical_edge_set_changed=ae!=be,channel_union_changed=a!=b,added_CHANNEL_nodes=len(b-a),removed_CHANNEL_nodes=len(a-b)))
  domain=channels;assert all(occ[n]-old_occ[n]==dirty_delta[n]+stable_delta[n] for n in domain);oldmask=set().union(*(original[n][0] for n in dirty));outside=[n for n in domain if occ[n]!=old_occ[n] and n not in oldmask]
  for label,flag in [('changed_endpoint_NETs',True),('unchanged_endpoint_NETs',False)]:
   subset=[r for r in netrows if r['endpoint_changed']==flag];stats[label]=dict(NETs=len(subset),physical_edge_set_changed=sum(r['physical_edge_set_changed'] for r in subset),channel_union_changed=sum(r['channel_union_changed'] for r in subset),physical_change_with_same_channel_union=sum(r['physical_edge_set_changed'] and not r['channel_union_changed'] for r in subset),added_CHANNEL_ownerships=sum(r['added_CHANNEL_nodes'] for r in subset),removed_CHANNEL_ownerships=sum(r['removed_CHANNEL_nodes'] for r in subset))
  nf=O/(case+'_NETs.jsonl');nf.open('x').write(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in netrows));row=dict(case=case,changed_CIDs=len(changed),partitions=stats,changed_endpoint_signed_delta_L1=sum(abs(x) for x in dirty_delta.values()),unchanged_endpoint_signed_delta_L1=sum(abs(x) for x in stable_delta.values()),total_signed_delta_L1=sum(abs(occ[n]-old_occ[n]) for n in domain),changed_resources_outside_prior_dirty_NET_CHANNEL_mask=len(outside),outside_changed_resources_with_unchanged_NET_delta=sum(stable_delta[n]!=0 for n in outside),outside_changed_resources_with_changed_NET_delta=sum(dirty_delta[n]!=0 for n in outside),all_NET_physical_edge_and_CHANNEL_unions_independently_expanded=True,all_original_and_target_CHANNEL_owner_ledgers_exact=True);rows.append(row)
  for p in [ep,vp,route,audit,nf]:bindings[str(p)]=sha(p)
  print('CHURN_AUDIT',json.dumps(row),flush=True)
 # Historical baseline repeats remain evidence only for exactly matching layouts.
 B=R/'experiments/mmc_same_binary_cold_repeat_v1_2026-10-18';rp=B/'independent_verification_v2.json';pp=B/'protocol.json';repeat=json.loads(rp.read_text());assert repeat['all4_same_route_and_work']
 for p,h in repeat['bindings'].items():assert sha(p)==h
 repeats=json.loads(pp.read_text());matches=[]
 for plan in protocol['cases']:
  ep=json.loads(pathlib.Path(plan['endpoint']).read_text());place=pathlib.Path(ep['inputs']['place']['path']);layout=geom(place);matched=[]
  for archived in repeats['cases']:
   oldplace=pathlib.Path(archived['reference_directory'])/'design.place'
   if geom(oldplace)==layout:matched.append(archived['layout'])
  matches.append(dict(case=plan['case'],matching_archived_repeat_layouts=matched,same_geometry_repeat_available=bool(matched)));bindings[str(place)]=sha(place)
 for p in [rp,pp]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());result=dict(status='ALL3_FULL_PHYSICAL_EDGE_AND_CHANNEL_UNION_CHURN_WITH_EXACT_SIGNED_OWNERSHIP_DECOMPOSITION',cases=rows,repeat_layout_identity=matches,bindings=bindings,scope='Exposed development-data diagnostic, not new predictions. Exact dirty/unchanged partition from frozen endpoint changes. Signed delta classes can cancel, so class L1 values do not add to total. Cold global rerouting changes do not prove incremental routing must change these NETs. Archived one-repeat same-layout agreement is not universal determinism; unmatched layouts receive no repeatability claim. Original labels, quality gates, budgets and native acceptance remain unchanged.')
 (O/'review.json').open('x').write(json.dumps(result,indent=2)+'\n');print('REPEAT_LAYOUT_IDENTITY',matches,flush=True)
if __name__=='__main__':main()

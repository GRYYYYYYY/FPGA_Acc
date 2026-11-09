"""Fixed-route support limits for local point-sketch feedback; not a rank bound."""
import array,collections,json,sys,xml.etree.ElementTree as ET
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';out=E/'mmc_local_feedback_support_v1_2026-10-18';out.mkdir(exist_ok=False);sourcep=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';source=json.loads(sourcep.read_text());old={q['connection_id']:q for q in source['records']};assert len(old)==115572;idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());gp=E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json';gvp=gp.parent/'independent_verification_v1.json';gpdata=json.loads(gp.read_text());assert sha(gp)==json.loads(gvp.read_text())['bindings'][str(gp)] and sha(idxp)==gpdata['bindings'][str(idxp)];bindings={str(p):sha(p) for p in [sourcep,idxp,gp,gvp,Path(__file__),R/'tools/run_native_endpoint_v2_feedback_v1_2026_10_18.py']};arrays={}
 for name in ['edge_source','edge_destination','positive_capacity']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256'];bindings[d['path']]=d['sha256'];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());arrays[name]=a
 caps=arrays['positive_capacity'];assert len(caps)==904438 and all(c>0 for c in caps)
 def nodes(q):
  u=q['source'];seen={u}
  for edge in q['answer']['physical_edge_ids']:assert arrays['edge_source'][edge]==u;u=arrays['edge_destination'][edge];assert u not in seen;seen.add(u)
  assert u==q['sink'];return seen
 oldowners=collections.defaultdict(set);members=collections.defaultdict(list)
 for c,q in old.items():oldowners[q['net_id']].update(nodes(q));members[q['net_id']].append(c)
 assert len(oldowners)==55300;oldledger=collections.Counter(n for ns in oldowners.values() for n in ns);assert dict(oldledger)=={int(n):v for n,v in source['ledger'].items()};prepared=[];channels=None;bins=None
 plan=dict(selection='All3existing native_retained_on local-feedback point sketches. Inspect initial,round0,round1,final. Masks: endpoint-dirty NETs and endpoint-dirty plus initial-overuse resource owners; latter derived without labels and is diagnostic only.',bound='If every unselected NET path stays fixed, predicted occupancy>=fixed_NET_occupancy A. For truth Y and capacity C, unavoidable absolute normalized error>=max(A-Y,0)/C. Mean this over complete channel/bin domain. Mutable NETs optimistically arbitrary/nonnegative; do not require their paths jointly feasible.',limits='Applies to literal unique-NET point occupancy with frozen paths. Does not constrain priors that redistribute all NET uncertainty, does not prove any Spearman/TopK gate impossible, and does not establish a new schedule gain. Labels are already-exposed diagnostic targets, not selector inputs.')
 (out/'protocol.json').write_text(json.dumps(plan,indent=2))
 for case in ['case_01','case_02','case_03']:
  model=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}';quality=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}';qp=quality/'verification.json';qv=json.loads(qp.read_text());vp=quality/'vectors.json';assert sha(vp)==qv['bindings'][str(vp)];vectors=json.loads(vp.read_text());ch=vectors['channels'];bs=vectors['bins'];assert len(ch)==258720 and len(bs)==17160
  if channels is None:channels=[x['node'] for x in ch];bins=[tuple(x['key']) for x in bs]
  assert channels==[x['node'] for x in ch] and bins==[tuple(x['key']) for x in bs];initialp=model/'native_retained/initial.json';ap=model/'initial_independent_verification_v1.json';initialaudit=json.loads(ap.read_text());assert sha(initialp)==initialaudit['bindings'][str(initialp)] and sha(sourcep)==initialaudit['bindings'][str(sourcep)];initial=json.loads(initialp.read_text());ip={q['connection_id']:q for q in initial['records']};dirty={q['net_id'] for c,q in ip.items() if (q['source'],q['sink'])!=(old[c]['source'],old[c]['sink'])};frozen=set(oldowners)-dirty;frozen_cids={c for net in frozen for c in members[net]};rp=model/'feedback_on/native_retained/receipt.json';fa=model/'feedback_audits/verification.json';fav=json.loads(fa.read_text());assert fav['status']=='pass' and fav['both_final_and_all_event_audits_pass'] and sha(rp)==fav['bindings'][str(rp)];receipt=json.loads(rp.read_text());states=[initial]
  for round_index in range(2):
   info=receipt['rounds'][round_index];assert set(info['affected_nets'])==dirty and {e['net_id'] for e in info['events']}==dirty;p=model/f'feedback_on/native_retained/round{round_index}.json';assert sha(p)==receipt['files'][str(p)];states.append(json.loads(p.read_text()));bindings[str(p)]=sha(p)
  finalp=model/'feedback_on/native_retained/sketch.json';assert sha(finalp)==receipt['files'][str(finalp)]==qv['bindings'][str(finalp)];final=json.loads(finalp.read_text());states.append(final)
  for state in states:
   current={q['connection_id']:q for q in state['records']};assert set(current)==set(old)
   for c in frozen_cids:assert all(current[c][k]==old[c][k] for k in ['net_id','source','sink','answer'])
   for net in frozen:assert state['epochs'][str(net)]==initial['epochs'][str(net)]
  initialowners=dict(oldowners)
  for net in dirty:initialowners[net]=set()
  for c,q in ip.items():
   if q['net_id'] in dirty:initialowners[q['net_id']].update(nodes(q))
  ile={int(n):v for n,v in initial['ledger'].items()};assert collections.Counter(n for ns in initialowners.values() for n in ns)==ile;overused={n for n,v in ile.items() if v>caps[n]};expanded=dirty|{net for net,ns in initialowners.items() if ns&overused};masks={'endpoint_dirty':dirty,'dirty_plus_initial_overuse_owners':expanded};fixed={}
  for name,mutable in masks.items():
   f=oldledger.copy()
   for net in mutable:f.subtract(oldowners[net])
   fixed[name]=+f;assert all(f[n]>=0 for n in f)
  assert all(x['predictions']['native_retained_on']==final['ledger'].get(str(x['node']),0) for x in ch)
  prepared.append(dict(case=case,channels=ch,bins=bs,fixed=fixed,masks=masks,frozen_NETs=len(frozen),frozen_CIDs=len(frozen_cids),overused_initial_resources=len(overused),original_primary_gate_pass=qv['primary_gate_pass']));
  for p in [qp,vp,initialp,ap,rp,fa,finalp]:bindings[str(p)]=sha(p)
  print('LOCAL FROZEN PATH STATES VERIFIED',case,len(dirty),len(expanded),len(frozen_cids),flush=True)
 graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)==idx['graph_sha256']==gpdata['bindings'][str(graph)];bindings[str(graph)]=sha(graph);channel_index={n:i for i,n in enumerate(channels)};bin_index={b:i for i,b in enumerate(bins)};projection={};bin_caps=collections.Counter();stack=[]
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   node=int(n.get('id'))
   if n.get('type') in ['CHANX','CHANY'] and int(n.get('capacity'))>0:
    assert node in channel_index;loc=n.find('loc');seg=n.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1;ids=[]
    for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
     for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
      key=(int(loc.get('layer','0')),x,y,n.get('type'),sid);i=bin_index[key];ids.append(i);bin_caps[i]+=int(n.get('capacity'))
    projection[node]=ids
   parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert set(projection)==set(channels) and all(bin_caps[i]==prepared[0]['bins'][i]['capacity'] for i in range(len(bins)));rows=[];manifest={}
 for case in prepared:
  folder=out/case['case'];folder.mkdir();maskfile=folder/'mutable_NETs.json';maskfile.write_text(json.dumps({k:sorted(v) for k,v in case['masks'].items()}));bindings[str(maskfile)]=sha(maskfile)
  for name,fixed in case['fixed'].items():
   cv=array.array('I',[fixed.get(n,0) for n in channels]);bv=array.array('I',[0])*len(bins)
   for node,v in zip(channels,cv):
    for b in projection[node]:bv[b]+=v
   for domain,values,table in [('channels',cv,case['channels']),('bins',bv,case['bins'])]:
    p=folder/(name+'__'+domain+'.u32');p.write_bytes(values.tobytes());manifest[case['case']+'__'+name+'__'+domain]=dict(path=str(p),sha256=sha(p),values=len(values),typecode='I',byteorder=sys.byteorder);floor_by_cap=collections.Counter();error_by_cap=collections.Counter();positive_by_cap=collections.Counter();forced=0
    for a,row in zip(values,table):
     y=row['labels']['cold'];pred=row['predictions']['native_retained_on'];cap=row['capacity'];assert cap>0 and pred>=a;floor_by_cap[cap]+=max(0,a-y);error_by_cap[cap]+=abs(pred-y);positive_by_cap[cap]+=max(0,pred-y);forced+=a>y
    floor=sum((F(v,c) for c,v in floor_by_cap.items()),F(0))/len(table);current=sum((F(v,c) for c,v in error_by_cap.items()),F(0))/len(table);positive=sum((F(v,c) for c,v in positive_by_cap.items()),F(0))/len(table);assert floor<=current;rows.append(dict(case=case['case'],mask=name,domain=domain,mutable_NETs=len(case['masks'][name]),fixed_NETs=55300-len(case['masks'][name]),current_endpoint_only_frozen_CIDs=case['frozen_CIDs'],coordinates=len(table),coordinates_with_unavoidable_overprediction=forced,optimistic_normalized_MAE_lower_bound=str(floor),optimistic_normalized_MAE_lower_bound_float=float(floor),current_normalized_MAE=str(current),current_normalized_MAE_float=float(current),lower_bound_share_of_current_MAE=float(floor/current) if current else None,lower_bound_share_of_current_overprediction=float(floor/positive) if positive else None,original_primary_gate_pass=case['original_primary_gate_pass']))
  print('LOCAL SUPPORT BOUNDS COMPLETE',case['case'],flush=True)
 (out/'vector_manifest.json').write_text(json.dumps(manifest,indent=2))
 with (out/'results.json').open('x') as f:json.dump(dict(status='all3_local_frozen_state_checks_and12_exact_support_bounds_computed',bindings=bindings,rows=rows,case_summary=[{k:v for k,v in x.items() if k not in ['channels','bins','fixed','masks']} for x in prepared],scope=plan['limits'],independent_verification_pending=True),f,indent=2)
if __name__=='__main__':main()

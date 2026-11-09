"""Source-only whole-NET two-edge channel rerouting support pilot, no commits."""
import sys,json,collections,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';cp=E/'mmc_typed_collision_risk_v1_2026-10-18/protocol.json';config=json.loads(cp.read_text());gp=E/'mmc_typed_collision_risk_v1_2026-10-18/groups.json';g=json.loads(gp.read_text());group_of={n:i for i,v in enumerate(g['groups']) if v['kind']=='geometry_channel' for n in v['members']};proofp=E/'mmc_anchored_NET_forecasts_verification_v1_2026-10-18/verification.json';proof=json.loads(proofp.read_text());out=E/'mmc_channel_diamond_support_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [cp,gp,proofp]};bindings.update(closure([Path(__file__)]));inputs={}
 for case,v in config['inputs'].items():
  path=Path(v['predictions']['native_retained_on']);assert sha(path)==proof['bindings'][str(path)];inputs[case]=dict(frame=str(path),endpoint=v['endpoint']);bindings[str(path)]=sha(path);bindings[v['endpoint']]=sha(v['endpoint'])
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,inputs=inputs,NET_limit_per_case=128,selection='First128NETs by numeric NET ID that contain any two-edge all-channel subpath; all source-only, no label selection.',candidate='Replace all occurrences of old(u,w,v) with(u,new_w,v), where new_w outside entire old NET footprint, different channel group, and every occurrence of old_w is exactly this pair. Same source/sink, directed positive-capacity edges, wholeNET single-parent state and all changed-query original exact additive RC budgets required. Lexicographic old physical edge pair then new physical edge pair; first admissible candidate per NET.',scope='New support feasibility pilot only, no objective-approved commits, native runs, new forecasts, timing/route/family claims.'),indent=2))
 cache=Cache();summaries=[]
 with cache.installed():
  print('CHANNEL SUPPORT GRAPH LOAD',flush=True);tick=time.perf_counter();graph,digest,nodes,f,rc,_=load_endpoints(inputs['case_01']['endpoint']);setup=time.perf_counter()-tick;offsets=f['row_offsets'];dest=f['dest_ranks'];ids=f['edge_ids'];caps=f['capacities'];slots={e:s for s,e in enumerate(ids)};assert digest==g['graph_sha256']
  for case,input in inputs.items():
   frame=json.loads(Path(input['frame']).read_text());assert frame['scale']==rc.scale;endpoint=json.loads(Path(input['endpoint']).read_text());queries={q['connection_id']:q for q in endpoint['connections']};nets=collections.defaultdict(list)
   for r in frame['records']:assert all(r[k]==queries[r['connection_id']][k] for k in ['net_id','source','sink']);nets[r['net_id']].append(r)
   eligible=[];candidates_by_net={}
   for net in sorted(nets):
    candidates={}
    for r in nets[net]:
     path=r['answer']['physical_edge_ids'];node=r['source']
     for i,e in enumerate(path[:-1]):
      w=dest[slots[e]];v=dest[slots[path[i+1]]]
      if node in group_of and w in group_of and v in group_of:candidates[e,path[i+1]]=(node,w,v)
      node=w
    if candidates:eligible.append(net);candidates_by_net[net]=candidates
    if len(eligible)==128:break
   results=[];reject=collections.Counter()
   for net in eligible:
    rows=nets[net];owned={r['source'] for r in rows};parent={};valid=True
    for r in rows:
     for e in r['answer']['physical_edge_ids']:
      v=dest[slots[e]];owned.add(v)
      if v in parent and parent[v]!=e:valid=False
      parent[v]=e
    if not valid:reject['baseline_parent_conflict']+=1;continue
    chosen=None
    for pair,(u,w,v) in sorted(candidates_by_net[net].items()):
     affected=[];supported=True
     for r in rows:
      path=r['answer']['physical_edge_ids'];positions=[i for i,e in enumerate(path) if dest[slots[e]]==w]
      if positions:
       if len(positions)!=1 or positions[0]+1>=len(path) or tuple(path[positions[0]:positions[0]+2])!=pair:supported=False;break
       affected.append((r,positions[0]))
     if not supported:reject['old_vertex_shared_other_branch']+=1;continue
     options=[]
     for s1 in range(offsets[u],offsets[u+1]):
      new=dest[s1]
      if new not in group_of or new in owned or group_of[new]==group_of[w] or caps[new]<=0:continue
      for s2 in range(offsets[new],offsets[new+1]):
       if dest[s2]==v:options.append((ids[s1],ids[s2],new,s1,s2))
     for e1,e2,new,s1,s2 in sorted(options):
      delta=rc.increment(s1)+rc.increment(s2)-rc.increment(slots[pair[0]])-rc.increment(slots[pair[1]]);changes=[]
      for r,i in affected:
       delay=r['answer']['delay']+delta
       if delay<0 or delay>r['budget_integer']:break
       path=r['answer']['physical_edge_ids'];changes.append(dict(connection_id=r['connection_id'],old_delay=r['answer']['delay'],new_delay=delay,budget=r['budget_integer'],old_edges=path,new_edges=path[:i]+[e1,e2]+path[i+2:]))
      else:
       chosen=dict(net_id=net,old_pair=list(pair),new_pair=[e1,e2],old_node=w,new_node=new,old_group=group_of[w],new_group=group_of[new],changes=changes);break
      reject['budget_rejected']+=1
     if chosen:break
    if chosen:results.append(chosen)
    else:reject['no_admitted_diamond']+=1
   p=out/(case+'_proposals.json');p.write_text(json.dumps(results,separators=(',',':')));summary=dict(case=case,selected_NETs=len(eligible),proposals=len(results),changed_queries=sum(len(x['changes']) for x in results),rejections=dict(reject),proposals_file=str(p),sha256=sha(p));summaries.append(summary);print('CHANNEL SUPPORT CASE DONE',json.dumps(summary),flush=True)
  for p,h in bindings.items():assert sha(p)==h
  with (out/'receipt.json').open('x') as f:json.dump(dict(status='all_three_channel_diamond_support_pilots_computed',bindings=bindings,graph_setup_seconds=setup,scale=rc.scale,summaries=summaries,independent_verification_pending=True,scope='Source-only topology/budget feasibility proposals, original state unchanged. Exact additive model budget is not native STA or complete-tree RC timing. No occupancy objective approval, concurrent proposal compatibility, model commit or routing outcome.'),f,indent=2)
if __name__=='__main__':main()

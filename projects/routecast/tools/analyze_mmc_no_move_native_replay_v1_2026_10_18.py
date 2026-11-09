"""No-move native replay path and full channel/span footprint comparison."""
import json,sys,time,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths
from prediction_metrics import compare
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_no_move_native_replay_v1_2026-10-18';vp=D/'verification.json';v=json.loads(vp.read_text());assert v['all3no_move_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in v['bindings'].items());bindings={**v['bindings'],**closure([Path(__file__)]),str(vp):sha(vp)}
gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(gp.read_text());ep=Path(g['previous_endpoint']);meta=json.loads(ep.read_text());oldroute=Path(g['previous_native_route']);old=mapped_paths(meta,oldroute);source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';oldframe=json.loads(source.read_text());ledgers={'previous':{int(n):x for n,x in oldframe['ledger'].items()}};paths={'previous':old};rows=[]
for arm in ['full_seed_a','cold','full_seed_b']:
 route=D/arm/'output.route';paths[arm]=mapped_paths(meta,route);a=json.loads((D/arm/'physical_audit.json').read_text());assert a['inputs_sha256']['route']==sha(route) and a['overflow_units']==0;ledgers[arm]={int(n):x for n,x in a['node_occupancy'].items()};changed=[cid for cid in old if old[cid]!=paths[arm][cid]];nets={q['connection_id']:q['net_id'] for q in meta['connections']};changed_nets={nets[cid] for cid in changed}
 rows.append(dict(arm=arm,changed_connections_from_previous=len(changed),changed_NETs_from_previous=len(changed_nets),placement_changed=False,whole_occupancy_maps_equal_previous=ledgers[arm]==ledgers['previous'],physical_paths_equal_previous=not changed))
repeated=dict(full_seed_physical_paths_equal=paths['full_seed_a']==paths['full_seed_b'],full_seed_occupancy_maps_equal=ledgers['full_seed_a']==ledgers['full_seed_b'],full_seed_route_file_bytes_equal=sha(D/'full_seed_a/output.route')==sha(D/'full_seed_b/output.route'))
channels=[];bins={};stack=[];graph=Path(meta['inputs']['graph']['path'])
for event,node in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(node);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if node.tag=='node' and parent=='rr_nodes':
  cap=int(node.get('capacity'));kind=node.get('type');nid=int(node.get('id'))
  if cap>0 and kind in ['CHANX','CHANY']:
   counts={m:l.get(nid,0) for m,l in ledgers.items()};channels.append(dict(node=nid,capacity=cap,counts=counts));loc=node.find('loc');seg=node.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
   for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
    for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
     key=(int(loc.get('layer','0')),x,y,kind,sid)
     if key not in bins:bins[key]=dict(key=key,capacity=0,counts={m:0 for m in ledgers})
     b=bins[key];b['capacity']+=cap
     for m,value in counts.items():b['counts'][m]+=value
  stack[-2].remove(node);node.clear()
 if node.tag=='rr_nodes':break
 stack.pop()
metrics={}
for arm in ['full_seed_a','cold','full_seed_b']:
 metrics[arm]={}
 for scope,data,key,k in [('concrete',channels,'node',max(1,len(channels)//20)),('spatial',list(bins.values()),'key',20)]:
  identity=lambda x:tuple(x[key]) if key=='key' else x[key]
  p={identity(x):x['counts']['previous']/x['capacity'] for x in data};t={identity(x):x['counts'][arm]/x['capacity'] for x in data};metrics[arm][scope]=compare(p,t,k)
 for row in rows:
  if row['arm']==arm:row['changed_channel_nodes_from_previous']=sum(x['counts'][arm]!=x['counts']['previous'] for x in channels)
with (D/'repeatability_vectors.json').open('x') as f:json.dump(dict(channels=channels,bins=[bins[k] for k in sorted(bins)]),f)
for p in [ep,oldroute,source,D/'repeatability_vectors.json']:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'repeatability_analysis_v1.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,repeated_full_seed=repeated,metrics_against_previous=metrics,positive_channel_universe=len(channels),spatial_span_universe=len(bins),scope='No-placement-change path/occupancy reproducibility with current binary. Fullseed replay and cold reroute are different initialization conditions. Previous source route used an earlier pipeline; no causal separation of binary/version and cold initialization without additional matched controls. No independent metric recomputation yet, unseen or total-time claim.'),f,indent=2)
print(json.dumps(dict(rows=rows,repeated_full_seed=repeated,metrics=metrics)),flush=True)

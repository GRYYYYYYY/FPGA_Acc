"""Fixed bounded development experiment: whole-net rip-up, unique-net demand."""
import heapq,json,time,shutil
from pathlib import Path
from collections import Counter,defaultdict
from prepared_csr import read,U64
from pre_route_endpoints import sha


def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_negotiated_capacity_v2_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('predict_cw32_negotiated_capacity_v2.py','prepared_csr.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'iterations':10,'order':'ascending NET/CID, same order each iteration','cost':'original scalar edge cost multiplied by 1 + current_other_net_demand/capacity + historical_overuse/capacity; exact integer ordering uses ceiling; capacity-zero disabled','history':'add max(0,unique-net-demand-capacity) each iteration for every node','state':'rip up full NET union before querying SOURCE to all distinct SINKs; no same-net demand duplication','sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Fixed development cohort with labels already exposed; no electrical/route-tree feasibility guarantee, no timing budget admission, no native feedback gain claim; all iterations retained, final iteration used without best-label selection.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
 for name in protocol['cohort']:
  start=time.monotonic();dest=out/name;dest.mkdir();front=root/'experiments/multiplier_family_endpoints_cw32_2026-10-06'/name;fp=json.loads((front/'protocol.json').read_text());fr=json.loads((front/'receipt.json').read_text());assert sha(front/'protocol.json')==fr['protocol_sha256'];assert sha(front/'endpoints.json')==fr['outputs']['endpoints.json'];ep=json.loads((front/'endpoints.json').read_text());graph=fp['inputs']['rr_graph'];assert sha(graph['path'])==graph['sha256']
  prepared=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name;m,f=read(prepared/'csr',graph['sha256']);assert all(i==n for i,n in enumerate(f['node_ids']));groups=defaultdict(list)
  for r in ep['connections']:groups[r['net_id']].append(r)
  occ=Counter();history=Counter();unions={};paths={};trace=[];visits=0
  for iteration in range(1,11):
   for net,cohort in sorted(groups.items()):
    occ.subtract(unions.get(net,set()));assert all(v>=0 for v in occ.values())
    sources={r['source'] for r in cohort};assert len(sources)==1;source=next(iter(sources));targets={r['sink'] for r in cohort};remaining=set(targets);dist={source:0};parent={};queue=[(0,source)];settled=set()
    while queue and remaining:
     value,node=heapq.heappop(queue)
     if value!=dist[node] or node in settled:continue
     settled.add(node);remaining.discard(node)
     for slot in range(f['row_offsets'][node],f['row_offsets'][node+1]):
      visits+=1;base=f['costs'][slot];sink=f['dest_ranks'][slot];cap=f['capacities'][sink]
      if base==U64 or cap==0:continue
      factor=cap+occ[sink]+history[sink];cost=(base*factor+cap-1)//cap;candidate=value+cost
      if candidate<dist.get(sink,float('inf')):dist[sink]=candidate;parent[sink]=(node,f['edge_ids'][slot]);heapq.heappush(queue,(candidate,sink))
    assert not remaining,'relaxed graph unexpectedly unreachable';used={source}
    for sink in sorted(targets):
     node=sink;edges=[];seen=set()
     while node!=source:
      assert node not in seen;seen.add(node);used.add(node);node,eid=parent[node];edges.append(eid)
     paths[(net,sink)]=list(reversed(edges))
    unions[net]=used;occ.update(used)
   excess={n:max(0,d-f['capacities'][n]) for n,d in occ.items()};history.update({n:v for n,v in excess.items() if v});row={'iteration':iteration,'all_type_overuse_units':sum(excess.values()),'channel_overuse_units':sum(v for n,v in excess.items() if f['types'][n] in (4,5)),'overused_nodes':sum(v>0 for v in excess.values())};trace.append(row);print(json.dumps({'design':name,**row}),flush=True)
  prediction={'physical_graph_sha256':graph['sha256'],'connections':[{**r,'physical_edge_ids':paths[(r['net_id'],r['sink'])],'method':'negotiated_capacity_fixed10'} for r in ep['connections']],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(ep['connections']),'completed':len(ep['connections']),'methods':{'negotiated_capacity_fixed10':len(ep['connections'])}};(dest/'prediction.json').write_text(json.dumps(prediction)+'\n');(dest/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
  assert sha(graph['path'])==graph['sha256'];result={'design':name,'graph':graph,'endpoint_path':str(front/'endpoints.json'),'endpoint_sha256':sha(front/'endpoints.json'),'prediction_sha256':sha(dest/'prediction.json'),'trace_sha256':sha(dest/'trace.json'),'wall_s':time.monotonic()-start,'edge_visits':visits,'final':trace[-1]};(dest/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results},indent=2)+'\n')
if __name__=='__main__':main()

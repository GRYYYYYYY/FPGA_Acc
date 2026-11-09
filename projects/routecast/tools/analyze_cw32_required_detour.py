"""Per-conflict necessary uniform scalar slack; independent constraints not summed."""
import json,heapq,shutil
from pathlib import Path
from prepared_csr import read,U64
from pre_route_endpoints import sha

def main():
 root=Path(__file__).resolve().parents[1];parent=root/'experiments/multiplier_cw32_scalar_mandatory_nodes_2026-10-06';out=root/'experiments/multiplier_cw32_required_detour_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('analyze_cw32_required_detour.py','prepared_csr.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 pr=json.loads((parent/'receipt.json').read_text());protocol={'parent_receipt_sha256':sha(parent/'receipt.json'),'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'method':'For each forced conflict node, delete it and compute unconstrained scalar shortest path to every mandatory sink; NET avoidance slack=max over its affected connections; need demand-capacity NETs to avoid node; select kth cheapest NET slack. Maximum across nodes is necessary uniform additive per-connection slack, not sufficient or additive across nodes. Unreachable avoidance represented null/infinite.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');summary=[]
 for case in pr['results']:
  name=case['design'];dest=out/name;dest.mkdir();conf=parent/name/'conflicts.json';conn=parent/name/'connections.json';assert sha(conf)==case['conflicts_sha256'] and sha(conn)==case['connections_sha256'];conflicts=json.loads(conf.read_text());connections=json.loads(conn.read_text());prep=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name;p=json.loads((prep/'protocol.json').read_text());m,f=read(prep/'csr',p['graph']['sha256']);reports=[];cache={}
  for c in conflicts:
   removed=c['node'];slacks=[]
   for net in c['nets']:
    affected=[r for r in connections if r['net_id']==net and removed in r['mandatory_nodes']];assert affected;per=[]
    for r in affected:
     s,t=r['source'],r['sink'];key=(removed,s)
     if key not in cache:
      d={} if s==removed else {s:0};q=[] if s==removed else [(0,s)]
      while q:
       value,u=heapq.heappop(q)
       if value!=d[u]:continue
       for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
        v=f['dest_ranks'][slot];base=f['costs'][slot]
        if v==removed or base==U64 or f['capacities'][v]==0:continue
        nd=value+base
        if nd<d.get(v,float('inf')):d[v]=nd;heapq.heappush(q,(nd,v))
      cache[key]=d
     shortest=cache[key].get(t);delta=None if shortest is None else shortest-r['scalar_budget'];assert delta is None or delta>0;per.append({'connection_id':r['connection_id'],'baseline':r['scalar_budget'],'avoid_shortest':shortest,'slack':delta})
    net_slack=None if any(r['slack'] is None for r in per) else max(r['slack'] for r in per);slacks.append({'net_id':net,'necessary_slack':net_slack,'connections':per})
   k=c['required_unique_nets']-c['capacity'];finite=sorted(r['necessary_slack'] for r in slacks if r['necessary_slack'] is not None);bound=finite[k-1] if len(finite)>=k else None;reports.append({'node':removed,'capacity':c['capacity'],'demand':c['required_unique_nets'],'nets_required_to_avoid':k,'necessary_uniform_slack':bound,'net_slacks':slacks})
  (dest/'conflicts.json').write_text(json.dumps(reports,indent=2)+'\n');bounds=[r['necessary_uniform_slack'] for r in reports];row={'design':name,'conflicts':len(reports),'uniform_scalar_slack_lower_bound':None if any(x is None for x in bounds) else max(bounds,default=0),'avoidance_unreachable_conflicts':sum(x is None for x in bounds),'conflict_report_sha256':sha(dest/'conflicts.json')};summary.append(row);print(json.dumps(row),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':summary},indent=2)+'\n')
if __name__=='__main__':main()

"""Native-label raw-delay vs frozen forecast budgets, diagnostic without gate changes."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from zero_rc_budget_certificate_graph_v1 import load_graph
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';D=E/'prospective_external_family_native_label_budget_compatibility_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);spec=read(P/'specifications/w160/episode_01/comparison_spec.json');ep=read(spec['endpoint']);graph=ep['inputs']['graph']['path'];assert sha(graph)==ep['graph_sha256'];g=load_graph(graph);arcs={(u,v,s) for u,v,s in zip(g['us'],g['vs'],g['switches'])};bindings={graph:sha(graph),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';sp=P/'specifications'/case/'comparison_spec.json';s=read(sp);ep=read(s['endpoint']);proof=read(s['label_proof']);assert proof['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and all(sha(p)==h for p,h in proof['bindings'].items());folder=Path(s['label_physical_audit']).parent;route=folder/'output.route';assert proof['bindings'][str(route)]==sha(route);frame=read(P/'predictions'/case/'native_retained_on/initial.json');budget={r['connection_id']:r for r in frame['records']};paths={}
  for name,branches in physical_paths(route).items():
   for path in branches:
    key=(name,path[0][0],path[-1][0]);assert key not in paths;paths[key]=path
  expected={(ep['net_names'][str(q['net_id'])],q['source'],q['sink']):q for q in ep['connections']};assert paths.keys()==expected.keys();records=[]
  for key,q in expected.items():
   path=paths[key];raw=0
   for (u,_),(v,switch) in zip(path,path[1:]):assert (u,v,switch) in arcs;raw+=g['weights'][switch]
   b=budget[q['connection_id']]['budget_integer'];records.append(dict(connection_id=q['connection_id'],net_id=q['net_id'],native_raw_delay_integer=raw,forecast_budget_integer=b,over_budget=raw>b,excess_integer=max(0,raw-b)))
  over=[r for r in records if r['over_budget']];out=D/case;out.mkdir(parents=True);rp=out/'all_CIDs.json';rp.write_text(json.dumps(records,indent=2)+'\n');row=dict(case=case,connections=len(records),native_CIDs_over_forecast_budget=len(over),NETs_with_native_over_budget=len({r['net_id'] for r in over}),max_excess_integer=max((r['excess_integer'] for r in over),default=0),scale=10**18);rows.append(row)
  for p in [sp,rp,route,Path(s['label_proof']),P/'predictions'/case/'native_retained_on/initial.json']:bindings[str(p)]=sha(p)
  print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_NATIVE_LABEL_PATHS_ORIGINAL_ZERO_RC_GRAPH_AND_FROZEN_BUDGETS_COMPARED',rows=rows,bindings=bindings,scope='load_graph proves every node/switch R/C zero, sum original switch Tdel*1e18 exact. Native raw delay need not satisfy heuristic forecast budgets. Descriptive compatibility only, no permission to relax budgets/labels/gates, no proof ranking acceptance impossible.'),indent=2)+'\n')
if __name__=='__main__':main()

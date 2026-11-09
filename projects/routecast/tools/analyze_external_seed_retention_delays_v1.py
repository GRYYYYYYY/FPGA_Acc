"""Fixed all3 posthoc CID path retention and zero-RC delay diagnostics; no policy fit."""
import json,sys,hashlib,csv,re,statistics
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
from zero_rc_budget_certificate_graph_v1 import load_graph
D=R/'experiments/prospective_external_family_seed_retention_delay_diagnosis_v1_2026-10-19'
P=R/'experiments/prospective_external_family_native_seed_delay_handoff_v1_2026-10-19'
S=R/'experiments/prospective_external_family_native_utility_seed_inputs_v1_2026-10-19'
T=R/'experiments/prospective_external_family_frame_timings_v1_2026-10-19'
G=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 v=read(P/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());D.mkdir(exist_ok=False)
 inputs=[P/'verification.json',G,Path(__file__).resolve()]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';inputs += [S/case/'seed.route',T/case/'initial_connection_criticalities.json']
  for arm in ('cold','seed'):inputs += [P/case/arm/'native/output.route',P/case/arm/'native/report_timing.setup.rpt',P/case/arm/'native/initial_connections.tsv']
 bindings={str(p):sha(p) for p in inputs}
 (D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Posthoc diagnosis all3, not training/tuning or causal proof. Exact physical node+incoming switch paths by name/source/sink; repeated endpoints must have identical paths. Raw delay original XML zero-RC switch sum; not complete STA or atom report increment. Fixed raw initial criticality deciles; no threshold selection or gate change. Worst report paths only summarize endpoints/slack, no unverified atom-to-packed mapping.'),indent=2)+'\n')
 graph=load_graph(G);print('GRAPH_KEYS',list(graph),flush=True)
 weights=graph['weights'];edges=set(zip(graph['us'],graph['vs'],graph['switches']))
 def paths(p):
  out={}
  for name,ps in physical_paths(p).items():
   for path in ps:
    key=(name,path[0][0],path[-1][0]);assert key not in out or out[key]==path;out[key]=path
    for (u,_),(w,switch) in zip(path,path[1:]):assert (u,w,switch) in edges
  return out
 def delay(path):return sum(weights[sw] for n,sw in path[1:])
 summaries=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';payload=read(T/case/'initial_connection_criticalities.json');assert len(payload)==15616
  cold=paths(P/case/'cold/native/output.route');final=paths(P/case/'seed/native/output.route');seed=paths(S/case/'seed.route')
  initial={(int(q['net']),int(q['pin'])):float(q['criticality']) for q in csv.DictReader((P/case/'cold/native/initial_connections.tsv').open(),delimiter='\t')}
  rows=[]
  for q in payload:
   k=(q['net_name'],q['source_rr'],q['target_rr']);a,b=cold[k],final[k];s=seed.get(k);crit=initial[(q['native_net_id'],q['local_sink_pin'])]
   da,db=delay(a),delay(b)
   rows.append(dict(connection_id=q['connection_id'],native_net_id=q['native_net_id'],local_pin=q['local_sink_pin'],net_name=q['net_name'],source_rr=k[1],sink_rr=k[2],initial_raw_criticality=crit,decile=min(9,max(0,int(crit*10))),seed_admitted=s is not None,seed_path_preserved=s==b if s else False,seed_path_equals_cold=s==a if s else False,final_equals_cold=a==b,cold_delay_as=da,final_delay_as=db,delta_as=db-da,seed_delay_as=delay(s) if s else None))
  assert len({q['connection_id'] for q in rows})==15616
  def summarize(rs):
   return dict(CIDs=len(rs),seed_admitted=sum(r['seed_admitted'] for r in rs),seed_preserved=sum(r['seed_path_preserved'] for r in rs),final_equals_cold=sum(r['final_equals_cold'] for r in rs),delay_worse=sum(r['delta_as']>0 for r in rs),delay_better=sum(r['delta_as']<0 for r in rs),delay_equal=sum(r['delta_as']==0 for r in rs),sum_delta_as=sum(r['delta_as'] for r in rs),preserved_worse=sum(r['seed_path_preserved'] and r['delta_as']>0 for r in rs),rerouted_admitted_worse=sum(r['seed_admitted'] and not r['seed_path_preserved'] and r['delta_as']>0 for r in rs))
  reports={}
  for arm in ('cold','seed'):
   text=(P/case/arm/'native/report_timing.setup.rpt').read_text().split('#Path 2')[0];reports[arm]={key:re.search(pattern,text)[1].strip() for key,pattern in [('startpoint',r'Startpoint:\s*(.+)'),('endpoint',r'Endpoint\s*:\s*(.+)'),('slack_ns',r'slack \([^)]*\)\s*([-0-9.]+)')]}
  out=D/case;out.mkdir(parents=True);(out/'connections.json').write_text(json.dumps(rows)+'\n');summary=dict(case=case,all=summarize(rows),by_initial_raw_criticality_decile={str(d):summarize([r for r in rows if r['decile']==d]) for d in range(10)},worst_setup_report=reports);summaries.append(summary);print(json.dumps(summary),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'diagnosis.json').write_text(json.dumps(dict(status='ALL3_FULL_CID_PHYSICAL_PATH_AND_ZERO_RC_DELAY_DIAGNOSED',rows=summaries,bindings=bindings,limitations='Exact path retention is observational, not a causal seed-only attribution. Raw route delay excludes cell/internal packed timing. Final critical paths can differ. No atom-to-packed pin mapping claimed.'),indent=2)+'\n')
if __name__=='__main__':main()

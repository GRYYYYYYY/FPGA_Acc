"""Authenticate complete search schedule and summarize diagnostic operations."""
import json,sys,math
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
name=sys.argv[1];out=Path(sys.argv[2]).resolve()
def load(p):return json.loads(p.read_text())
def auth(d):
 for section in ['bindings','files']:
  for p,h in d.get(section,{}).items():assert sha(p)==h,p
receipt=load(out/'receipt.json');auth(receipt)
parity=load(out/'parity_verification.json');auth(parity)
assert parity['name']==name and parity['all_five_complete_state_files_byte_equal'] and parity['all_feedback_events_price_schedule_epoch_and_outcome_equal']
endpoint=next(Path(p) for p in receipt['bindings'] if p.endswith('/endpoints.json'))
ep=load(endpoint);groups=defaultdict(list)
for q in ep['connections']:groups[q['net_id']].append(q)
work=load(out/'search_work.json');schedule=[('initial',n) for n in sorted(groups)]
for r in receipt['rounds']:schedule += [(f"round{r['round_index']}",n) for n in r['affected_nets']]
assert work['initial_queries']==len(groups) and work['round_queries']==[len(r['affected_nets']) for r in receipt['rounds']]
assert len(work['metrics'])==len(schedule)
phase=defaultdict(list);details=[]
for (stage,net),metric in zip(schedule,work['metrics']):
 qs=groups[net];assert len({q['source'] for q in qs})==1
 assert metric['source']==qs[0]['source'] and metric['targets']==len({q['sink'] for q in qs})
 for k,v in metric.items():assert isinstance(v,int) and v>=0
 assert metric['pushes']==metric['relaxations']+1 and metric['pops']<=metric['pushes']
 assert metric['stale']<=metric['pops'] and metric['settled']<=metric['touched'] and metric['settled']<=metric['pops']-metric['stale']
 detail=dict(metric,phase=stage,net_id=net,connections=len(qs));phase[stage].append(detail);details.append(detail)
def summarize(rows):
 arcs=sorted((m['scanned_arcs'] for m in rows),reverse=True);total=sum(arcs)
 return dict(queries=len(rows),operation_totals={k:sum(x[k] for x in rows) for k in ['settled','scanned_arcs','pushes','pops','stale','relaxations','touched','reset_nodes']},max_scanned_arcs=arcs[0],top_one_percent_query_arc_share=sum(arcs[:max(1,math.ceil(len(arcs)/100))])/total if total else 0,one_target_queries=sum(x['targets']==1 for x in rows),one_target_arc_share=sum(x['scanned_arcs'] for x in rows if x['targets']==1)/total if total else 0,top_queries=sorted(rows,key=lambda x:(-x['scanned_arcs'],x['net_id']))[:10])
bindingpaths=[Path(__file__),out/'receipt.json',out/'parity_verification.json',out/'search_work.json',endpoint]
bindings={str(p):sha(p) for p in bindingpaths}
result=dict(bindings=bindings,name=name,complete_search_schedule_and_operation_invariants_pass=True,phases={k:summarize(v) for k,v in phase.items()},all_queries=summarize(details),scope='Complete instrumented model, original full-state/event parity; operation counts not time attribution or paired performance. Independent physical legality/RC follows byte-identical audited reference states, not fresh native routing or HDL/heldout evidence.')
assert all(sha(p)==h for p,h in bindings.items())
(out/'search_work_verification_v1.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(name=name,queries=len(schedule),phases={k:{x:y for x,y in v.items() if x not in ['top_queries','operation_totals']}|{'scanned_arcs':v['operation_totals']['scanned_arcs']} for k,v in result['phases'].items()}),indent=2))

"""Full12 archived independent Fraction comparison and epoch negative checks."""
import json,time,hashlib,copy
from pathlib import Path
from actual_change_budget_recheck_v1_2026_10_18 import BudgetRecheck
from unified_rr_audit_inventory_v1 import read
from memoized_fraction_path_delay_unified_v1 import FractionPathMemo
R=Path(__file__).resolve().parents[1];D=R/'experiments/actual_change_budget_recheck_v1_2026-10-18';D.mkdir(exist_ok=False);bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases'];rows=[];negatives=[];start=time.perf_counter()
for width in (8,16,32):
 selected=[c for c in cases if c['width']==width];old=load(selected[0]['old']);graph=Path(old['inputs']['graph']['path']);tick=time.perf_counter();inventory=read(graph,old['graph_sha256']);memo=FractionPathMemo(graph,old['graph_sha256'],inventory);route=graph.with_name('design.route');state=BudgetRecheck(old,route,memo);setup=time.perf_counter()-tick;bindings[str(route)]=sha(route)
 for c in selected:
  w,i=c['width'],c['index'];target=load(c['target']);budget=load(c['budget']);out=R/f'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w{w}_m{i}';reference=load(out/'original_budget_verification.json');bindings[str(out/'output.route')]=sha(out/'output.route')
  tick=time.perf_counter();result=state.evaluate(target,out/'output.route',budget,memo);elapsed=time.perf_counter()-tick
  assert result['rows']==reference['rows'] and result['violation_ids']==reference['violation_ids']
  rows.append(dict(width=w,index=i,connections=len(result['rows']),recomputed=len(result['changed_connection_ids']),reused=result['reused_delays'],violations=len(result['violation_ids']),setup_seconds=setup if i==0 else 0,update_seconds=elapsed,all_fraction_rows_equal=True))
  if i==0:
   for mode in ['graph','net','identity','duplicate','missing']:
    bad=copy.deepcopy(target)
    if mode=='graph':bad['graph_sha256']='0'*64
    elif mode=='net':bad['inputs']['net']['sha256']='0'*64
    elif mode=='identity':bad['connections'][0]['net_id']=-1
    elif mode=='duplicate':bad['connections'].append(dict(bad['connections'][0]))
    elif mode=='missing':bad['connections'].pop()
    try:state.evaluate(bad,out/'output.route',budget,memo)
    except (ValueError,KeyError):negatives.append(dict(width=w,mode=mode,rejected=True))
    else:raise AssertionError('Invalid epoch accepted: '+mode)
  print(w,i,'recomputed',rows[-1]['recomputed'],'reused',rows[-1]['reused'],flush=True)
 for entry in old['inputs'].values():bindings[entry['path']]=entry['sha256']
for name in ['actual_change_budget_recheck_v1_2026_10_18.py','verify_actual_change_budget_recheck_v1_2026_10_18.py','native_route_ledger_import_compact.py','memoized_fraction_path_delay_unified_v1.py','unified_rr_audit_inventory_v1.py']:
 p=R/'tools'/name;bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,rows=rows,negative_cases=negatives,component_seconds=time.perf_counter()-start,all12_full_fraction_rows_equal=True,scope='Budget recheck component only, freshly prepared old exact delays and full route scans paid. Not physical/canonical/occupancy/native acceptance, independent heldout evaluation or paired speed claim. Reference is archived independent full original XML/Fraction audit. Initial preparation and perupdate times are separate observations, no end-to-end inference.',remaining=['Independent delta physical/NET-union/canonical acceptance','Stale old-route mutation and omitted-path negative fixtures','Matched component timing with identical cold caches and full admission','Prospective matched native-state full-cost workflow'])
with (D/'verification.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')

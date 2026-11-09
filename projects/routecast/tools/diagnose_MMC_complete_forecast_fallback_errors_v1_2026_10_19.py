"""Descriptive connection/fallback coverage and additive magnitude-error accounting."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
import json,hashlib,struct,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_complete_forecast_fallback_error_diagnosis_v1_2026-10-19';O.mkdir(exist_ok=False);M=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19';closure=R/'experiments/mmc_complete_static_criticality_study_closure_v1_2026-10-19/research_decision_v1.json';assert json.loads(closure.read_text())['status']=='CLOSED_ALL3_COMPLETE_STATIC_CRITICALITY_FORECAST_COLD_QUALITY_GATES_FAILED_NOT_PROMOTED';receipt=M/'receipt.json';prod=json.loads(receipt.read_text());quality=R/'experiments/mmc_complete_static_criticality_cold_quality_v1_2026-10-19/results.json';qdoc=json.loads(quality.read_text());protocol=json.loads((M/'protocol.json').read_text());graph=next(Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'));channels={};stack=[];bindings={str(p):sha(p) for p in [closure,receipt,quality,graph,Path(__file__).resolve()]}
 spec={'scope':'Exposed all3 selected states; diagnostic only, no new routing/predictor/parameter or primary gate.','partition':'Existing COMMITTED/RETAIN_PRIMARY_FAILURE/RETAIN_OVERFLOW_INCREASE/RETAIN_OBJECTIVE_INCREASE','magnitude_error':'For each resource with D=sum_g Dg and native truth T, overprediction=max(D-T,0)/cap. Allocate overprediction proportionally Dg/D, exact rational conservation. Underprediction has no observed-group assignment.','conditional_lower_bound':'For each group fixed as observed, max(Dg-T,0)/cap is unavoidable if all other groups can contribute any nonnegative demand; bounds across groups are not additive.','prefix_scope':'Failed-query order/prefix length reconstructed from frozen criticality/localpin/CID order and first-failure contract. No partial path bytes or causal quality claim.'};(O/'protocol.json').write_text(json.dumps(spec,indent=2)+'\n')
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:channels[int(e.get('id'))]=int(e.get('capacity'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720;rows=[]
 for case in protocol['cases']:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());groups=defaultdict(list)
  for q in meta['connections']:groups[q['net_id']].append(q)
  timing=R/f'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/{case}/initial_connection_criticalities.json';ct={x['connection_id']:x for x in json.loads(timing.read_text())};selected=M/case/'records.jsonl';budgets={r['connection_id']:r['budget_integer'] for r in map(json.loads,selected.read_text().splitlines())};events=M/case/'events.jsonl';group_demand=defaultdict(Counter);group_stats=defaultdict(Counter);failures=[];seen=set();reconstructed_paid_expansions=0;cache_misses=0;cache_hits=0
  for line in events.open():
   x=json.loads(line);net=x['net_id'];assert net not in seen;seen.add(net);status=x['decision'];stats=group_stats[status];stats['NETs']+=1;stats['connections']+=x['connections'];assert x['connections']==len(groups[net]);group_demand[status].update(n for n in x['chosen_owned'] if n in channels);cache_hits+=x['proposal_cache_hit'];cache_misses+=not x['proposal_cache_hit']
   if not x['primary_complete']:
    ordered=[]
    for q in groups[net]:
     c=ct[q['connection_id']];v=struct.unpack('<f',struct.pack('<f',float(c['criticality_float32_text'])))[0];ordered.append((-Fraction(*v.as_integer_ratio()),c['local_sink_pin'],q['connection_id']))
    order=[q[2] for q in sorted(ordered)];f=x['primary_failure'];cid=f['connection_id'];position=order.index(cid);unsearched=len(order)-position-1;stats['logical_committed_prefix_connections_discarded']+=position;stats['logical_unsearched_connections']+=unsearched;stats['logical_failed_connections']+=1
    if f['status']=='RETAIN_RAW_BUDGET':assert f['raw']>budgets[cid]
    else:assert f['status']=='UNREACHABLE'
    failures.append({'net_id':net,'connections':len(order),'failed_connection_id':cid,'failure_status':f['status'],'logical_prefix_discarded':position,'unsearched':unsearched,'cached_proposal':x['proposal_cache_hit']})
    if not x['proposal_cache_hit']:reconstructed_paid_expansions+=position+1
   elif not x['proposal_cache_hit']:reconstructed_paid_expansions+=x['connections']
  assert len(seen)==55300 and sum(s['connections'] for s in group_stats.values())==115572;produced=next(r for r in prod['rows'] if r['case']==case);assert reconstructed_paid_expansions==produced['statistics']['new_expansions'];assert cache_hits==produced['statistics'].get('proposal_cache_hits',0) and cache_misses==produced['statistics']['proposal_cache_misses'];ledger=M/case/'unique_NET_occupancy.json';demand={int(n):v for n,v in json.loads(ledger.read_text()).items()};target=R/f'experiments/mmc_prospective_pressure_native_v2_2026-10-19/{case}/cold/physical_audit.json';truth={int(n):v for n,v in json.loads(target.read_text())['node_occupancy'].items()};allocated=defaultdict(Fraction);lower=defaultdict(Fraction);over=under=Fraction();pair_counts=Counter()
  for n,cap in channels.items():
   parts={g:c.get(n,0) for g,c in group_demand.items()};D=sum(parts.values());T=truth.get(n,0);assert D==demand.get(n,0);excess=max(D-T,0);over+=Fraction(excess,cap);under+=Fraction(max(T-D,0),cap)
   for group,count in parts.items():
    pair_counts[group]+=count;lower[group]+=Fraction(max(count-T,0),cap)
    if D:allocated[group]+=Fraction(count*excess,D*cap)
  assert sum(allocated.values())==over;metric=next(x for x in qdoc['cases'] if x['case']==case)['metrics']['static_criticality']['concrete'];assert (over+under)/len(channels)==Fraction(metric['mae']);report={g:{**dict(s),'positive_CHANNEL_NET_resource_pairs':pair_counts[g],'allocated_overprediction_error':str(allocated[g]),'fixed_group_alone_overprediction_lower_bound':str(lower[g])} for g,s in group_stats.items()};failure_file=O/f'{case}_failed_NETs.json';failure_file.write_text(json.dumps(failures,indent=2)+'\n');rows.append({'case':case,'groups':report,'normalized_overprediction_sum':str(over),'normalized_underprediction_sum':str(under),'concrete_MAE':str((over+under)/len(channels)),'reconstructed_paid_expansions':reconstructed_paid_expansions,'failures':str(failure_file)});print('FALLBACK_ERROR',case,{g:{k:v for k,v in s.items() if k in ['NETs','connections','logical_committed_prefix_connections_discarded','logical_unsearched_connections']} for g,s in report.items()},flush=True)
  for p in [ep,timing,events,selected,ledger,target,failure_file]:bindings[str(p)]=sha(p)
 (O/'review.json').write_text(json.dumps({'status':'ALL3_FALLBACK_CONNECTION_PREFIX_AND_CONSERVING_DEMAND_MAGNITUDE_ERROR_DIAGNOSIS_PRODUCED','rows':rows,'bindings':bindings,'independent_verification_pending':True,'scope':spec},indent=2)+'\n')
if __name__=='__main__':main()

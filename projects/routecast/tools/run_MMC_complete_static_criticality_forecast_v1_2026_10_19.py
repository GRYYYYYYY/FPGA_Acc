"""Complete input-only current3 static shared-tree forecasts with existing safety gates."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
import json,hashlib,time,resource,os
from MMC_zero_node_RC_shared_CSR_v1 import load
from load_initial_connection_criticalities_v3 import load as load_timing
from load_structural_node_base_v1 import load as load_base
from compiled_criticality_tree_v2 import Graph,FrozenPrices,BINARY
from criticality_objective_admission_v1 import prepare as admit
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def save(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
class Slots:
 def __init__(self,n):self.n=n
 def __contains__(self,e):return type(e) is int and 0<=e<self.n
 def __getitem__(self,e):
  if e not in self:raise KeyError(e)
  return e
class RC:
 def __init__(self,costs):self.costs=costs
 def initial(self,source):return 0
 def increment(self,slot):return self.costs[slot]
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0));O=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19';O.mkdir(exist_ok=False);save(O/'owner.json',{'pid':os.getpid(),'startticks':Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19]});cases=[f'episode_{i:02d}' for i in range(1,4)];inputs={case:R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json' for case in cases};metas={case:json.loads(ep.read_text()) for case,ep in inputs.items()};groups={};indices={};needed=defaultdict(list);bindings={str(p):sha(p) for p in inputs.values()};bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';bankproof=bank.parent/'independent_prediction_verification_v1.json';bp=json.loads(bankproof.read_text());assert bp['status']=='ALL3_COMPLETE_NET_ENSEMBLE_IDENTITY_XML_DAG_EXPECTATION_AND_LEDGER_AUDIT_PASS';assert sha(bank)==bp['bindings'][str(bank)];bindings[str(bank)]=sha(bank);bindings[str(bankproof)]=sha(bankproof)
 for case in cases:
  groups[case]=defaultdict(list)
  for q in metas[case]['connections']:groups[case][q['net_id']].append(q)
  assert len(groups[case])==55300 and len(metas[case]['connections'])==115572
  ix=bank.parent/case/'NET_contribution_indices.json';assert sha(ix)==bp['bindings'][str(ix)];indices[case]=dict(zip(sorted(groups[case]),json.loads(ix.read_text())));assert len(indices[case])==55300;bindings[str(ix)]=sha(ix)
  for net,index in indices[case].items():needed[index].append((case,net))
 graph=Path(metas[cases[0]]['inputs']['graph']['path']);assert all(m['graph_sha256']==sha(graph) for m in metas.values());bindings[str(graph)]=sha(graph)
 admissions=[R/'experiments/mmc_NET5_balanced_adapter_cost_review_v1_2026-10-19/research_decision_v1.json',R/'experiments/mmc_NET5_structural_criticality_applicability_closure_v1_2026-10-19/research_decision_v1.json',R/'experiments/mmc_current_initial_timing_admission_closure_v1_2026-10-19/research_decision_v1.json']
 for p in admissions:bindings[str(p)]=sha(p)
 for name in ['compiled_criticality_tree_v2.py','compiled_criticality_tree_v1.py','load_initial_connection_criticalities_v3.py','load_structural_node_base_v1.py','criticality_objective_admission_v1.py','criticality_net_admission_v1.py','criticality_net_occupancy_gate_v1.py','MMC_zero_node_RC_shared_CSR_v1.py','endpoint_bbox_demand_v1.py']:
  p=R/'tools'/name;bindings[str(p)]=sha(p)
 bindings[str(Path(__file__).resolve())]=sha(__file__);bindings[str(BINARY)]=sha(BINARY)
 protocol={'cases':cases,'required_connections_each':115572,'required_NETs_each':55300,'bindings':bindings.copy(),'policy':'One ascending input NETid pass. Complete deterministic original model minimum-parent tree as initial/fallback; same max(1ns,ceil1.5rawfloor) budgets. Existing descending exact initialized criticality/localpin/CID shared-tree attachment, fixed native node base only, no present/history/span. Whole-NET original physical/budget/singleparent, common objective nonincrease and full-ledger overuse nonincrease gates. Any failed primary or rejected gate preserves full old tree.','cache':'Proposal cache only, exact bank index and all CID/net/source/sink/criticality/localpin/budget fields; gate always rerun on current full ledger. Immutable native base/graph shared.','quality':'All3 cold-final resource258720 and spatial17160 universes, zeros and original normalization. Spearman and fixed-ID top5percent12936/resource, top20/spatial precision+recall; MAE reported. Necessary previous_native4metric screen unchanged; pass requires all4 nonregression and at least1 strict percase. Separate all4 comparison to existing NET_tree_ensemble. Existing endpoint_bbox_demand_v1 geometry baseline spatial only, same spatial metrics. Missing original raw_min_on stays unresolved and full original gate false until provided; raw_min_off/native_retained_off supplementary. Temporal pressure may be supplementary only, never replaces cold gate.','cost':'Record paid graph/base/immutable workspace/price packing, timing loader/integrity, bank floor materialization, search, gate, ledger reconstruction and outputs. Upstream bank production3424.3175s and fresh initialized timing startups are explicit preexisting dependencies, not free or claimed new full workflow speed.','scope':'All known exposed MMC layouts, existing algorithm reuse, no new native route/policy. No heldout/generalization, actual setup closure, global legal route, full workflow or hardware claim.','failure':'Stop on semantic/integrity failure and preserve it; do not stop/select cases for numerical quality. No reruns or parameter sweeps.'};save(O/'protocol.json',protocol);print('COMPLETE_FORECAST_FIXED3_REGISTERED',flush=True)
 tick=time.perf_counter();floors={}
 for line in bank.open():
  x=json.loads(line)
  if x['index'] not in needed:continue
  labels={int(n):tuple(d) for n,d in x['support_distance'].items()};parents={int(n):min(map(tuple,v)) for n,v in x['support_choices'].items()};paths={}
  for sink in x['sinks']:
   node=sink;edges=[];seen={node}
   while node!=x['source']:
    up,slot=parents[node];assert up not in seen and labels[up][1]+1==labels[node][1];seen.add(up);edges.append(slot);node=up
   paths[sink]=list(reversed(edges))
  floors[x['index']]={'net':x['net_id'],'source':x['source'],'paths':paths,'raw':{s:labels[s][0] for s in x['sinks']}}
 bank_seconds=time.perf_counter()-tick;assert set(floors)==set(needed);tick=time.perf_counter();offsets,dest,costs,caps,kinds,_=load(graph);graph_seconds=time.perf_counter()-tick;assert all(offsets[n]==offsets[n+1] for n,k in enumerate(kinds) if k=='SINK');assert all(kinds[n]!='SOURCE' and caps[n]>0 for n in dest);tick=time.perf_counter();base,bb=load_base(len(caps),10**18);base_seconds=time.perf_counter()-tick;bindings.update(bb);tick=time.perf_counter();g=Graph({'row_offsets':offsets,'dest_ranks':dest},costs,[0]*len(caps));workspace_seconds=time.perf_counter()-tick;tick=time.perf_counter();prices=FrozenPrices(base);pack_seconds=time.perf_counter()-tick;fields={'row_offsets':offsets,'dest_ranks':dest,'capacities':caps,'edge_ids':range(len(dest))};slots=Slots(len(dest));rc=RC(costs);cache={};rows=[]
 def owned(source,records):
  own={source};parent={}
  for r in records:
   u=source;seen={u};raw=0
   for slot in r['answer']['physical_edge_ids']:
    assert offsets[u]<=slot<offsets[u+1];v=dest[slot];assert v not in seen and caps[v]>0
    if v in parent:assert parent[v]==(u,slot)
    parent[v]=(u,slot);seen.add(v);own.add(v);u=v;raw+=costs[slot]
   assert u==r['sink'] and raw==r['answer']['delay']<=r['budget_integer']
  return own
 try:
  for case in cases:
   case_start=time.perf_counter();D=O/case;D.mkdir();tick=time.perf_counter();timing_dir=R/f'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/{case}';timing=load_timing(timing_dir);timing_seconds=time.perf_counter()-tick;bindings[str(timing_dir/'verification.json')]=sha(timing_dir/'verification.json');old_records={};old_owned={};ledger=Counter();tick=time.perf_counter()
   for net,qs in sorted(groups[case].items()):
    model=floors[indices[case][net]];assert model['net']==net and {q['source'] for q in qs}=={model['source']} and {q['sink'] for q in qs}==set(model['paths']);records=[]
    for q in sorted(qs,key=lambda q:q['connection_id']):
     raw=model['raw'][q['sink']];records.append(dict(q,answer={'status':'FOUND','physical_edge_ids':model['paths'][q['sink']],'delay':raw},floor_integer=raw,budget_integer=max(10**9,(3*raw+1)//2)))
    old_records[net]=records;old_owned[net]=owned(model['source'],records);ledger.update(old_owned[net])
   initial_overflow=sum(max(0,c-caps[n]) for n,c in ledger.items());initial_seconds=time.perf_counter()-tick;stats=Counter();search_seconds=gate_seconds=0;completed=0;chosen_owned={};path_file=D/'records.jsonl';event_file=D/'events.jsonl';new_native_before=list(g.total_stats)
   with path_file.open('x') as out,event_file.open('x') as events:
    for ordinal,(net,qs) in enumerate(sorted(groups[case].items()),1):
     previous=old_records[net];ordered=[]
     for q in qs:
      c=timing[q['connection_id']];assert (c['net'],c['source_rr'],c['target_rr'])==(q['net_id'],q['source'],q['sink']);value=Fraction(c['criticality_numerator'],c['criticality_denominator']);ordered.append((-value,c['local_sink_pin'],q['connection_id'],q,value))
     ordered.sort();budget_byid={r['connection_id']:r['budget_integer'] for r in previous};key=(indices[case][net],tuple((cid,q['net_id'],q['source'],q['sink'],c.numerator,c.denominator,pin,budget_byid[cid]) for _,pin,cid,q,c in ordered));cached=key in cache
     if cached:primary=cache[key];stats['proposal_cache_hits']+=1
     else:
      tick=time.perf_counter();tree=g.tree(qs[0]['source']);paths={};failure=None
      for _,pin,cid,q,c in ordered:
       r=tree.expand(q['sink'],c,prices,budget_byid[cid]);stats['new_expansions']+=1
       if not r['committed']:failure={'connection_id':cid,'status':r['status'],'raw':r.get('raw')};break
       paths[cid]={'status':'FOUND','physical_edge_ids':list(r['path_slots']),'delay':r['raw']}
      search_seconds+=time.perf_counter()-tick;primary={'complete':failure is None,'paths':paths if failure is None else None,'failure':failure};cache[key]=primary;stats['proposal_cache_misses']+=1
     decision='RETAIN_PRIMARY_FAILURE';plan=None;selected=previous
     if primary['complete']:
      candidate=[dict(r,answer=primary['paths'][r['connection_id']]) for r in previous];tick=time.perf_counter();plan=admit(fields,rc,slots,qs,previous,candidate,ledger,timing,prices);gate_seconds+=time.perf_counter()-tick;decision=plan['status']
      if plan['accepted']:
       selected=candidate
       for node,count in plan['updates'].items():
        if count:ledger[node]=count
        else:ledger.pop(node,None)
     union=owned(qs[0]['source'],selected);chosen_owned[net]=union;stats[decision]+=1;completed+=len(selected)
     for r in selected:out.write(json.dumps(r,separators=(',',':'))+'\n')
     event={'net_id':net,'connections':len(qs),'proposal_cache_hit':cached,'primary_complete':primary['complete'],'primary_failure':primary['failure'],'decision':decision,'chosen_owned':sorted(union)}
     if plan is not None:event.update(old_score=str(plan['old_score']),candidate_score=str(plan['candidate_score']),objective_delta=str(plan['objective_delta']),prospective_overflow_delta=plan['prospective_overflow_delta'])
     events.write(json.dumps(event,separators=(',',':'))+'\n')
     if ordinal%1000==0:
      progress={'case':case,'NETs':ordinal,'required_NETs':55300,'completed_connections':completed,'statistics':dict(stats),'elapsed_case_seconds':time.perf_counter()-case_start};temp=O/'progress.tmp';save(temp,progress);os.replace(temp,O/'progress.json');print('COMPLETE_FORECAST',case,ordinal,'cache',stats['proposal_cache_hits'],'seconds',round(progress['elapsed_case_seconds'],2),flush=True)
   assert completed==115572 and len(chosen_owned)==55300;tick=time.perf_counter();fresh=Counter(n for nodes in chosen_owned.values() for n in nodes);assert fresh==ledger;overflow=sum(max(0,c-caps[n]) for n,c in ledger.items());assert overflow<=initial_overflow;ledger_seconds=time.perf_counter()-tick;ledger_file=D/'unique_NET_occupancy.json';save(ledger_file,{str(n):v for n,v in sorted(ledger.items())});stats_native=[x-y for x,y in zip(g.total_stats,new_native_before)];row={'case':case,'connections':completed,'NETs':55300,'statistics':dict(stats),'initial_overflow':initial_overflow,'final_overflow':overflow,'timing_load_seconds':timing_seconds,'initial_floor_records_and_ledger_seconds':initial_seconds,'new_search_seconds':search_seconds,'full_NET_gate_seconds':gate_seconds,'independent_internal_ledger_rebuild_seconds':ledger_seconds,'native_stats':stats_native,'case_component_seconds':time.perf_counter()-case_start};rows.append(row);save(D/'receipt.json',row)
   for p in [path_file,event_file,ledger_file,D/'receipt.json']:bindings[str(p)]=sha(p)
   save(O/'cases_progress.json',{'rows':rows});print('COMPLETE_FORECAST_CASE_DONE',case,row['case_component_seconds'],flush=True)
 finally:g.close()
 for p,h in protocol['bindings'].items():assert sha(p)==h,p
 bindings[str(O/'protocol.json')]=sha(O/'protocol.json');save(O/'receipt.json',{'status':'ALL3_COMPLETE_STATIC_CRITICALITY_FORECASTS_PRODUCED_INDEPENDENT_XML_EVENT_AND_QUALITY_PENDING','rows':rows,'shared_costs_seconds':{'bank_floor_materialization':bank_seconds,'graph_load':graph_seconds,'base_load':base_seconds,'compiled_workspace':workspace_seconds,'immutable_price_pack':pack_seconds},'total_paid_cached_input_seconds_before_receipt':time.perf_counter()-begin,'unique_proposals':len(cache),'peak_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'bindings':bindings,'scope':protocol['scope']});print('COMPLETE_FORECAST_ALL3_DONE',flush=True)
if __name__=='__main__':main()

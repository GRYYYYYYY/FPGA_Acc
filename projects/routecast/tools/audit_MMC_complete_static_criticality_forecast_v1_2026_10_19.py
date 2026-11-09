"""Original XML selected paths and accepted whole-NET updates; no producer gate calls."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from array import array
import json,hashlib,struct,xml.parsers.expat as expat,resource,time
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));M=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19';receipt=M/'receipt.json';prod=json.loads(receipt.read_text());assert prod['status']=='ALL3_COMPLETE_STATIC_CRITICALITY_FORECASTS_PRODUCED_INDEPENDENT_XML_EVENT_AND_QUALITY_PENDING';O=R/'experiments/mmc_complete_static_criticality_audit_v1_2026-10-19';O.mkdir(exist_ok=False);protocol=json.loads((M/'protocol.json').read_text());bindings={str(p):sha(p) for p in [receipt,M/'protocol.json',Path(__file__).resolve()]}
 for p,h in prod['bindings'].items():assert sha(p)==h,p
 cases=protocol['cases'];metas={};groups={};bycase={};needed=defaultdict(list);edge_ids=set();index_maps={}
 for case in cases:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());metas[case]=meta;groups[case]=defaultdict(list)
  for q in meta['connections']:groups[case][q['net_id']].append(q)
  ix=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/NET_contribution_indices.json';indices=json.loads(ix.read_text());assert len(indices)==len(groups[case])==55300;index_maps[case]=dict(zip(sorted(groups[case]),indices))
  for net,index in index_maps[case].items():needed[index].append((case,net))
  path=M/case/'records.jsonl';count=0
  for line in path.open():
   r=json.loads(line);edge_ids.update(r['answer']['physical_edge_ids']);count+=1
  assert count==115572
  for p in [ep,ix,path]:bindings[str(p)]=sha(p)
 bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';assert sha(bank)==prod['bindings'][str(bank)];floors={}
 for line in bank.open():
  x=json.loads(line)
  if x['index'] not in needed:continue
  parent={int(n):sorted(values)[0] for n,values in x['support_choices'].items()};paths={};raw={}
  for sink in x['sinks']:
   current=sink;path=[];seen={current}
   while current!=x['source']:
    up,slot=parent[current];assert up not in seen;seen.add(up);path.append(slot);current=up
   paths[sink]=list(reversed(path));raw[sink]=x['support_distance'][str(sink)][0];edge_ids.update(path)
  floors[x['index']]={'source':x['source'],'net':x['net_id'],'paths':paths,'raw':raw}
 assert set(floors)==set(needed);graph=Path(metas[cases[0]]['inputs']['graph']['path']);assert sha(graph)==metas[cases[0]]['graph_sha256'];caps=array('I');types=[];arcs={};switches={};stack=[];edge=0;switch=None
 def start(tag,a):
  nonlocal edge,switch
  parent=stack[-1] if stack else None
  if tag=='switch' and parent=='switches':switch=int(a['id'])
  elif tag=='timing' and parent=='switch':
   value=Fraction(a.get('Tdel','0'))*10**18;assert value.denominator==1 and value>=0;switches[switch]=int(value)
  elif tag=='node' and parent=='rr_nodes':assert int(a['id'])==len(caps);caps.append(int(a['capacity']));types.append(a['type'])
  elif tag=='timing' and parent=='node':assert Fraction(a.get('R','0'))==Fraction(a.get('C','0'))==0
  elif tag=='edge' and parent=='rr_edges':
   if edge in edge_ids:arcs[edge]=(int(a['src_node']),int(a['sink_node']),switches[int(a['switch_id'])])
   edge+=1
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end;tick=time.perf_counter()
 with graph.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):parser.Parse(chunk,False)
 parser.Parse(b'',True);xml_seconds=time.perf_counter()-tick;assert edge==8097539 and len(caps)==904438 and set(arcs)==edge_ids
 base_path=R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10/node_base.u64';base_proof=base_path.parent/'verification.json';base_info=json.loads(base_proof.read_text());assert sha(base_path)==base_info['bindings'][str(base_path)] and base_info['scale']==10**18;base=array('Q');base.frombytes(base_path.read_bytes());assert base.itemsize==8 and len(base)==len(caps)
 def audit_records(qs,records):
  queries={q['connection_id']:q for q in qs};assert len(queries)==len(qs)==len(records);seen=set();parents={};union={qs[0]['source']};destinations={};delays={};paths={}
  for r in records:
   cid=r['connection_id'];assert cid in queries and cid not in seen;seen.add(cid);q=queries[cid];assert all(r[k]==v for k,v in q.items());assert r['answer']['status']=='FOUND';u=q['source'];assert types[u]=='SOURCE' and caps[u]>0;local={u};raw=0;used=[]
   for slot in r['answer']['physical_edge_ids']:
    assert type(slot) is int and slot in arcs;a,b,cost=arcs[slot];assert a==u and b not in local and caps[b]>0
    if b in parents:assert parents[b]==(u,slot)
    parents[b]=(u,slot);local.add(b);union.add(b);raw+=cost;u=b;used.append(b)
   assert u==q['sink'] and types[u]=='SINK' and raw==r['answer']['delay'] and r['floor_integer']<=raw<=r['budget_integer'];assert r['budget_integer']==max(10**9,(3*r['floor_integer']+1)//2);destinations[cid]=used;delays[cid]=raw;paths[cid]=r['answer']['physical_edge_ids']
  assert seen==set(queries);return union,destinations,delays,paths
 def score(users,delays,criticality):
  total=sum((criticality[cid]*raw for cid,raw in delays.items()),Fraction());maximum={}
  for cid,nodes in users.items():
   for n in nodes:maximum[n]=max(maximum.get(n,Fraction()),criticality[cid])
  return total+sum(((1-c)*base[n] for n,c in maximum.items()),Fraction())
 rows=[]
 for case in cases:
  case_begin=time.perf_counter();old_records={};old_audits={};ledger=Counter();actual=defaultdict(list);seen_cids=set();timing_root=R/f'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/{case}';timing_file=timing_root/'initial_connection_criticalities.json';timing_proof=json.loads((timing_root/'verification.json').read_text());assert sha(timing_file)==timing_proof['bindings'][str(timing_file)];criticality={}
  for x in json.loads(timing_file.read_text()):
   value=struct.unpack('<f',struct.pack('<f',float(x['criticality_float32_text'])))[0];criticality[x['connection_id']]=Fraction(*value.as_integer_ratio())
  for net,qs in sorted(groups[case].items()):
   model=floors[index_maps[case][net]];assert model['net']==net and {q['source'] for q in qs}=={model['source']} and {q['sink'] for q in qs}==set(model['paths']);records=[]
   for q in qs:
    raw=model['raw'][q['sink']];records.append(dict(q,answer={'status':'FOUND','physical_edge_ids':model['paths'][q['sink']],'delay':raw},floor_integer=raw,budget_integer=max(10**9,(3*raw+1)//2)))
   old_records[net]=records;old_audits[net]=audit_records(qs,records);ledger.update(old_audits[net][0])
  initial_overflow=sum(max(0,c-caps[n]) for n,c in ledger.items())
  for line in (M/case/'records.jsonl').open():
   r=json.loads(line);assert r['connection_id'] not in seen_cids;seen_cids.add(r['connection_id']);actual[r['net_id']].append(r);model=floors[index_maps[case][r['net_id']]];assert r['floor_integer']==model['raw'][r['sink']]
  assert len(actual)==55300 and seen_cids==set(range(115572));selected_audits={net:audit_records(groups[case][net],records) for net,records in actual.items()};events=[];decisions=Counter();candidate_rejections_not_physical_replayed=0
  for line in (M/case/'events.jsonl').open():
   event=json.loads(line);net=event['net_id'];assert net in groups[case] and (not events or net>events[-1]);events.append(net);assert event['connections']==len(actual[net]);before=old_audits[net];after=selected_audits[net];assert event['chosen_owned']==sorted(after[0]);old_score=score(before[1],before[2],criticality);chosen_score=score(after[1],after[2],criticality);decisions[event['decision']]+=1
   if event['decision']=='COMMITTED':
    delta=0
    for n in before[0]|after[0]:
     count=ledger.get(n,0);new=count-int(n in before[0])+int(n in after[0]);assert new>=0;delta+=max(0,new-caps[n])-max(0,count-caps[n])
     if new:ledger[n]=new
     else:ledger.pop(n,None)
    assert delta==event['prospective_overflow_delta']<=0;assert Fraction(event['old_score'])==old_score and Fraction(event['candidate_score'])==chosen_score and Fraction(event['objective_delta'])==chosen_score-old_score<=0
   else:
    assert before[3]==after[3] and before[0]==after[0]
    if event['primary_complete']:
     candidate_rejections_not_physical_replayed+=1;assert Fraction(event['old_score'])==old_score;assert Fraction(event['candidate_score'])-old_score==Fraction(event['objective_delta'])
     if event['decision']=='RETAIN_OBJECTIVE_INCREASE':assert Fraction(event['objective_delta'])>0
     else:assert event['decision']=='RETAIN_OVERFLOW_INCREASE' and event['prospective_overflow_delta']>0
    else:assert event['decision']=='RETAIN_PRIMARY_FAILURE' and event['primary_failure'] is not None
  assert events==sorted(groups[case]);fresh=Counter(n for v in selected_audits.values() for n in v[0]);assert ledger==fresh;published={int(n):v for n,v in json.loads((M/case/'unique_NET_occupancy.json').read_text()).items()};assert dict(fresh)==published;overflow=sum(max(0,c-caps[n]) for n,c in fresh.items());row=next(r for r in prod['rows'] if r['case']==case);assert overflow==row['final_overflow']<=initial_overflow==row['initial_overflow'];assert all(row['statistics'][k]==v for k,v in decisions.items());rows.append({'case':case,'connections':115572,'NETs':55300,'accepted_and_retained_state_events':len(events),'decisions':dict(decisions),'initial_overflow':initial_overflow,'final_overflow':overflow,'counterfactual_rejected_candidates_not_physically_replayed':candidate_rejections_not_physical_replayed,'case_audit_seconds':time.perf_counter()-case_begin});print('COMPLETE_FORECAST_XML_AUDIT_PASS',case,flush=True)
  for p in [M/case/'records.jsonl',M/case/'events.jsonl',M/case/'unique_NET_occupancy.json',timing_file,timing_root/'verification.json']:bindings[str(p)]=sha(p)
 for p in [graph,bank,base_path,base_proof]:bindings[str(p)]=sha(p)
 (O/'verification.json').write_text(json.dumps({'status':'ALL3_COMPLETE_SELECTED_PATHS_XML_BUDGETS_SINGLEPARENT_LEDGER_AND_ACCEPTED_GATE_REPLAY_PASS','rows':rows,'xml_seconds':xml_seconds,'total_before_receipt_seconds':time.perf_counter()-begin,'bindings':bindings,'scope':'Independent all selected paths and all accepted common-score/occupancy updates; retained state checked against full input-only fallback. Rejected candidate paths not emitted by producer, so their physical/search optimality and counterfactual scores are not independently certified. No legal global route, native STA or prediction quality/gain claim.'},indent=2)+'\n');print('ALL3_COMPLETE_FORECAST_XML_AUDIT_PASS',flush=True)
if __name__=='__main__':main()

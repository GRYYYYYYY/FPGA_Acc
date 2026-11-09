"""Rebuild class demands from selected edge paths, histogram errors and unsigned-float ranks."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from array import array
import json,hashlib,struct,xml.parsers.expat as expat
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_complete_forecast_fallback_error_diagnosis_v1_2026-10-19';review=O/'review.json';d=json.loads(review.read_text());assert not (O/'independent_verification_v1.json').exists()
 for p,h in d['bindings'].items():assert sha(p)==h
 graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');channels=array('B');destination=array('I');stack=[]
 def start(tag,a):
  parent=stack[-1] if stack else None
  if tag=='node' and parent=='rr_nodes':assert int(a['id'])==len(caps);cap=int(a['capacity']);caps.append(cap);channels.append(int(cap>0 and a['type'] in ['CHANX','CHANY']))
  elif tag=='edge' and parent=='rr_edges':destination.append(int(a['sink_node']))
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):parser.Parse(chunk,False)
 parser.Parse(b'',True);assert len(caps)==904438 and len(destination)==8097539 and sum(channels)==258720;M=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19';bindings={str(p):sha(p) for p in [review,graph,Path(__file__).resolve()]};checks=[]
 for row in d['rows']:
  case=row['case'];eventfile=M/case/'events.jsonl';events={x['net_id']:x for x in map(json.loads,eventfile.read_text().splitlines())};recordfile=M/case/'records.jsonl';nets=defaultdict(set);queries=defaultdict(list);budgets={};seen=set()
  for r in map(json.loads,recordfile.read_text().splitlines()):
   cid=r['connection_id'];assert cid not in seen;seen.add(cid);net=r['net_id'];nets[net].update([r['source'],*[destination[e] for e in r['answer']['physical_edge_ids']]]);queries[net].append(cid);budgets[cid]=r['budget_integer']
  assert len(nets)==len(events)==55300 and seen==set(range(115572));groups=sorted(row['groups']);demand={g:Counter() for g in groups};statistics={g:Counter() for g in groups};timing=R/f'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/{case}/initial_connection_criticalities.json';c={x['connection_id']:x for x in json.loads(timing.read_text())};paid_calls=0
  for net,nodes in nets.items():
   event=events[net];g=event['decision'];s=statistics[g];s['NETs']+=1;s['connections']+=len(queries[net]);demand[g].update(n for n in nodes if channels[n]);assert len(queries[net])==event['connections']
   if not event['primary_complete']:
    f=event['primary_failure'];cid=f['connection_id'];failbits=struct.unpack('<I',struct.pack('<f',float(c[cid]['criticality_float32_text'])))[0];failtie=c[cid]['local_sink_pin'],cid;prefix=0
    for other in queries[net]:
     bits=struct.unpack('<I',struct.pack('<f',float(c[other]['criticality_float32_text'])))[0];assert 0<=float(c[other]['criticality_float32_text'])<=1
     if bits>failbits or bits==failbits and (c[other]['local_sink_pin'],other)<failtie:prefix+=1
    s['logical_committed_prefix_connections_discarded']+=prefix;s['logical_unsearched_connections']+=len(queries[net])-prefix-1;s['logical_failed_connections']+=1
    if not event['proposal_cache_hit']:paid_calls+=prefix+1
    if f['status']=='RETAIN_RAW_BUDGET':assert f['raw']>budgets[cid]
   elif not event['proposal_cache_hit']:paid_calls+=len(queries[net])
  target=R/f'experiments/mmc_prospective_pressure_native_v2_2026-10-19/{case}/cold/physical_audit.json';truth={int(n):v for n,v in json.loads(target.read_text())['node_occupancy'].items()};hist=Counter()
  for n,flag in enumerate(channels):
   if flag:hist[caps[n],truth.get(n,0),tuple(demand[g].get(n,0) for g in groups)]+=1
  over=under=Fraction();allocated={g:Fraction() for g in groups};lower={g:Fraction() for g in groups}
  for (cap,T,values),frequency in hist.items():
   D=sum(values);excess=max(D-T,0);over+=frequency*Fraction(excess,cap);under+=frequency*Fraction(max(T-D,0),cap)
   for g,value in zip(groups,values):
    lower[g]+=frequency*Fraction(max(value-T,0),cap)
    if D:allocated[g]+=frequency*Fraction(value*excess,D*cap)
  assert Fraction(row['normalized_overprediction_sum'])==over and Fraction(row['normalized_underprediction_sum'])==under and Fraction(row['concrete_MAE'])==(over+under)/258720 and sum(allocated.values())==over;assert paid_calls==row['reconstructed_paid_expansions']
  for g in groups:
   r=row['groups'][g]
   for k,value in statistics[g].items():assert value==r[k]
   assert sum(demand[g].values())==r['positive_CHANNEL_NET_resource_pairs'];assert allocated[g]==Fraction(r['allocated_overprediction_error']);assert lower[g]==Fraction(r['fixed_group_alone_overprediction_lower_bound'])
  checks.append({'case':case,'NETs':55300,'connections':115572,'all_class_demands_from_edge_destination_unions_verified':True,'histogram_error_allocation_and_bounds_exact':True,'first_failure_priority_boundary_verified_by_float32_integer_bits':True});print('FALLBACK_ERROR_INDEPENDENT_PASS',case,flush=True)
  for p in [eventfile,recordfile,timing,target]:bindings[str(p)]=sha(p)
 (O/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL3_FALLBACK_COVERAGE_PREFIX_CLASS_DEMAND_ERROR_HISTOGRAMS_INDEPENDENTLY_VERIFIED','rows':checks,'bindings':bindings,'scope':'Per-class magnitude accounting and logical expansion-call counts, not node-search expansions or original discarded path certification. Proportional allocation and fixed-group lower bounds are descriptive; no additive rank/topK causal attribution.'},indent=2)+'\n')
if __name__=='__main__':main()

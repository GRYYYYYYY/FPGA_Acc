"""Finite wholeNET candidate bin intervals and rigorous optimistic topK exclusion."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from spatial_candidate_rank_bounds_v1 import rank_bounds
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_spatial_rank_bounds_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_map_candidate_coverage_v1_2026-10-20/verification.json';contract=E/'spatial_candidate_rank_bounds_contract_v1_2026-10-20/verification.json';assert all(sha(p)==h for p,h in read(contract)['bindings'].items());files=[Path(__file__),source,contract,E/'wbuart_prior_uncertainty_review_v1_2026-10-20/verification.json'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL72_RECORDED_POOL_SPATIAL_RANK_INTERVAL_DIAGNOSTIC','bound':'Sum perNET min/max contribution to each fixed spatial bin, divide by original positive bin capacity. If at leastK other bin lower bounds outrank a target bin upper bound under original fixed-key ties, that target cannot be topK under any selection or convex mixture of recorded wholeNET candidates.','scope':'Exposed-family retrospective diagnostic only. Interval-possible is not proof of joint feasibility; no new model/paths/label-directed weights, K/ties/domains/gates unchanged. Candidate pool missing unrecorded partial/fallback alternatives.','bindings':bindings},indent=2)+'\n');rows=[];graphs={};workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')
 for row in read(source)['rows']:
  out=Path(row['output']);ep=read(row['endpoint']);graph=ep['inputs']['graph']['path']
  if graph not in graphs:graphs[graph]=[int(e.get('sink_node')) for _,e in ET.iterparse(graph) if e.tag=='edge']
  dest=graphs[graph];resources=[json.loads(x) for x in Path(row['resources']).read_text().splitlines()];bins=read(Path(row['resources']).parent/'spatial_bins.json');keys=[tuple(b['key']) for b in bins];assert keys==sorted(keys);index={k:i for i,k in enumerate(keys)};caps=[b['capacity'] for b in bins];nodebins={r['id']:[index[tuple(k)] for k in r['bins']] for r in resources};pool=defaultdict(set);initial=defaultdict(list);final=defaultdict(list)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for q in read(out/'round1.json')['records']:final[q['net_id']].append(q)
  def support(rs):return frozenset(dest[e] for q in rs for e in q['answer']['physical_edge_ids'] if dest[e] in nodebins)
  for n,rs in initial.items():pool[n].add(support(rs))
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:pool[event['net_id']].add(support(rs))
  previous={x['net_id']:x for x in read(row['payload'])};lower=[0]*len(bins);upper=[0]*len(bins)
  def project(s):return Counter(i for n in s for i in nodebins[n])
  for net,choices in pool.items():
   assert len(choices)==previous[net]['unique_CHANNEL_supports'];vectors=[project(s) for s in choices];domain=set().union(*(set(v) for v in vectors))
   for i in domain:lower[i]+=min(v.get(i,0) for v in vectors);upper[i]+=max(v.get(i,0) for v in vectors)
  values=[0]*len(bins)
  for rs in final.values():
   for i,count in project(support(rs)).items():values[i]+=count
  assert all(a<=v<=b for a,v,b in zip(lower,values,upper));spec=read(next(c['specification'] for c in workflow['comparisons'] if c['case']==row['case']));truth=read(spec['label_physical_audit']);truthvalues=[0]*len(bins)
  for n,count in truth['node_occupancy'].items():
   for i in nodebins.get(int(n),[]):truthvalues[i]+=count
  domain=read(spec['domain_proof']);k=domain['spatial_k'];target=sorted(range(len(bins)),key=lambda i:(-F(truthvalues[i],caps[i]),keys[i]))[:k];selected=sorted(range(len(bins)),key=lambda i:(-F(values[i],caps[i]),keys[i]))[:k];b=rank_bounds(lower,upper,caps,k);excluded=[i for i in target if b[i]['excluded_from_topK']];guaranteed=[i for i in target if b[i]['guaranteed_in_topK']];hits=len(set(target)&set(selected));assert hits<=k-len(excluded)
  d=D/row['case']/row['initializer']/row['timing_policy']/row['priority'];d.mkdir(parents=True);p=d/'bounds.json';p.write_text(json.dumps({'keys':[list(k) for k in keys],'capacity':caps,'lower':lower,'upper':upper,'final':values,'truth':truthvalues,'truth_topK':target,'final_topK':selected,'rank_bounds':b},separators=(',',':'))+'\n');summary={k:row[k] for k in ['case','initializer','timing_policy','priority','output','endpoint','resources','target_route']};summary.update(payload=str(p),k=k,bins=len(bins),actual_hits=hits,optimistic_hits_upper_bound=k-len(excluded),truth_bins_excluded_even_by_intervals=excluded,truth_bins_guaranteed_by_intervals=guaranteed);rows.append(summary);bindings[str(p)]=sha(p);print(row['case'],row['initializer'],row['timing_policy'],row['priority'],hits,k-len(excluded),flush=True)
 assert len(rows)==72
 (D/'verification.json').write_text(json.dumps({'status':'ALL72_CANDIDATE_BIN_INTERVALS_AND_DETERMINISTIC_RANK_BOUNDS_COMPUTED','rows':rows,'bindings':bindings,'independent_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()

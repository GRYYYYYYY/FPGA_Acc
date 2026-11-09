"""Fixed warm-state target-tree scores, no candidate generation or publication."""
import json,hashlib,sys
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from audit_structural_node_base_v1 import audit as audit_base
E=R/'experiments';D=E/'wbuart_native_warm_snapshot_rescore_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);C=E/'wbuart_candidate_coverage_strata_v1_2026-10-20';FCAST=E/'wbuart_forecasts_v1_2026-10-20/verification.json';B=E/'wbuart_native_target_budget_diagnosis_v1_2026-10-20';files=[Path(__file__),C/'verification.json',C/'independent_verification_v1.json',FCAST,B/'verification.json',B/'independent_verification_v1.json'];bindings={str(p):sha(p) for p in files};rows=[]
 for arm in read(C/'verification.json')['rows']:
  if arm['initializer']!='native_retained' or arm['timing_policy']!='warm_timing_round_updated':continue
  spec=next(r for r in read(B/'verification.json')['rows'] if r['case']==arm['case']);ep=Path(spec['endpoint']);meta=read(ep);graph,digest,nodes,fields,rc,queries=load_endpoints(ep);nativepaths,native,ledger=load_complete(Path(spec['native_route']),meta,nodes,fields,rc);warmfile=Path(spec['warm_directory'])/'initial.json';warm=read(warmfile);warmledger={int(n):x for n,x in warm['ledger'].items()};old={q['connection_id']:q for q in warm['records']};target={q['connection_id']:dict(old[q['connection_id']],answer={'status':'FOUND','physical_edge_ids':q['physical_edge_ids'],'delay':q['delay_integer']}) for q in native};width=arm['case'].split('/')[0];baseproof=E/'wbuart_node_bases_v1_2026-10-20'/width/'verification.json';base=audit_base(graph,baseproof,rc.scale);timingout=Path(next(a['output'] for r in read(FCAST)['rows'] if r['case']==arm['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated'));timingfile=timingout/'timing_round0.json';cr={q['connection_id']:F(q['criticality_numerator'],q['criticality_denominator']) for q in read(timingfile)['criticalities']};slots={eid:i for i,eid in enumerate(fields['edge_ids'])};caps=fields['capacities'];span={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in ['CHANX','CHANY']};groups=defaultdict(list)
  for q in queries:groups[q['net_id']].append(q['connection_id'])
  strata={q['net_id']:q for q in read(arm['payload'])};payload=[]
  def support(records):return {q['source'] for q in records}|{fields['dest_ranks'][slots[e]] for q in records for e in q['answer']['physical_edge_ids']}
  for net,cids in sorted(groups.items()):
   before=[old[cid] for cid in cids];after=[target[cid] for cid in cids];owned=support(before);newowned=support(after)
   def cost(n):return base[n]*(1+max(0,warmledger.get(n,0)-int(n in owned)-caps[n]+1))+(rc.scale//(20*10**9))*span.get(n,0)
   def score(records):
    users={};raw=F(0)
    for q in records:
     c=cr[q['connection_id']];raw+=c*q['answer']['delay']
     for e in q['answer']['physical_edge_ids']:
      n=fields['dest_ranks'][slots[e]];users[n]=max(users.get(n,F(0)),c)
    return raw+sum((1-c)*cost(n) for n,c in users.items())
   a,b=score(before),score(after);delta=b-a;pressure=sum(max(0,warmledger.get(n,0)+int(n in newowned)-int(n in owned)-caps[n])-max(0,warmledger.get(n,0)-caps[n]) for n in owned^newowned);bad=[cid for cid in cids if target[cid]['answer']['delay']>old[cid]['budget_integer']];status='BUDGET_INCOMPATIBLE' if bad else 'OBJECTIVE_AND_OVERFLOW_INCREASE' if delta>0 and pressure>0 else 'OBJECTIVE_INCREASE' if delta>0 else 'OVERFLOW_INCREASE' if pressure>0 else 'REFERENCE_ADMISSIBLE';payload.append({'net_id':net,'status':status,'budget_violating_CIDs':bad,'old_score':str(a),'native_target_score':str(b),'objective_delta':str(delta),'overflow_delta':pressure,'coverage':strata[net]['coverage'],'native_records':after})
  first=read(timingout/'receipt.json')['rounds'][0]['events'][0];anchor=next(q for q in payload if q['net_id']==first['net_id']);assert F(first['objective_guard']['old_score'])==F(anchor['old_score']);d=D/arm['case'];d.mkdir(parents=True);p=d/'NETs.json';p.write_text(json.dumps(payload)+'\n');summary=defaultdict(int);missing=defaultdict(int)
  for q in payload:summary[q['status']]+=1;missing[q['status']]+=q['coverage']=='target_support_missing'
  rows.append({'case':arm['case'],'payload':str(p),'endpoint':str(ep),'warm_frame':str(warmfile),'timing_frame':str(timingfile),'base_proof':str(baseproof),'all_NET_status_counts':dict(summary),'missing_target_support_status_counts':dict(missing)});print(arm['case'],dict(missing),flush=True)
  for p in [ep,warmfile,timingfile,baseproof,p,Path(spec['native_route'])]:bindings[str(p)]=sha(p)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9666_NATIVE_TARGET_NETS_SCORED_AT_FIXED_WARM_SNAPSHOT','rows':rows,'bindings':bindings,'scope':'Every NET evaluated independently against same warm ledger/round0 criticality/zero accumulated history/static span prices and old-owner exclusion. Not serial native/model trajectory, search optimality, global joint feasibility or label-directed deployment. Budget-incompatible NETs retained as category; no guards/labels changed. Separate implementation validation pending.'},indent=2)+'\n')
if __name__=='__main__':main()

"""Frozen coherent-ready-owner forecast versus current-live persistence on actual queries."""
import json,re
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from verify_prince_ownership_ledger_v2 import owner_payload
from audit_native_route import NODE
R=Path(__file__).resolve().parents[1];E=R/'experiments';L=E/'prince_ownership_ledger_trial_v2_2026-10-20';Q=E/'prince_connection_query_trial_v1_2026-10-20';D=E/'prince_ready_owner_forecast_v1_2026-10-20'
def final_owners(path):
 owners={};current=None;pattern=re.compile(r'^Net (\d+) \((.*)\)(: global net connecting:)?\s*$')
 for line in path.read_text().splitlines():
  match=pattern.fullmatch(line)
  if match:current=int(match[1]);owners[current]=set()
  node=NODE.match(line)
  if node and node[2] in ['CHANX','CHANY']:owners[current].add(int(node[1]))
 return owners
def rational(x):return [x.numerator,x.denominator]
def main():
 assert not D.exists();D.mkdir();design=E/'prince_present_identity_trial_v1_2026-10-20/ready_owner_forecast_screen_design_v1.json';join=E/'prince_query_ledger_join_v1_2026-10-20/verification.json';ledger=L/'ledger_verification_v1.json';proof=json.loads(join.read_text());lp=json.loads(ledger.read_text());bindings={str(p):sha(p) for p in [design,join,ledger,Path(__file__)]};policy=dict(design=str(design),equal_pair_aggregation='For each NET/node, arithmetic mean of baseline predictions over distinct saved query-state groups, without call multiplicity; then absolute error. Candidate prediction constant per NET/node. Give each NET/node equal weight.',metrics='Exact rational pair error and exact integer call-weighted error. All9 cases retained; no pooling to override per-case results.',development_exposed=True,bindings=dict(bindings));(D/'protocol.json').write_text(json.dumps(policy,indent=2)+'\n');inputs=[]
 # Freeze EVERY input prediction before reading final route labels.
 for case in sorted(x['case'] for x in proof['rows']):
  d=L/case/'capture';ready=d/'callback.tsv.ready.tsv';events=[int(x.split()[0]) for x in ready.read_text().splitlines() if int(x.split()[4])];assert len(events)<=1;bindings[str(ready)]=sha(ready)
  if not events:inputs.append(dict(case=case,available=False,reason='No frozen ready event; width96 legal final label unavailable'));continue
  i=events[0];op=d/'owners'/f'owners_{i}.bin';_,owners=owner_payload(op);counts=Counter(n for group in owners.values() for n in group);rawp=Q/case/'capture/queries.tsv';assert sha(rawp)==proof['bindings'][str(rawp)];bindings[str(rawp)]=sha(rawp);assert sha(op)==lp['bindings'][str(op)];bindings[str(op)]=sha(op);target=i+1;out=D/(case.replace('/','_')+'.inputs.jsonl');groups=calls=0
  with out.open('x') as f:
   for line in rawp.open():
    if int(line.split('\t',1)[0])!=target:continue
    it,encoded,node,kind,occ,cap,pres,acc,base,cost,nc,active,ident,pin,sink,own,count=map(int,line.split())
    if kind not in [4,5]:continue
    net=encoded-1;forecast=counts[node]-int(node in owners[net]);baseline=occ-own;assert cap==1 and min(forecast,baseline)>=0;f.write(json.dumps([net,node,ident,forecast,baseline,count],separators=(',',':'))+'\n');groups+=1;calls+=count
  assert groups>0;inputs.append(dict(case=case,available=True,ready_iteration=i,query_iteration=target,groups=groups,calls=calls,input_path=str(out),input_sha256=sha(out)))
 (D/'frozen_inputs.json').write_text(json.dumps(dict(rows=inputs,bindings=bindings),indent=2)+'\n');frozen_sha=sha(D/'frozen_inputs.json');rows=[]
 canonicalp=E/'prince_native_canonical_v1_2026-10-20/receipt.json';canonical=json.loads(canonicalp.read_text());bindings[str(canonicalp)]=sha(canonicalp)
 for row in inputs:
  if not row['available']:rows.append(row);continue
  case=row['case'];source=E/'prince_native_cohort_v1_2026-10-20'/case;receipt=source/'receipt.json';native=json.loads(receipt.read_text());assert native['native_full_check_pass'];canon=next(x for x in canonical['results'] if x['case']==case);assert canon['semantic_consistency_gate_pass'] and canon['original_zero_counter_gate_pass'];route=source/'output.route';assert sha(route)==native['files'][str(route)];owners=final_owners(route);counts=Counter(n for group in owners.values() for n in group);assert max(counts.values())<=1;pair=defaultdict(lambda:[0,0,0]);call_errors=[0,0];calls=groups=0
  for x in map(json.loads,Path(row['input_path']).open()):
   net,node,ident,pred,baseline,count=x;truth=counts[node]-int(node in owners[net]);assert truth>=0;call_errors[0]+=count*abs(baseline-truth);call_errors[1]+=count*abs(pred-truth);pair[net,node][0]+=baseline;pair[net,node][1]+=1;pair[net,node][2]=pred;calls+=count;groups+=1
  errors=[Fraction(0),Fraction(0)]
  for (net,node),(summed,n,pred) in pair.items():
   truth=counts[node]-int(node in owners[net]);errors[0]+=abs(Fraction(summed,n)-truth);errors[1]+=abs(pred-truth)
  result=dict(row,unique_NET_node_pairs=len(pair),call_error_persistence=call_errors[0],call_error_ready_owner=call_errors[1],pair_error_persistence=rational(errors[0]),pair_error_ready_owner=rational(errors[1]),candidate_call_MAE=call_errors[1]/calls,persistence_call_MAE=call_errors[0]/calls,candidate_pair_MAE=float(errors[1]/len(pair)),persistence_pair_MAE=float(errors[0]/len(pair)));rows.append(result);bindings[str(receipt)]=sha(receipt);bindings[str(route)]=sha(route);assert sha(row['input_path'])==row['input_sha256'];bindings[row['input_path']]=row['input_sha256'];print('READY_OWNER_SCREEN_CASE',case,call_errors,[float(x) for x in errors],flush=True)
 assert len(rows)==9 and sum(x['available'] for x in rows)==6 and sha(D/'frozen_inputs.json')==frozen_sha;assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='FROZEN_READY_OWNER_CONDITIONAL_DEMAND_SCREEN_COMPLETE_NOT_PROMOTED',rows=rows,bindings=bindings,frozen_inputs_sha256=frozen_sha),indent=2)+'\n')
if __name__=='__main__':main()

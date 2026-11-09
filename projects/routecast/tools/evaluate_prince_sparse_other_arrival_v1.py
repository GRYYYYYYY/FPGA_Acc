"""Input-selected floor-active-domain diagnostic; no rescue of rejected snapshot forecaster."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from verify_prince_ownership_ledger_v2 import owner_payload
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';Q=E/'prince_connection_query_trial_v1_2026-10-20';L=E/'prince_ownership_ledger_trial_v2_2026-10-20';D=E/'prince_sparse_other_arrival_v1_2026-10-20'
def metrics(c):
 c={k:int(c.get(k,0)) for k in ['TP','FP','FN','TN']};n=sum(c.values());return dict(c,observations=n,precision=c['TP']/(c['TP']+c['FP']) if c['TP']+c['FP'] else None,recall=c['TP']/(c['TP']+c['FN']) if c['TP']+c['FN'] else None,prevalence=(c['TP']+c['FN'])/n if n else None)
def cell(pred,target):return ('TP' if target else 'FP') if pred else ('FN' if target else 'TN')
def scored(records,truth):
 calls=Counter();pairs={};strata={i:[Counter(),{}] for i in [0,1]}
 for net,node,connection,own,pred,count in records:
  target=int(any(owner!=net for owner in truth.get(node,set())));key=cell(pred,target);calls[key]+=count;pairs[net,node]=(pred,target);strata[own][0][key]+=count;strata[own][1][net,node]=(pred,target)
 pc=Counter(cell(p,t) for p,t in pairs.values());return dict(calls=metrics(calls),unique_pairs=metrics(pc),strata={str(i):dict(calls=metrics(c),unique_pairs=metrics(Counter(cell(p,t) for p,t in ps.values()))) for i,(c,ps) in strata.items()},unique_pairs_in_both_strata=len(strata[0][1].keys()&strata[1][1].keys()),zero_alert_control_calls=metrics(dict(TP=0,FP=0,FN=calls['TP']+calls['FN'],TN=calls['FP']+calls['TN'])))
def main():
 assert not D.exists();D.mkdir();design=E/'prince_reactive_floor_trial_v1_2026-10-20/sparse_other_arrival_screen_design_v1.json';oldp=E/'prince_ready_owner_forecast_v1_2026-10-20/verification.json';joinp=E/'prince_query_ledger_join_v1_2026-10-20/verification.json';source=json.loads(oldp.read_text());join=json.loads(joinp.read_text());bindings={str(p):sha(p) for p in [design,oldp,joinp,Path(__file__)]};(D/'protocol.json').write_text(json.dumps(dict(bindings=dict(bindings),policy='Frozen eligible O=I, bounded-ready other forecast alarm F>0. All predictions/selection frozen before this run joins final labels. Prior labels development-exposed. Unique NET/node dedup overall; each I-stratum dedups separately, so stratum unique counts may overlap. No new admission criterion or width/case gating.'),indent=2)+'\n');inputs=[]
 for row in source['rows']:
  case=row['case']
  if not row['available']:inputs.append(dict(case=case,available=False,reason=row['reason']));continue
  op=L/case/'capture/owners'/f"owners_{row['ready_iteration']}.bin";_,owners=owner_payload(op);counts=Counter(n for group in owners.values() for n in group);qp=Q/case/'capture/queries.tsv';assert sha(qp)==join['bindings'][str(qp)];dest=D/(case.replace('/','_')+'.inputs.jsonl');eligible=0
  with dest.open('x') as f:
   for line in qp.open():
    if int(line.split('\t',1)[0])!=row['query_iteration']:continue
    it,encoded,node,kind,occ,cap,pres,acc,base,cost,nc,active,connection,pin,sink,own,count=map(int,line.split())
    if kind not in [4,5] or occ!=own:continue
    assert cap==1 and own in [0,1];net=encoded-1;forecast=counts[node]-int(node in owners[net]);assert forecast>=0;pred=int(min(forecast,1)>0);f.write(json.dumps([net,node,connection,own,pred,count],separators=(',',':'))+'\n');eligible+=1
  assert eligible>0;inputs.append(dict(case=case,available=True,query_iteration=row['query_iteration'],ready_iteration=row['ready_iteration'],groups=eligible,input_path=str(dest),input_sha256=sha(dest)));bindings[str(op)]=sha(op);bindings[str(qp)]=sha(qp)
 frozen=D/'frozen_inputs.json';frozen.write_text(json.dumps(dict(rows=inputs,bindings=dict(bindings)),indent=2)+'\n');frozen_hash=sha(frozen);rows=[]
 for row in inputs:
  if not row['available']:rows.append(row);continue
  route=E/'prince_native_cohort_v1_2026-10-20'/row['case']/'output.route';receipt=route.parent/'receipt.json';rp=json.loads(receipt.read_text());assert rp['native_full_check_pass'] and sha(route)==rp['files'][str(route)];owners=final_owners(route);inverse={}
  for net,nodes in owners.items():
   for node in nodes:inverse.setdefault(node,set()).add(net)
  assert all(len(group)==1 for group in inverse.values());records=[json.loads(line) for line in Path(row['input_path']).open()];assert len(records)==row['groups'] and sha(row['input_path'])==row['input_sha256'];result=scored(records,inverse);rows.append(dict(row,metrics=result));bindings[str(route)]=sha(route);bindings[str(receipt)]=sha(receipt);bindings[row['input_path']]=row['input_sha256'];print('SPARSE_ARRIVAL_CASE',row['case'],json.dumps(result['calls']),flush=True)
 assert len(rows)==9 and sum(x['available'] for x in rows)==6 and sha(frozen)==frozen_hash;assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='SPARSE_OTHER_ARRIVAL_INPUT_SELECTED_DIAGNOSIS_COMPLETE',rows=rows,bindings=bindings,frozen_inputs_sha256=frozen_hash,scope='Secondary consumer-relevant diagnostic only; rejected ready forecaster remains rejected. Original full9 quality/native/fullpaid/unseen obligations unchanged.'),indent=2)+'\n')
if __name__=='__main__':main()

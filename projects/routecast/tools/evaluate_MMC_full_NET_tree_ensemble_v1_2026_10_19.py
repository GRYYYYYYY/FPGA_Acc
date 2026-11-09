"""Fixed known-family development evaluation, admitted complete predictions only."""
import pathlib,json,hashlib
from fractions import Fraction
from prospective_pressure_metrics_v1 import metrics,gate
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,separators=(',',':'));f.write('\n')
def main():
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';admit=M/'independent_prediction_verification_v1.json'
 if not admit.exists():raise SystemExit('NOT_READY: independent complete prediction admission required')
 a=json.loads(admit.read_text());assert a['status']=='ALL3_COMPLETE_NET_ENSEMBLE_IDENTITY_XML_DAG_EXPECTATION_AND_LEDGER_AUDIT_PASS';receipt=M/'receipt.json';assert a['bindings'][str(receipt)]==sha(receipt)
 for p,h in a['bindings'].items():assert sha(p)==h,p
 spec=json.loads((M/'protocol.json').read_text());assert spec['samples']==16 and spec['exact_assignment_limit']==4096 and spec['seed']==19
 old=R/'experiments/mmc_prospective_pressure_evaluation_v2_2026-10-19';op=old/'independent_metric_verification_v1.json';ov=json.loads(op.read_text());assert ov['status']=='all3_forecast_metrics_and_registered_decisions_independently_verified';orp=old/'results.json';assert ov['bindings'][str(orp)]==sha(orp);oldresults=json.loads(orp.read_text());domainfile=old/'domain.json';domain=json.loads(domainfile.read_text());assert len(domain)==len(set(domain))==258720 and sorted(domain)==domain;k=12936
 labels=R/'experiments/mmc_prospective_pressure_targets_v2_2026-10-19';lp=labels/'verification.json';labelproof=json.loads(lp.read_text());assert labelproof['status']=='all3_admitted_traces_split_at_iteration1';O=R/'experiments/mmc_full_NET_tree_ensemble_quality_v1_2026-10-19';O.mkdir();bindings={str(p):sha(p) for p in [admit,receipt,M/'protocol.json',op,orp,domainfile,lp,pathlib.Path(__file__).resolve(),R/'tools/prospective_pressure_metrics_v1.py']};vectors={}
 # Freeze every candidate/control vector before future payload reads.
 for case in spec['cases']:
  p=M/case/'expected_unique_NET_occupancy.json';assert a['bindings'][str(p)]==sha(p);ledger={int(n):Fraction(x) for n,x in json.loads(p.read_text()).items()};candidate=[ledger.get(n,Fraction(0)) for n in domain];assert all(x>=0 for x in candidate);baselinefile=old/(case+'_predictions.json');assert oldresults['bindings'][str(baselinefile)]==sha(baselinefile);baseline=json.loads(baselinefile.read_text());vectors[case]={'NET_tree_ensemble':candidate,**baseline};assert set(vectors[case])=={'NET_tree_ensemble','raw_min','previous_native','native_retained','uniform_risk'}
  vp=O/(case+'_predictions.json');write(vp,{model:[str(x) for x in values] for model,values in vectors[case].items()});bindings[str(vp)]=sha(vp);bindings[str(p)]=sha(p);bindings[str(baselinefile)]=sha(baselinefile)
 write(O/'prediction_admission.json',dict(bindings=bindings,cases=spec['cases'],all_vectors_materialized_before_future_payload_reads=True,scope='Known exposed development data; not prospective/heldout. Same fixed K/metrics/controls as predictor protocol.'))
 rows=[]
 for case in spec['cases']:
  p=labels/case/'targets.json';assert labelproof['bindings'][str(p)]==sha(p);target=json.loads(p.read_text());assert target['first_target_iteration']==2;result={}
  for name,raw in target['targets'].items():
   truth={int(n):x for n,x in raw.items()};t=[truth.get(n,0) for n in domain];result[name]={model:metrics(pred,t,k,domain) for model,pred in vectors[case].items()}
   previous=next(row for row in oldresults['episodes'] if row['episode']==case)['metrics'][name]
   for control in ['raw_min','previous_native','native_retained','uniform_risk']:assert result[name][control]==previous[control]
  primary=result['sum_checkpoint_overflow_units'];decision=gate(primary['NET_tree_ensemble'],{model:primary[model] for model in ['raw_min','previous_native','native_retained','uniform_risk']},k,len(domain));rows.append(dict(case=case,primary_gate=decision,metrics=result));bindings[str(p)]=sha(p);print('FULL ENSEMBLE QUALITY',case,decision,flush=True)
 write(O/'results.json',dict(status='all3_complete_NET_ensemble_forecasts_development_evaluated',bindings=bindings,cases=rows,all3_primary_gate_pass=all(row['primary_gate']=='pass' for row in rows),independent_metric_audit_pending=True,strict_unseen_family_admitted=False,complete_workflow_gain_proven=False,scope='Known MMC development data only. 3cases all required, candidate vs raw_min/source/native_retained controls under fixed capture/rho gate; uniform capture only. No family holdout, native utility, balanced complete-time or hardware claim.'))
if __name__=='__main__':main()

"""Six probability words only; native inference never receives final-owner labels."""
import json,time,struct
from pathlib import Path
from pre_route_endpoints import sha
from calibrate_prince_sparse_other_mean_v1 import fit
from verify_prince_ready_owner_forecast_v1 import final_inverse,L
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_sparse_other_mean_calibration_v1_2026-10-20';D=E/'prince_input_mean_models_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);mp=S/'models.json';proof=S/'verification.json';v=json.loads(proof.read_text());assert sha(mp)==v['models_sha256'];models=json.loads(mp.read_text());sourcep=E/'prince_sparse_other_arrival_v1_2026-10-20/verification.json';source=json.loads(sourcep.read_text());bindings={str(p):sha(p) for p in [Path(__file__),mp,proof,sourcep,S/'independent_verification_v1.json',S/'native_mean_component_trial_design_v1.json']};tick=time.perf_counter();data={};acquisition={}
 for row in source['rows']:
  if not row['available']:continue
  case=row['case'];inp=Path(row['input_path']);assert sha(inp)==row['input_sha256'];oracle=L/case/'capture/queries.tsv.ledger.bin';truth=final_inverse(oracle);records={}
  for net,node,connection,own,ready,n in map(json.loads,inp.open()):
   y=int(bool(truth[node]-{net}));key=(own,net,node)
   if key in records:assert records[key][:2]==(ready,y);records[key]=(ready,y,records[key][2]+n)
   else:records[key]=(ready,y,n)
  data[case]=records;receipt=E/'prince_connection_query_trial_v1_2026-10-20'/case/'capture/receipt.json';acquisition[case]=json.loads(receipt.read_text())['native_seconds']
  for p in [inp,oracle,receipt]:bindings[str(p)]=sha(p)
 data_preparation_seconds=time.perf_counter()-tick;training=[]
 for model in models['folds']:
  tick=time.perf_counter();replay=fit(model['train_cases'],data);seconds=time.perf_counter()-tick
  for key in ['I_only_words','I_ready_words','cell_counts','training_state_count']:assert replay[key]==model[key]
  training.append(dict(heldout_episode=model['heldout_episode'],train_cases=model['train_cases'],replayed_fit_seconds=seconds,known_training_query_acquisition_seconds=sum(acquisition[x] for x in model['train_cases']),upstream_frontend_pack_place_cost_missing=True))
 rows=[]
 for w in [96,128,160]:
  for ep in range(1,4):
   case=f'w{w:03d}/episode_{ep:02d}';group=f'episode_{ep:02d}';model=next(x for x in models['folds'] if x['heldout_episode']==group);assert all(x.split('/')[1]!=group for x in model['train_cases']);ref=L/case/'capture';ids=(ref/'identity.txt').read_text().splitlines();resolved=(ref/'callback.tsv.resolved.sha256').read_text().strip();rr=ref/'boundary/iteration_1.bin';nrr=struct.unpack_from('<Q',rr.read_bytes(),16)[0];mapping=E/'prince_resident_consumer_v1_2026-10-20'/case/'NET_mapping.json';nnets=len(json.loads(mapping.read_text()));words=[model['I_only_words'][str(i)] for i in [0,1]]+[model['I_ready_words'][f'{i},{r}'] for i in [0,1] for r in [0,1]];out=D/(case.replace('/','_')+'.model.txt');out.write_text('\n'.join(['INPUT_ONLY_READY_MEAN_V1',ids[0],ids[1],ids[2],case,ids[6],resolved,sha(mp),group,f'{nnets} {nrr}',str(len(model['train_cases'])),*model['train_cases'],' '.join(map(str,words))])+'\n');rows.append(dict(case=case,payload=str(out),sha256=sha(out),heldout_episode=group,train_cases=model['train_cases'],source_models_sha256=sha(mp),six_probability_words=words,label_payload_in_inference=False))
   for p in [ref/'identity.txt',ref/'callback.tsv.resolved.sha256',rr,mapping]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'manifest.json').write_text(json.dumps(dict(rows=rows,training_replay=training,data_preparation_seconds=data_preparation_seconds,bindings=bindings,scope='Frozen out-of-episode tables, all9 cases including unlabeled width96. Replayed fit and known acquisition costs charged; historical upstream costs incomplete, no fullpaid timing evidence.'),indent=2)+'\n');print('INPUT_ONLY_MEAN_MODELS_PREPARED',len(rows))
if __name__=='__main__':main()

"""One-window activation, live-only ready cache, fold inputs and exact scalar witness coverage."""
import json,struct,bisect
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from verify_prince_query_ledger_join_v1 import history
from verify_prince_ownership_ledger_v2 import owner_payload
from verify_prince_native_query_trial_v1 import f32,value,bits
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_input_mean_trial_v1_2026-10-20';OLD=E/'prince_present_identity_trial_v1_2026-10-20'
def table(p):return [list(map(int,s.split())) for s in p.read_text().splitlines()]
def main():
 pp=D/'protocol.json';vp=D/'verification.json';p=json.loads(pp.read_text());v=json.loads(vp.read_text());by={x['case']:x for x in v['rows']};bindings={str(q):sha(q) for q in [pp,vp,Path(__file__)]};results=[];mode_ids={'identity':0,'base':1,'ready':2,'residual':3}
 assert len(by)==36 and all(x['native_exit_code'] in [0,2] and x['iterations']>0 and x['callback_sequence_complete'] for x in v['rows'])
 for job in p['jobs']:
  full=job['case'];case,mode=full.rsplit('/',1);d=D/full;row=by[full];qp=d/'queries.tsv';a=table(qp);assert len(a)==row['iterations'] and all(len(x)==17 and x[5]==x[2] and x[15]+x[16]==x[2] and x[8]<=x[16] and x[9]==0 and sum(x[11:15])==x[7]<=x[6]<=x[2] for x in a);events=[int(x.split()[0]) for x in (d/'callback.tsv.ready.tsv').read_text().splitlines() if int(x.split()[4])];assert len(events)<=1;ready=events[0] if events else None;model=job['input_model'];payload=Path(model['payload']);assert sha(payload)==model['sha256'];lines=payload.read_text().splitlines();assert lines[0]=='INPUT_ONLY_READY_MEAN_V1' and lines[4]==case and lines[8]==case.split('/')[1];assert lines[11:15]==model['train_cases'] and all(x.split('/')[1]!=lines[8] for x in lines[11:15]);words=list(map(int,lines[15].split()));assert words==model['six_probability_words'] and len(words)==6
  receipt=d/'queries.tsv.model_load.tsv';load=receipt.read_text().strip().split();assert len(load)==7 and row['launch_before_ns']<=int(load[0])<=int(load[1])<=row['launch_after_ns'];assert load[2:]==[model['sha256'],case,model['heldout_episode'],str(mode_ids[mode]),model['source_models_sha256']]
  if mode=='identity':
   assert row['nonclock_iteration_summaries_equal'] and row['terminal_physical_sequences_equal'];old=table(OLD/case/'capture/queries.tsv');assert len(old)==len(a) and all(x[:6]==y for x,y in zip(a,old));assert all(x[8]==x[16]==0 for x in a)
  if ready is None:
   assert all(x[6:10]==[0,0,0,0] and x[10]==0 and x[15]==x[2] and x[16]==0 for x in a);assert not (d/'queries.tsv.ready_codes.bin').exists() and not (d/'queries.tsv.mean_witness.tsv').exists();results.append(dict(case=full,ready_iteration=None,window_calls=0,changed_calls=0,scalar_groups=0,witness_calls=0,not_activated=True));continue
  target=ready+1;identity=D/case/'identity';b=table(identity/'queries.tsv');assert all(x[:6]==y[:6] for x,y in zip(a[:ready],b[:ready]));assert all(x[6]==x[2] and x[10]==ready for x in a if x[0]==target)
  for x in a:
   if x[0]!=target:assert x[6:10]==[0,0,0,0] and x[15]==x[2] and x[16]==0
  for i in range(1,ready+1):
   for name in [f'boundary/iteration_{i}.bin',f'boundary/boxes_{i}.bin',f'owners/owners_{i}.bin']:assert sha(d/name)==sha(identity/name)
  op=d/'owners'/f'owners_{ready}.bin';_,owners=owner_payload(op);inverse=defaultdict(set)
  for net,nodes in owners.items():
   for node in nodes:inverse[node].add(net)
  codesp=d/'queries.tsv.ready_codes.bin';raw=codesp.read_bytes();assert raw[:8]==b'RCMEAN01';i,nrr,nnets=struct.unpack_from('<QQQ',raw,8);assert i==ready and len(raw)==32+4*nrr;codes=struct.unpack_from('<'+'I'*nrr,raw,32)
  for node,code in enumerate(codes):
   nets=inverse[node];expected=0 if not nets else (next(iter(nets))+1 if len(nets)==1 else nnets+1);assert code==expected
  lp=d/'queries.tsv.ledger.bin';entries,times,occupancy=history(lp);witness=d/'queries.tsv.mean_witness.tsv';groups=0;covered=0;positive=changed=0;cells=[0]*4
  for x in table(witness):
   assert len(x)==19;i,net,node,connection,occ,own,r,pres,acc,base,qb,qc,delta,h,original,returned,mid,count,epoch=x;assert i==target and mid==mode_ids[mode] and occ==own and own in [0,1] and r in [0,1] and count>0;entry_epoch,entry_iteration,entry_net,pin,sink,retained=entries[connection];assert (entry_epoch,entry_iteration,entry_net)==(epoch,i,net);assert own==int(node in retained) and occ==occupancy[node][bisect.bisect_right(times[node],epoch)-1];assert r==int(bool(inverse[node]-{net}));assert qb==words[own] and qc==words[2+own*2+r]
   expected_delta=0. if mode=='identity' else value(qb) if mode=='base' else value(qc) if mode=='ready' else max(0.,f32(value(qc)-value(qb)));assert bits(expected_delta)==delta;expected_h=f32(occ+expected_delta);assert bits(expected_h)==h;current_present=f32(1.+f32(value(pres)*occ));forecast_present=f32(1.+f32(value(pres)*expected_h));expected_original=f32(f32(value(base)*value(acc))*current_present);expected_return=f32(f32(value(base)*value(acc))*forecast_present);assert bits(expected_original)==original and bits(expected_return)==returned and expected_return>=expected_original;covered+=count;groups+=1;cells[2*own+r]+=count;positive+=count*(expected_delta>0);changed+=count*(original!=returned)
  active=next(x for x in a if x[0]==target);assert covered==active[7] and cells==active[11:15] and positive==active[16] and changed==active[8];assert all(x[16]==0 for x in a if x[0]!=target)
  for path in [qp,receipt,payload,op,codesp,lp,witness]:
   if path!=payload:assert sha(path)==row['files'][str(path)]
   bindings[str(path)]=sha(path)
  results.append(dict(case=full,ready_iteration=ready,window_calls=active[6],eligible_calls=covered,changed_calls=changed,positive_delta_calls=positive,scalar_groups=groups,witness_calls=covered,probability_words_exact=True,before_ready_identity=True,after_window_identity_checked=True))
 assert len(results)==36 and all(sha(p)==h for p,h in bindings.items());out=D/'input_mean_inference_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='INPUT_ONLY_MODEL_IDENTITY_WINDOW_FEATURES_AND_GROUPED_SCALARS_VERIFIED',rows=results,bindings=bindings,limitations=['Witness groups cover all eligible evaluations numerically; first representative per scalar group has independently replayed epoch/owner/ready inputs. Remaining per-query feature equality uses runtime ledger checks and verified cache encoding.','No every-inlined-cost-path coverage or global forecast/unseen/fullpaid claim.']),indent=2)+'\n');print('INPUT_MEAN_INFERENCE_PASS',len(results),sum(x['scalar_groups'] for x in results),sum(x['witness_calls'] for x in results))
if __name__=='__main__':main()

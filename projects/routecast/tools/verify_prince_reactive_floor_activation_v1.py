"""Verify before-ready identity, actual label activation, payload identities and cost deltas."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_reactive_floor_trial_v1_2026-10-20';OLD=R/'experiments/prince_present_identity_trial_v1_2026-10-20'
def table(path):return [list(map(int,line.split())) for line in path.read_text().splitlines()]
def main():
 pp=D/'protocol.json';vp=D/'verification.json';p=json.loads(pp.read_text());v=json.loads(vp.read_text());rows={x['case']:x for x in v['rows']};bindings={str(q):sha(q) for q in [pp,vp,Path(__file__)]};results=[]
 for job in p['jobs']:
  full=job['case'];case,mode=full.rsplit('/',1);d=D/full;record=rows[full];qp=d/'queries.tsv';a=table(qp);assert len(a)==record['iterations'] and all(len(x)==11 and x[5]==x[2] and x[7]==x[8]+x[9]<=x[6]<=x[2] for x in a);events=[int(x.split()[0]) for x in (d/'callback.tsv.ready.tsv').read_text().splitlines() if int(x.split()[4])];assert len(events)<=1;ready=events[0] if events else None
  if mode=='control':
   old=OLD/case/'capture';assert all(x[:6]==y for x,y in zip(a,table(old/'queries.tsv')));assert record['nonclock_iteration_summaries_equal'] and record['terminal_physical_sequences_equal'];assert all(x[6:10]==[0,0,0,0] for x in a)
  else:
   assert ready is not None;control=D/case/'control';b=table(control/'queries.tsv');assert all(x[:6]==y[:6] and x[6:10]==[0,0,0,0] for x,y in zip(a[:ready],b[:ready]));assert all(x[6]==x[2] and x[10]==ready for x in a[ready:]);assert mode=='floor' or sum(x[7] for x in a)>0
   if mode=='floor':assert all(x[9]==0 for x in a)
   for i in range(1,ready+1):
    for path in [d/'boundary'/f'iteration_{i}.bin',d/'boundary'/f'boxes_{i}.bin',d/'owners'/f'owners_{i}.bin']:
     ref=control/path.relative_to(d);assert sha(path)==sha(ref);bindings[str(path)]=sha(path);bindings[str(ref)]=sha(ref)
  consumer=json.loads((d/'consumer_mode.json').read_text());assert consumer['label_oracle_after_ready']==(mode!='control') and consumer['reactive_floor']==(mode=='floor');payload=job['oracle_input'];load=d/'queries.tsv.payload_load.tsv';load_seconds=0
  if payload['available']:
   fields=load.read_text().strip().split();begin,end=int(fields[0]),int(fields[1]);assert record['launch_before_ns']<=begin<=end<=record['launch_after_ns'];assert fields[2]==payload['sha256'] and fields[3]==case;load_seconds=(end-begin)/1e9;assert sha(payload['payload'])==payload['sha256'];bindings[str(load)]=sha(load);bindings[payload['payload']]=payload['sha256']
  else:assert mode=='control' and ready is None and not load.exists()
  for path in [qp,d/'consumer_mode.json',d/'callback.tsv.ready.tsv']:assert sha(path)==record['files'][str(path)];bindings[str(path)]=sha(path)
  subtotal=(payload.get('oracle_generation_native_seconds',0)+payload.get('prepare_seconds',0)+record['paid_case_seconds']);results.append(dict(case=full,ready_iteration=ready,native_legal=record['native_full_check_pass'],iterations=record['iterations'],oracle_channel_calls=sum(x[6] for x in a),changed_cost_calls=sum(x[7] for x in a),raised_cost_calls=sum(x[8] for x in a),lowered_cost_calls=sum(x[9] for x in a),payload_load_seconds=load_seconds,known_cost_subtotal_seconds=subtotal,not_fullpaid_speed_evidence=True))
 assert len(results)==21 and all(sha(p)==h for p,h in bindings.items());out=D/'activation_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='FIXED_READY_ACTIVATION_AND_BEFORE_READY_IDENTITY_VERIFIED',rows=results,bindings=bindings,limitations='Labels from baseline final routes are factual-policy labels, not counterfactual demand after costs change. Known cost subtotal excludes historical frontend/pack/place/build/audits; cannot support fullpaid speedup.'),indent=2)+'\n');print(json.dumps(results))
if __name__=='__main__':main()

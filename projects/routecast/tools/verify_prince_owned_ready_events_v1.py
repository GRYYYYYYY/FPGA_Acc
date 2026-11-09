"""Live event/controller/payload parity and bounded same-domain process clocks."""
import json,struct
from pathlib import Path
from pre_route_endpoints import sha
from prince_forecast_ready_gate_v1 import ReadyGate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_owned_ready_trial_v1_2026-10-20'
def main():
 vp=D/'verification.json';v=json.loads(vp.read_text());assert len(v['rows'])==18 and all(x['callback_sequence_complete'] and x['no_iteration_route_files'] and x['nonclock_iteration_summaries_equal'] and x['terminal_physical_sequences_equal'] for x in v['rows']);replay=E/'prince_forecast_ready_replay_v1_2026-10-20/decisions.json';expected={x['case']:x['selected_iteration'] for x in json.loads(replay.read_text())['rows']};bindings={str(q):sha(q) for q in [vp,replay,Path(__file__),R/'tools/prince_forecast_ready_gate_v1.py',R/'tools/prince_ready_gate_v1.h']};rows=[];observations=events=payloads=0
 for row in v['rows']:
  case,mode=row['case'].rsplit('/',1);d=D/row['case'];receipt=json.loads((d/'receipt.json').read_text());assert all(sha(q)==h for q,h in receipt['files'].items());callbacks=[list(map(int,s.split())) for s in (d/'callback.tsv').read_text().splitlines()];reference=E/'prince_configured_consumer_trial_v1_2026-10-20'/row['case']/'callback.tsv';old=[list(map(int,s.split())) for s in reference.read_text().splitlines()];assert [x[:11] for x in callbacks]==[x[:11] for x in old];ready=[s.split() for s in (d/'callback.tsv.ready.tsv').read_text().splitlines()];clock=[list(map(int,s.split())) for s in (d/'callback.tsv.ready_clock.tsv').read_text().splitlines()];begin,end,code=map(int,(d/'main_clock.tsv').read_text().split());assert code==row['native_exit_code'] and row['case_begin_ns']<=row['launch_before_ns']<=begin<=end<=row['launch_after_ns'];identity=(d/'identity.txt').read_text().splitlines();resolved=(d/'callback.tsv.resolved.sha256').read_text().strip();controller=ReadyGate({'identity':tuple(identity),'resolved':resolved});selected=[];publication=None
  assert len(callbacks)==len(ready)==len(clock)==row['iterations']
  for index,(raw,c,cb) in enumerate(zip(ready,clock,callbacks),1):
   assert len(raw)==9;iteration,nodes,over,streak,emitted,rh,bh=map(int,raw[:7]);decision=int(raw[8]);want=controller.observe(controller.identity,index,cb[1],cb[4]);assert iteration==index and nodes==cb[1] and over==cb[4] and bool(emitted)==want and streak==controller.streak and [rh,bh]==cb[7:9] and raw[7]==('FORECAST_READY' if want else 'CONTINUE');assert c[0]==index and c[1]==decision and begin<=cb[11]<=decision<=c[2]<=cb[12]<=cb[13]<=end;observations+=1
   if want:selected.append(index);publication=c[2]
  assert selected==([] if expected[case] is None else [expected[case]]);selected_iteration=selected[0] if selected else None
  if selected:
   events+=1;reference_root=E/'prince_resident_phase_trial_v1_2026-10-20'/case/'capture/boundary';payloads_to_check=[(d/'callback.tsv.ready_RR.bin',reference_root/f'iteration_{selected_iteration}.bin'),(d/'callback.tsv.ready_boxes.bin',reference_root/f'boxes_{selected_iteration}.bin')]
   for a,b in payloads_to_check:assert sha(a)==sha(b);bindings[str(b)]=sha(b);payloads+=1
   actual=(d/'callback.tsv.ready_identity.txt').read_text().splitlines();assert actual==identity+[resolved,str(selected_iteration)];record=dict(native_main_to_event_seconds=(publication-begin)/1e9,staged_case_to_event_seconds=(publication-row['case_begin_ns'])/1e9,remaining_native_main_seconds=(end-publication)/1e9)
  else:
   assert not list(d.glob('callback.tsv.ready_*.bin')) and not (d/'callback.tsv.ready_identity.txt').exists();record={}
  rows.append(dict(case=case,mode=mode,selected_iteration=selected_iteration,main_seconds=(end-begin)/1e9,clock=record));
  for q in [d/'receipt.json',reference,d/'callback.tsv.ready.tsv',d/'callback.tsv.ready_clock.tsv',d/'main_clock.tsv']:bindings[str(q)]=sha(q)
 assert observations==454 and events==12 and payloads==24 and all(sha(q)==h for q,h in bindings.items());(D/'ready_event_verification_v1.json').write_text(json.dumps(dict(status='ALL18_LIVE_RUNS_454_RULE_OBSERVATIONS_AND12_READY_EVENTS_MATCH_FROZEN_REPLAY',rows=rows,observations=observations,ready_events=events,RR_BB_payload_pairs=12,byte_identical_payloads=payloads,bindings=bindings,scope='Live FORECAST_READY never stops/commits native routing. Copied RR/BB/identity survive callback expiry; all triggering phase payloads match audited historical observation. Clock domains validated by launch-before/main/event/main-end/launch-after bounds on this host. Main clock excludes loader/startup/destruction outside main; staged-case clock includes only that observed staging/run prefix, not earlier protocol/build/compile/pack/place costs or later independent audits. Publication means stream flush, not fsync durability or remote subscriber latency. No fullpaid gain/unseen claim.'),indent=2)+'\n');print('LIVE_READY_EVENTS_PASS',observations,events,payloads)
if __name__=='__main__':main()

"""Forced rollback after FULL in a genuinely routed, previously synchronized context."""
import sys,json,os,shutil,subprocess,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from live_mailbox_thread_v2 import Worker
from canonical_reload_inventory import canonical_reload
out=R/'experiments/native_postroute_v5_rollback_2026-10-07';out.mkdir();source=R/'experiments/native_resume_postroute_v5_integrated_adder_step3_workflow_2026-10-07';r=json.loads((source/'receipt.json').read_text());cmd=next(s['native']['command'] for s in r['stages'] if s['stage']=='first').copy();w=out/'native';w.mkdir()
for name in ('design.blif','design.net','design.place'):shutil.copyfile(source/'first'/name,w/name)
ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inv=SharedRRInventory(ctx);worker=Worker(ctx,inv,out/'mailbox');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_TX_POST_ROUTE='1',ROUTECAST_TX_FORCE_ROLLBACK='1',ROUTECAST_TX_PRODUCER=str(R/'tools/native_route_transaction/live_search_client_v3.py'),ROUTECAST_TX_EXPORT_PREFIX=str(w/'live'),ROUTECAST_TX_CANDIDATE=str(w/'candidate.route'),ROUTECAST_TX_REQUEST=str(w/'request.txt'),ROUTECAST_TX_PREFIX=str(w/'tx'),ROUTECAST_SEARCH_ENDPOINT=str(ep),ROUTECAST_SEARCH_REPORT=str(w/'live.initial.setup.rpt'),ROUTECAST_SEARCH_MAILBOX=str(out/'mailbox'),ROUTECAST_REUSE_STEP='0',ROUTECAST_RESUME_SAME_PLACE_ROUTE=str(source/'first_seed.route'),ROUTECAST_RESUME_ALLOW_PARTIAL='1',ROUTECAST_RR_FLOORS_FILE=str(source/'rr_floors.txt'))
with (w/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=150).returncode
worker.finish();assert code==0;status=json.loads((w/'tx.attempt0.json').read_text());assert not status['committed'] and status['mutation_started'] and status['epoch_before']==status['epoch_after']==0 and 'forced post-validation' in status['error'];assert (w/'tx.attempt0.before.route').read_bytes()==(w/'tx.attempt0.after.route').read_bytes();cpds=list(map(float,re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',(w/'run.log').read_text())));assert cpds==[5.05896,5.05896]
p=dict(command=cmd,width=32,decision='R',cpd_ns=5.05896,files={str(p):sha(p) for p in w.iterdir() if p.is_file()});canonical=canonical_reload(p,w,out/'canonical',inv);assert canonical['mismatches']==canonical['fixups']==0
(out/'receipt.json').write_text(json.dumps(dict(status=status,cpds_ns=cpds,canonical=canonical,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()},scope='Actual seed-routed step3, first native sync/timing then forced post-FULL rollback; routing bytes and epoch restored, packed baseline restored and original sync rerun, fresh native timing equals initial, final normalized original FULL/STA zero mismatch/fixup.'),indent=2)+'\n');print('ROLLBACK PASS')

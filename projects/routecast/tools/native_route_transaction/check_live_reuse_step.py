"""Live search transaction followed by normalized original-native FULL/STA."""
import sys,json,os,re,time,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from canonical_reload_inventory import canonical_reload
from source_binding import closure
out=R/('experiments/native_live_search_reuse_2026-10-07/step_'+os.environ['ROUTECAST_REUSE_STEP']);out.mkdir();b=R/'experiments/native_resume_shared_cold_adder_step3_workflow_2026-10-07';base=b/'canonical';old=json.loads((b/'receipt.json').read_text());ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';producer=R/'tools/native_route_transaction/live_search_client_v2.py';binary=R/'build/native_route_transaction_v6_2026-10-07/routecast_transaction_vpr';w=out/'native';w.mkdir()
inputs={str(p):sha(p) for p in (ep,producer,binary,*[base/n for n in ('design.blif','design.net','design.place','design.route','report_timing.setup.rpt')])};sources=closure([Path(__file__),producer,R/'tools/native_route_transaction/live_search_server_v2.py',R/'tools/native_route_transaction/live_search_worker_v2.py']);(out/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,scope='Known adder step3 fresh live search; includes native bootstrap/export/producer/import/sync/timing and final normalized reload. Prepared source endpoints and initial own timing report; no cold candidate read.'),indent=2)+'\n')
for n in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(base/n,w/n)
cmd=list(old['canonical']['command']);cmd[0]=str(binary);env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_SEARCH_SOCKET']=os.environ['ROUTECAST_SEARCH_SOCKET'];env.update(ROUTECAST_TX_PRODUCER=str(producer),ROUTECAST_TX_EXPORT_PREFIX=str(w/'live'),ROUTECAST_TX_CANDIDATE=str(w/'candidate.route'),ROUTECAST_TX_REQUEST=str(w/'request.txt'),ROUTECAST_TX_PREFIX=str(w/'tx'),ROUTECAST_SEARCH_ENDPOINT=str(ep),ROUTECAST_SEARCH_REPORT=str(base/'report_timing.setup.rpt'))
start=time.perf_counter()
with (w/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=w,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=150).returncode
native_s=time.perf_counter()-start;log=(w/'run.log').read_text();assert code==0,(code,log[-4000:]);status=json.loads((w/'tx.attempt0.json').read_text());assert status['committed'] and status['epoch_after']==1
cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);assert cpd==4.87739;shutil.copyfile(w/'tx.attempt0.after.route',w/'output.route')
ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'verification_context');inv=SharedRRInventory(ctx)
p=dict(command=cmd.copy(),width=old['canonical']['width'],decision='R',cpd_ns=cpd,files={str(p):sha(p) for p in w.iterdir() if p.is_file()});p['command'][p['command'].index('--analysis')]='--route';canonical=canonical_reload(p,w,out/'canonical',inv)
assert all(sha(p)==h for p,h in inputs.items()) and all(sha(p)==h for p,h in sources.items())
(out/'receipt.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,native_including_producer_seconds=native_s,total_through_final_proof_seconds=time.perf_counter()-start,cpd_ns=cpd,status=status,producer=json.loads((w/'live.search/receipt.json').read_text()),canonical=canonical,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()},scope='One known fixture, live fresh search and original normalized FULL/STA. No fair repeated shared-context cold timing comparison yet.'),indent=2)+'\n');print('PASS',cpd,native_s,flush=True)

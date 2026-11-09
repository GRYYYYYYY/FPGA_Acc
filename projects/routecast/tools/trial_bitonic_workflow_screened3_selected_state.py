"""Materialize joint QoR selection, revalidate native state, import selected ledger."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha,extract
from owner_union_wire_rc_context_cached_tree import OwnerUnionWireRCContext
from native_route_ledger_import_compact import import_native_ledger,physical_paths
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];cold=ROOT/'experiments/bitonic_workflow_screened3_swapped_cold_2026-10-07';out=ROOT/'experiments/bitonic_workflow_screened3_selected_state_2026-10-07';out.mkdir(exist_ok=True);v=json.loads((cold/'verification.json').read_text());r=json.loads((cold/'receipt.json').read_text());assert sha(cold/'receipt.json')==v['receipt_sha256']
protocol=dict(source_sha256=sha(Path(__file__)),cold_verification_sha256=sha(cold/'verification.json'),rule='candidate iff CPD <= cold AND wirelength <= cold, native reported precision',scope='Actual prepared archived-bundle selection/reload/import, no fresh in-process routing gate or full accepted workflow clock.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for ref,row in zip(v['rows'],r['rows']):
 n=ref['count'];assert n==row['count'];assert all(sha(f)==d for f,d in row['files'].items());accept=ref['joint_nonregression'];candidate=None
 if accept:
  can=ROOT/f'experiments/bitonic_workflow_screened3_resident_staging_n{n}_canonical_2026-10-07';cr=json.loads((can/'receipt.json').read_text());cv=json.loads((can/'verification.json').read_text());assert sha(can/'receipt.json')==cv['receipt_sha256'];candidate=Path(cr['results'][0]['cwd'])/'reload';assert all(sha(f)==d for f,d in cr['results'][0]['sha256'].items())
 chosen=candidate if accept else ROOT/f'work/bitonic_workflow_screened3_swapped_cold_n{n}_canonical_2026-10-07/0/reload';work=out/f'n{n}';work.mkdir(exist_ok=True);tick=time.perf_counter()
 for name in ['design.blif','design.net','design.place','design.route']:shutil.copyfile(chosen/name,work/name)
 bundle={name:sha(work/name) for name in ['design.blif','design.net','design.place','design.route']};cmd=row['command'].copy();cmd[cmd.index('--route')]='--analysis';graph=Path(cmd[cmd.index('--read_rr_graph')+1])
 with (work/'selected.log').open('w') as f:code=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
 log=(work/'selected.log').read_text();assert code==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
 assert all(sha(work/name)==d for name,d in bundle.items());assert not any(int(x) for x in re.findall(r'(?:Found (\d+) mismatches|Fixed (\d+) routing traces)',log) for x in x if x)
 cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1];wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);assert F(cpd)<=F(ref['cold_cpd_ns']) and wire<=ref['cold_wirelength']
 ep,mapping=extract(work/'design.net',work/'design.place',graph);(work/'endpoints.json').write_text(json.dumps(ep,indent=2)+'\n');ctx=OwnerUnionWireRCContext(work/'endpoints.json',weight_ns=F(1,20));state=import_native_ledger(ctx,work/'design.route');a=audit(graph,work/'design.route');assert len(state.records)==ref['connections'];assert {str(k):val for k,val in state.ledger.items()}==a['node_occupancy'];assert physical_paths(work/'design.route')==physical_paths(chosen/'design.route')
 ledger=dict(records=len(state.records),node_occupancy={str(k):val for k,val in state.ledger.items()},unions={str(k):sorted(val) for k,val in state.unions.items()});(work/'ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');rows.append(dict(count=n,selection='candidate' if accept else 'cold',cpd_ns=cpd,wirelength=wire,connections=len(state.records),reload_frontend_import_audit_seconds=time.perf_counter()-tick,command=cmd,files={str(f):sha(f) for f in work.iterdir() if f.is_file()}));print(n,rows[-1]['selection'],cpd,wire,flush=True)
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==3),indent=2)+'\n')
assert sha(Path(__file__))==protocol['source_sha256']

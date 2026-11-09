"""Canonical/native physical proof for actual same-placement NET repair."""
import json,re,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from loaded_native_canonical_reload import canonical_reload
from stream_native_route_audit_cached import audit
from native_route_work_metrics import extract
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'experiments/native_resume_target_partial_v7_2026-10-07'
rp=base/'receipt.json';r=json.loads(rp.read_text());x=r['rows'][0];assert x['mode']=='resume' and x['exit_code']==0
work=base/'resume';log=work/'run.log';assert sha(log)==x['log_sha256']
text=log.read_text();metrics=extract(text);assert metrics['routing_success'] and metrics['rerouted_connection_attempts']>0
cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1];wire=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1])
p=dict(width=32,decision='R',command=x['command'],cpd_ns=float(cpd),files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
canonical=canonical_reload(p,work,work/'canonical');assert canonical['mismatches']==canonical['fixups']==0
route=work/'canonical/design.route';graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml'
a=audit(graph,route);assert a['overflow_units']==0 and len(a['connections'])==1929
norm=lambda f:{n:Counter(paths) for n,paths in physical_paths(f).items() if paths}
paths=norm(route);assert paths==norm(work/'output.route')
seed=norm(graph.parent/'design.route');assert paths.keys()==seed.keys();changed=[n for n in seed if seed[n]!=paths[n]]
ep=ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target_endpoints.json';e=json.loads(ep.read_text())
expected=Counter((e['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in e['connections'])
actual=Counter((name,path[0][0],path[-1][0]) for name,rows in paths.items() for path,count in rows.items() for _ in range(count));assert actual==expected
report=dict(receipt_sha256=sha(rp),verifier_sha256=sha(Path(__file__)),native_metrics=metrics,canonical=canonical,physical_audit=a,endpoint_json_sha256=sha(ep),all1929_endpoints_match=True,canonical_paths_preserved=True,changed_net_names=changed,cpd_ns=cpd,wirelength=wire,scope='Actual target w32/m2 resume from partial seed; missing52 NETs initial1ns estimate, not partial STA bound. Canonical zerofixup FULL/STA and physical union proof. No independent initial occupancy snapshot proof, heldout or netgain; same-target quality must compare cold CPD2.87238/wire11847.')
(base/'repair_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(metrics['iterations'],metrics['rerouted_connection_attempts'],cpd,wire,changed)

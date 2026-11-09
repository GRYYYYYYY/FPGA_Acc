"""Execute explicit native cold fallback after frozen budget preflight rejection."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from loaded_native_canonical_reload import canonical_reload,binary
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];pre=ROOT/'experiments/mux_budget_preflight_2026-10-06';r=json.loads((pre/'receipt.json').read_text());assert len(r['rows'])==3;out=ROOT/'experiments/mux_preflight_cold_fallback_2026-10-06';out.mkdir();gate=json.loads((ROOT/'experiments/mux_budget_repair_quality_gate_2026-10-06/receipt.json').read_text());cases=json.loads((ROOT/'experiments/mux_live_placement_updates_2026-10-06/protocol.json').read_text())['cases'];env={k:v for k,v in os.environ.items()if not k.startswith('ROUTECAST_')};rows=[]
for pf,old,spec in zip(r['rows'],gate['rows'],cases):
 w=pf['width'];assert w==old['width']==spec['width']and pf['status']=='REJECT_BUDGET_CANDIDATE_USE_NATIVE_COLD';work=out/f'w{w}';work.mkdir();source=Path(spec['source']);started=time.perf_counter()
 for name in ('design.blif','design.net'):shutil.copyfile(source/name,work/name)
 shutil.copyfile(spec['swapped'],work/'design.place');cmd=old['native']['command'].copy();cmd[0]=str(binary)
 with (work/'run.log').open('w')as stream:code=subprocess.run(cmd,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
 assert code==0;cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',(work/'run.log').read_text())[-1]);shutil.copyfile(work/'design.place',work/'accepted.place');p=dict(width=w,decision='A',command=cmd,cpd_ns=cpd,files={str(p):sha(p)for p in work.iterdir()if p.is_file()});reload=canonical_reload(p,work,work/'canonical');a=audit(source/'rr_graph.xml',work/'canonical/design.route');assert a['overflow_units']==0 and len(a['connections'])=={8:466,16:936,32:1929}[w]
 rows.append(dict(width=w,native=p,reload=reload,physical_connections_checked=len(a['connections']),cold_route_canonical_audit_seconds=time.perf_counter()-started,preflight_overhead_seconds=pf['context_bind_seconds']+pf['preflight_seconds']));(out/'receipt.json').write_text(json.dumps(dict(preflight_receipt_sha256=sha(pre/'receipt.json'),source_sha256=sha(Path(__file__)),rows=rows,scope='Actual cold fallback after rejected budget candidate; route/reload/audit timed, prior parsing/preflight separately. No prediction/native import attempted; no speedup claim.'),indent=2)+'\n');print(w,cpd,flush=True)

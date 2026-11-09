"""Verify candidate own-packing reports and old-path coverage differences."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_joint_candidate_details_2026-10-06';base=ROOT/'experiments/mux_retained_joint_quality_gate_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json')and len(r['rows'])==4;rows=[];bindings={}
def key(body,field):return re.search(r'^'+field+r'\s*:\s*(.*?) \(',body,re.M)[1]
def logical(body):return [(m[1],m[2],int(m[3]))for line in body.splitlines()if(m:=re.match(r'^(\S+)\.(inpad|outpad|in|out)\[(\d+)\]\s+\(',line))]
for row in r['rows']:
 w,i=row['width'],row['index'];reload=row['reload'];assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0;assert all(sha(p)==h for p,h in reload['files'].items());work=Path(next(iter(reload['files']))).parent;route=work/'design.route';pred=base/f'w{w}_m{i}/predicted.route';paths=lambda p:{n:sorted(v)for n,v in physical_paths(p).items()if v};assert paths(route)==paths(pred);graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';a=audit(graph,route);assert a['overflow_units']==0 and len(a['connections'])=={8:466,16:936}[w]
 report=work/'report_timing.setup.rpt';old=ROOT/f'experiments/mux_old_aggregated_timing_2026-10-06/w{w}/canonical/report_timing.setup.rpt';bodies=re.findall(r'#Path (\d+)\n(.*?)(?=\n#Path |\Z)',report.read_text(),re.S);assert len(bodies)==w*8;top=bodies[0][1];prior=re.findall(r'#Path (\d+)\n(.*?)(?=\n#Path |\Z)',old.read_text(),re.S);same_endpoint=[(n,b)for n,b in prior if key(b,'Endpoint')==key(top,'Endpoint')];exact=[n for n,b in prior if logical(b)==logical(top)];rows.append(dict(width=w,index=i,cpd_ns=reload['cpd_ns'],startpoint=key(top,'Startpoint'),endpoint=key(top,'Endpoint'),logical_points=logical(top),old_same_endpoint_paths=[dict(rank=int(n),startpoint=key(b,'Startpoint'),logical_points=logical(b))for n,b in same_endpoint],old_exact_logical_path_ranks=exact,physical_connections_checked=len(a['connections'])))
 for p in (report,old,pred,route):bindings[str(p)]=sha(p)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='Four original ownpacking zero-fixup replays,2804 physicalpathpreservation/capacitychecks, fullendpointreportcounts. Old reportedpathcoverage comparison; not proof of unique solecause or exhaustive allfanin timing coverage.'),indent=2)+'\n');print([(x['width'],x['index'],x['startpoint'],x['endpoint'],x['old_exact_logical_path_ranks'])for x in rows])

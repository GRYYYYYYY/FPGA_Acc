"""Original canonical old-layout replay with explicit timing decomposition."""
import json,re,shutil
from pathlib import Path
from pre_route_endpoints import sha
from loaded_native_canonical_reload import canonical_reload
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06';out.mkdir();base=ROOT/'experiments/mux_budget_repair_quality_gate_2026-10-06';receipt=json.loads((base/'receipt.json').read_text());rows=[];inputs={}
for row in receipt['rows']:
 w=row['width'];source=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128';work=out/f'w{w}';work.mkdir()
 for name,target in [('design.blif','design.blif'),('design.net.post_routing','design.net.post_routing'),('design.place','accepted.place'),('design.route','output.route')]:shutil.copyfile(source/name,work/target);inputs[str(source/name)]=sha(source/name)
 oldreport=source/'report_timing.setup.rpt';inputs[str(oldreport)]=sha(oldreport)
 # Original initial CPD comes from retained original-run log, not moved-layout data.
 logs=[p for p in source.glob('*.log') if 'Final critical path delay' in p.read_text(errors='replace')];assert logs
 values={float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',p.read_text())[-1])for p in logs};assert len(values)==1
 for p in logs:inputs[str(p)]=sha(p)
 command=row['native']['command']+['--timing_report_detail','aggregated','--echo_file','on','--echo_dot_timing_graph_node','-1']
 native=dict(width=w,decision='A',command=command,cpd_ns=values.pop(),files={str(p):sha(p)for p in work.iterdir()if p.is_file()})
 result=canonical_reload(native,work,work/'canonical');rows.append(result);print(w,result['cpd_ns'],flush=True)
 (out/'receipt.json').write_text(json.dumps(dict(rows=rows,source_sha256=sha(Path(__file__)),inputs=inputs,scope='Old accepted original layout/route only; original VPR FULL/STA zero-fixup aggregated report.'),indent=2)+'\n')

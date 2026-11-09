"""Authenticate native changed-placement control and all printed physical arcs."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_d32_swapped_place_cold_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());work=Path(p['cwd']);assert r['exit_code']==0 and r['native_success'];assert sha(out/'protocol.json')==r['protocol_sha256'] and sha(root/'tools/trial_gf2_d32_swapped_place_cold.py')==r['source_sha256']
for path,h in r['files_sha256'].items():assert sha(path)==h
for path,h in p['input_sha256'].items():
 if Path(path).name!='design.place':assert sha(path)==h
swapped=root/'experiments/gf2_d32_placement_swap_2026-10-06/swapped.place'
assert sha(swapped)==p['input_sha256'][str(work/'design.place')]
assert [line.split() for line in (work/'design.place').read_text().splitlines()]==[line.split() for line in swapped.read_text().splitlines()]
cmd=p['command'];graph=Path(cmd[cmd.index('--read_rr_graph')+1]);assert sha(graph)==p['graph_sha256'] and sha(cmd[0])==p['binary_sha256'] and sha(cmd[1])==p['architecture_sha256'];log=(work/'run.log').read_text();assert 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log;assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1])==r['cpd_ns'];a=audit(graph,work/'design.route');assert len(a['connections'])==264 and a['overflow_units']==0;result={'receipt_sha256':sha(out/'receipt.json'),'native_FULL_success':True,'cpd_ns':r['cpd_ns'],'native_process_wall_s':r['native_process_wall_s'],'connections':264,'overflow_units':0,'changed_place_token_rows_exact':True,'native_place_whitespace_reformat':True,'scope':'Matched swappedplacement originalVPR coldcontrol plus printedphysicalarc/capacity audit; not predictor timing/1ns success or net speed claim.'};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

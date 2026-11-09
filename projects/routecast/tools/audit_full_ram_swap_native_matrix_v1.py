"""All-case raw route capacity/branch audit and prospective endpoint parity."""
import json,re
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_ram_swap_native_matrix_v1_2026-10-09';D=E/'full_ram_swap_native_audit_v1_2026-10-09';D.mkdir(exist_ok=False)
r=json.loads((B/'receipt.json').read_text())
for p,h in r['bindings'].items():assert sha(p)==h
rows=[];paths=[Path(__file__),B/'receipt.json',R/'tools/stream_native_route_audit.py']
for row in r['results']:
 cid=row['candidate'];folder=B/f'candidate_{cid}';assert row['exit_code']==0
 for p,h in row['files'].items():assert sha(p)==h
 graph=folder/'rr_graph.xml';route=folder/'design.route';assert sha(graph)==sha(E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml')
 expectedplace=E/'full_ram_comb_only_route_v1_2026-10-09/design.place' if cid==0 else E/f'full_ram_swap_candidates_v1_2026-10-09/candidate_{cid}/design.place'
 assert sha(folder/'design.place')==sha(expectedplace)
 result=audit(graph,route);assert result['overflow_units']==0 and result['all_printed_branch_arc_switch_and_union_checks_pass']
 epfile=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json' if cid==0 else E/f'full_ram_swap_candidates_v1_2026-10-09/candidate_{cid}/endpoints.json';ep=json.loads(epfile.read_text());names={int(n):v for n,v in ep['net_names'].items()}
 route_names={int(m[1]):m[2] for m in re.finditer(r'^Net (\d+) \((.*)\)$',route.read_text(),re.M)}
 expected=Counter((names[c['net_id']],c['source'],c['sink']) for c in ep['connections']);actual=Counter((route_names[c['net_id']],c['source'],c['sink']) for c in result['connections']);assert expected==actual and sum(actual.values())==16819
 (D/f'candidate_{cid}.json').write_text(json.dumps(result)+'\n');text=(folder/'route.log').read_text()
 rows.append(dict(candidate=cid,connections=sum(actual.values()),overflow_units=0,native_s=row['native_s'],iterations=int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]),wirelength=int(re.search(r'Total wirelength:\s*(\d+)',text)[1]),cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1])))
 paths.extend([graph,route,folder/'route.log',folder/'design.place',epfile]);print(rows[-1],flush=True)
(D/'verification.json').write_text(json.dumps(dict(passed=True,results=rows,bindings={str(p):sha(p) for p in paths},scope='All native printed branch/arcs/switches/unique-net capacities and full prospective endpoint parity. Timing is engineering architecture/SDC, not independent product requirement; no complete physical initialization/Full functional equivalence or net-benefit evidence.'),indent=2)+'\n')

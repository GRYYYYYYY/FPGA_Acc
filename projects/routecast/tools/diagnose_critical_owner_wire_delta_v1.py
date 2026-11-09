"""Attribute native wirelength to complete unique-NET original RR channel unions."""
import json,re,xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];graph=R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml';xml=ET.parse(graph).getroot();length={}
for n in xml.find('rr_nodes'):
 if n.get('type') not in ('CHANX','CHANY'):continue
 loc=n.find('loc');length[int(n.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
vectors=[('cold',R/'experiments/native_cold_branch_control_v8_2026-10-08/cold/output.route',R/'experiments/native_cold_branch_control_v8_2026-10-08/cold/run.log'),('budget_repaired',R/'experiments/budget_repair_reconciled_dump_v1_2026-10-08/reconciled.route',R/'experiments/budget_repair_reconciled_dump_v1_2026-10-08/reload.log')]
for index in range(4):
 d=R/f'experiments/critical_owner_native_reload_plan{index}_v1_2026-10-08';vectors.append((f'plan{index}',d/'reconciled.route',d/'reload.log'))
bindings={str(graph):sha(graph),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/native_route_ledger_import_compact.py'):sha(R/'tools/native_route_ledger_import_compact.py')};rows=[];values={}
for name,route,log in vectors:
 for p in (route,log):bindings[str(p)]=sha(p)
 pernet={net:sum(length.get(n,0) for n in {n for p in paths for n,s in p}) for net,paths in physical_paths(route).items()};total=sum(pernet.values());printed=int(re.findall(r'Total wirelength:\s*(\d+)',log.read_text())[-1]);assert total==printed;values[name]=pernet;rows.append(dict(mode=name,total=total,printed_total=printed,per_net_wirelength=pernet))
deltas=[]
for index in range(4):
 name=f'plan{index}'
 for reference in ('cold','budget_repaired'):
  assert values[name].keys()==values[reference].keys();changes={n:values[name][n]-values[reference][n] for n in values[name] if values[name][n]!=values[reference][n]};deltas.append(dict(mode=name,reference=reference,total_delta=sum(changes.values()),per_net_delta=changes))
D=R/'experiments/critical_owner_wire_delta_v1_2026-10-08';D.mkdir(exist_ok=False);assert all(sha(p)==h for p,h in bindings.items())
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,all_six_native_wirelength_totals_exactly_recomputed=True,rows=rows,deltas=deltas,scope='Complete printed native channel union geometry accounting; no lower bound/minimum wire or performance proof.'),indent=2)+'\n');print([(x['mode'],x['reference'],x['total_delta'],x['per_net_delta'] if x['reference']=='budget_repaired' else len(x['per_net_delta'])) for x in deltas])

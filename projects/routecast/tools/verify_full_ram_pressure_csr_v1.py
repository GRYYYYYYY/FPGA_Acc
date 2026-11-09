"""Recompute every frozen pressure increment from background ownership."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read,U64
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_pressure_csr_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_length_switch_prediction_v1_2026-10-09'
P=E/'full_ram_frozen_pressure_prediction_v1_2026-10-09'
proof=E/'full_ram_length_switch_csr_verification_v1_2026-10-09/verification.json'
v=json.loads(proof.read_text());assert v['passed']
for p,h in v['bindings'].items():assert sha(p)==h
bgfile=B/'prediction.json';bg=json.loads(bgfile.read_text());graphsha=bg['physical_graph_sha256']
mb,base=read(B/'csr',graphsha);mp,pressure=read(P/'csr',graphsha)
assert base.keys()==pressure.keys()
for field in base:
    if field!='costs':assert base[field]==pressure[field]
assert mb['context_sha256']!=mp['context_sha256']
penalties=[]
for i,n in enumerate(base['node_ids']):
    cap=base['capacities'][i];demand=bg['node_occupancy'].get(str(n),0)
    penalty=(256*max(0,demand-cap+1)+cap-1)//cap if cap>0 and base['types'][i] in (4,5) else 0
    penalties.append(penalty)
changed=0;disabled=0;increments=0
for slot,cost in enumerate(base['costs']):
    penalty=penalties[base['dest_ranks'][slot]]
    expected=U64 if cost==U64 else cost+penalty
    assert pressure['costs'][slot]==expected
    disabled+=cost==U64
    if cost!=U64:changed+=penalty>0;increments+=penalty
out=dict(passed=True,all_physical_arcs_checked=mb['edges'],changed_arc_costs=changed,disabled_arcs=disabled,
    total_arc_cost_increment=increments,penalized_channel_nodes=sum(x>0 for x in penalties),
    baseline_context=mb['context_sha256'],pressure_context=mp['context_sha256'],
    bindings={str(p):sha(p) for p in [Path(__file__),proof,bgfile,B/'csr/manifest.json',P/'csr/manifest.json',P/'protocol.json']},
    scope='All CSR topology/node metadata unchanged, exact frozen-background alpha256 increments; queried net is included, so occupied-at-capacity channels get positive penalty. Cost payload changes distinguish contexts even though legacy mode string remains rr_length_switch. No target labels, measured speedup or pressure calibration.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(changed,out['penalized_channel_nodes'],mp['context_sha256'])

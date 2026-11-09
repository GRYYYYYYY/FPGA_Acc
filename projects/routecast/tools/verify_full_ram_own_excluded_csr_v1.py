"""Recompute every frozen pressure increment from background ownership."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read,U64
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_own_excluded_csr_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_length_switch_prediction_v1_2026-10-09'
P=E/'full_ram_own_excluded_channel_prediction_v1_2026-10-09'
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
from array import array
import hashlib,sys
from collections import defaultdict,Counter
reduced=array('Q');reduced.frombytes((P/'csr/own_reduction.bin').read_bytes())
if sys.byteorder!='little':reduced.byteswap()
assert len(reduced)==mb['nodes']
for i,n in enumerate(base['node_ids']):
    cap=base['capacities'][i];d=bg['node_occupancy'].get(str(n),0)
    lower=(256*max(0,d-cap)+cap-1)//cap if cap>0 and base['types'][i] in (4,5) and d else 0
    assert reduced[i]==penalties[i]-lower
edge_dest=dict(zip(base['edge_ids'],(base['node_ids'][r] for r in base['dest_ranks'])))
net_nodes=defaultdict(set)
for c in bg['connections']:
    net_nodes[c['net_id']].update([c['source'],*(edge_dest[e] for e in c['physical_edge_ids'])])
counts=Counter(n for nodes in net_nodes.values() for n in nodes)
assert {str(n):v for n,v in counts.items()}==bg['node_occupancy']
identity={str(net):hashlib.sha256(json.dumps(dict(csr=mp['context_sha256'],reduction_sha256=sha(P/'csr/own_reduction.bin'),own_nodes=sorted(nodes)),sort_keys=True).encode()).hexdigest() for net,nodes in net_nodes.items()}
(D/'effective_contexts.json').write_text(json.dumps(identity,sort_keys=True)+'\n')
out=dict(passed=True, own_reduction_nodes_verified=len(reduced), net_owner_sets_verified=len(identity), effective_contexts_sha256=sha(D/'effective_contexts.json'), own_reduction_sha256=sha(P/'csr/own_reduction.bin'),all_physical_arcs_checked=mb['edges'],changed_arc_costs=changed,disabled_arcs=disabled,
    total_arc_cost_increment=increments,penalized_channel_nodes=sum(x>0 for x in penalties),
    baseline_context=mb['context_sha256'],pressure_context=mp['context_sha256'],
    bindings={str(p):sha(p) for p in [Path(__file__),proof,bgfile,B/'csr/manifest.json',P/'csr/manifest.json',P/'protocol.json',P/'csr/own_reduction.bin',R/'tools/csr_consumer/net_pressure_main_v1.cpp',R/'build/routecast_net_pressure_v1']},
    scope='All CSR topology/node metadata unchanged, exact frozen-background alpha256 increments; Retain-own base payload plus independently checked own reduction and full net-node sets define net-specific effective costs; all owner sets match unique-net ledger. Context identities recorded separately. Cost payload changes distinguish contexts even though legacy mode string remains rr_length_switch. No target labels, measured speedup or pressure calibration.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(changed,out['penalized_channel_nodes'],mp['context_sha256'])

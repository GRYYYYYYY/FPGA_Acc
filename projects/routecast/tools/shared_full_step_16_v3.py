"""Independent physical and Fraction replay of diagnostic relaxation witnesses."""
import json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_shared_full_stage_4_v3_2026-10-08'
r=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
m=json.loads((E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json').read_text());inv=read(m['inputs']['graph']['path'],m['graph_sha256']);edges={eid:arc for arc,eid in inv.physical.arcs.items()};counts=Counter();minimal=Counter();found=0
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json'
 queries={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};budgets={q['connection_id']:F(*q['exact_delay_s']) for q in json.loads((E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json').read_text())}
 for event in json.loads((D/f'step_{step}.json').read_text())['events']:
  for a in event['attempts']:
   probes=a.get('diagnostic_relaxations',[]);success=[]
   for p in probes:
    mask=int(p['relax_capacity'])+2*int(p['relax_parents'])+4*int(p['relax_wire']);counts[(mask,p['status'])]+=1
    if p['status']!='FOUND':continue
    success.append(mask);found+=1;q=queries[a['connection_id']];node=q['source'];rr,cc=inv.classes[inv.node_classes[node]];delay=rr*cc/2;seen={node}
    for eid in p['physical_edge_ids']:
     u,v,s=edges[eid];assert u==node and v not in seen and inv.arc_multiplicities[(u,v,s)]==1;seen.add(v);node=v
     rr,cc=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+rr/2)*cc+td
    assert node==q['sink'] and delay<=budgets[a['connection_id']]
   for mask in success:
    if not any(other!=mask and other&mask==other for other in success):minimal[mask]+=1
out=dict(bindings={str(p):sha(p) for p in (D/'receipt.json',Path(__file__))},independent_found_witnesses=found,counts={str(k):v for k,v in counts.items()},minimal_successful_relaxation_masks=dict(minimal),mask_definition={'1':'outside capacity','2':'sameNET parents','4':'wire bound'},scope='Relaxed paths diagnostic only, never installed. Physical exact budget witnesses verified; no uniqueness of cause or global infeasibility claim.')
(D/'probe_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

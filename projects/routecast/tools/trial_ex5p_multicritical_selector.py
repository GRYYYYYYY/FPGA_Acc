"""Validate deterministic multi-path target/owner rule against prior staged evidence."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from select_multicritical_targets import select_targets
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_multicritical_selector_v2_2026-10-06';out.mkdir();files={name:root/'experiments'/directory/filename for name,directory,filename in [('trace','ex5p_top3_packed_pins_2026-10-06','receipt.json'),('paths','ex5p_top3_timing_arcs_2026-10-06','receipt.json'),('inputs','ex5p_top3_rr_bindings_2026-10-06','receipt.json'),('outputs','ex5p_top3_output_bindings_2026-10-06','receipt.json'),('minima','ex5p_top3_empty_delay_2026-10-06','receipt.json'),('candidate','ex5p_critical_coupled2_2026-10-06','receipt.json')]};data={k:json.loads(p.read_text()) for k,p in files.items()};p={'inputs_sha256':{str(f):sha(f) for f in files.values()},'selector_source_sha256':sha(root/'tools/select_multicritical_targets.py'),'top_k':3,'selection':'Largest positive certified old-minus-empty-minimum integer delay per frozen path, tie smaller connectionID; stable pathrank dedup. Unbound internal pins retained explicitly. Retrospective rule validation, not prospective unseen-family outcome.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');r=select_targets(data['paths']['predicted_top3_paths'],data['inputs']['bindings'],data['outputs']['bindings'],data['minima']['records'],3,internal_bindings=data['trace']['bindings']);assert r['target_connection_ids']==[1890,1888,726];ep=json.loads((root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json').read_text());g=Path(ep['inputs']['graph']['path']);assert sha(g)==data['candidate']['graph_sha256'];xml=ET.parse(g).getroot();edges=list(xml.find('rr_edges'));caps={int(n.get('id')):int(n.get('capacity')) for n in xml.find('rr_nodes')};unions=defaultdict(set)
for rec in data['candidate']['records']:
 unions[rec['net_id']].add(rec['source'])
 for eid in rec['answer']['physical_edge_ids']:unions[rec['net_id']].add(int(edges[eid].get('sink_node')))
minima={x['query']['connection_id']:x for x in data['minima']['records']};nets=set();owners={}
for cid in r['target_connection_ids']:
 x=minima[cid];q=x['query'];nets.add(q['net_id']);nodes={q['source']}|{int(edges[eid].get('sink_node')) for eid in x['physical_edge_ids']};blocked={n:sorted(net for net,ns in unions.items() if net!=q['net_id'] and n in ns) for n in nodes};blocked={n:rows for n,rows in blocked.items() if len(rows)>=caps[n]};owners[cid]=blocked;nets.update(net for rows in blocked.values() for net in rows)
prior=json.loads((root/'experiments/ex5p_top3_joint_repair_2026-10-06/protocol.json').read_text());assert sorted(nets)==prior['affected_nets'];assert {str(cid):{str(n):rows for n,rows in ns.items()} for cid,ns in owners.items()}==prior['blocked_owners'];r.update({'release_net_ids':sorted(nets),'released_connection_ids':[x['connection_id'] for x in data['candidate']['records'] if x['net_id'] in nets],'blocked_owners':owners,'graph_sha256':sha(g),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))});assert len(r['released_connection_ids'])==121;(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('selected',r['target_connection_ids'],'NETs',len(nets),'connections',len(r['released_connection_ids']))

rejected=[]
for name,inputs,outputs in [('missing_external_input',[x for x in data['inputs']['bindings'] if x['connection_id']!=1648],data['outputs']['bindings']),('missing_terminal',data['inputs']['bindings'],data['outputs']['bindings'][1:])]:
 try:select_targets(data['paths']['predicted_top3_paths'],inputs,outputs,data['minima']['records'],3,internal_bindings=data['trace']['bindings'])
 except ValueError:rejected.append(name)
 else:raise AssertionError('incomplete cohort silently accepted')
assert len(rejected)==2
(out/'contract.json').write_text(json.dumps({'missing_binding_rejections':rejected,'internal_pins_require_explicit_packed_trace':True},indent=2)+'\n')

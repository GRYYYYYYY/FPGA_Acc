"""Independent selected on/off native archive checks, without rerouting."""
from collections import Counter
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha,extract,placements
from audit_native_route import audit
from native_node_labels import node_labels
from rr_graph import read_rr_graph

parent=Path('experiments/prospective_local_feedback_v3_2026-10-04')
out=Path('experiments/prospective_feedback_audit_2026-10-04')
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());decision=json.loads((parent/'decision.json').read_text());result=json.loads((parent/'receipt.json').read_text());off=json.loads((parent/'off_result.json').read_text())
assert off['decision_sha256']==result['decision_sha256']==sha(parent/'decision.json')
files=[parent/'protocol.json',parent/'decision.json',parent/'receipt.json',parent/'off_result.json']
for mode in ('selected_native','off_native'):files += [parent/mode/'receipt.json',parent/mode/'vpr_stdout.txt']
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'scope':'independent archived native endpoint/arc/switch/net-union/placement identity audit; no new performance run','inputs':{str(f):sha(f) for f in files},'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
graph=Path(p['inputs']['graph']['path']);net=Path(p['inputs']['net']['path']);g=read_rr_graph(graph);rows=[]
for mode,cid,folder in [('on',decision['selected_candidate'],'selected_native'),('off',decision['off_selected_candidate'],'off_native')]:
    receipt=json.loads((parent/folder/'receipt.json').read_text());route=Path(receipt['final_route']['path']);place=route.with_suffix('.place');original=Path(p['placements'][str(cid)]['path'])
    assert sha(route)==receipt['final_route']['sha256'];assert sha(parent/folder/'vpr_stdout.txt')==receipt['log_sha256']
    assert placements(place,sha(net))==placements(original,sha(net))
    ep,_=extract(net,place,graph);labels=node_labels(g,route,sha(place));checked=audit(graph,route)
    wanted=Counter((r['net_id'],r['source'],r['sink']) for r in ep['connections']);actual=Counter((r['net_id'],r['source'],r['sink']) for r in checked['connections'])
    assert wanted==actual;assert not checked['overflow_nodes']
    users={}
    for r in checked['connections']:
        for n in {r['source']}|{g.edges[e].sink for e in r['edge_ids']}:users.setdefault(str(n),set()).add(r['net_id'])
    assert labels=={n:len(v) for n,v in users.items()}
    (out/f'{mode}_native_audit.json').write_text(json.dumps(checked)+'\n')
    row={'mode':mode,'candidate':cid,'connections':sum(actual.values()),'graph_sha256':g.sha256,'route_sha256':sha(route),'canonical_place_sha256':sha(place),'proposal_place_sha256':sha(original),'exact_endpoint_multiset':True,'all_arc_switch_union_checks':True,'overflow_nodes':0};rows.append(row);print(json.dumps(row),flush=True)
for f,digest in protocol['inputs'].items():assert sha(f)==digest
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_checks_passed':True},indent=2)+'\n')

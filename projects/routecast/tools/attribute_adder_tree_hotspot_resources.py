"""Post-hoc exact channel/node/net contributions for frozen maximum-case hot bins."""
import json
import shutil
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from audit_native_route import NET,NODE
from prepared_csr import read
from pre_route_endpoints import sha


def main():
    base=Path('experiments');design='adder_tree_3L_128bits'
    diagnosis=base/'adder_tree_family_hotspot_diagnosis_2026-10-06';dr=json.loads((diagnosis/'receipt.json').read_text());assert sha(diagnosis/'report.json')==dr['report_sha256']
    diagnostic=json.loads((diagnosis/'report.json').read_text());hot=next(r for r in diagnostic['records'] if r['design']==design and r['model']=='sparse_reset')
    keys=sorted({r['id'] for r in hot['native_top_rows']+hot['prediction_top_rows']})
    predroot=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset';pr=json.loads((predroot/'receipt.json').read_text());pp=json.loads((predroot/'protocol.json').read_text())
    assert sha(predroot/'prediction.json')==pr['prediction_sha256'] and sha(predroot/'protocol.json')==pr['protocol_sha256']
    native=base/'adder_tree_family_native_path_audit_2026-10-06'/design;nr=json.loads((native/'receipt.json').read_text());np=json.loads((native/'protocol.json').read_text());assert sha(native/'protocol.json')==nr['protocol_sha256']
    assert nr['physical_checks_pass'] and nr['retained_endpoint_multiset_exact']
    truthpath=native/'physical_branches.json';assert sha(truthpath)==nr['outputs']['physical_branches.json']
    pred=json.loads((predroot/'prediction.json').read_text());truth=json.loads(truthpath.read_text());ep=json.loads(Path(pp['inputs']['endpoints']['path']).read_text())
    graph=pp['inputs']['graph'];route=np['inputs']['evaluator_route'];assert np['inputs']['rr_graph']==graph
    assert sha(graph['path'])==graph['sha256'] and sha(route['path'])==route['sha256']
    wanted={key:tuple(key.split(',')) for key in keys};members=defaultdict(list);caps={};stack=[]
    for event,node in ET.iterparse(graph['path'],events=('start','end')):
        if event=='start':stack.append(node);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if node.tag=='node' and parent=='rr_nodes':
            kind=node.get('type');cap=int(node.get('capacity'))
            if kind in ('CHANX','CHANY') and cap:
                loc=node.find('loc');seg=node.find('segment').get('segment_id');nid=int(node.get('id'))
                for key,(x,y,axis,segment) in wanted.items():
                    if axis==kind and segment==seg and int(loc.get('xlow'))<=int(x)<=int(loc.get('xhigh')) and int(loc.get('ylow'))<=int(y)<=int(loc.get('yhigh')):
                        members[key].append(nid);caps[nid]=cap
            stack[-2].remove(node);node.clear()
        if node.tag=='rr_nodes':break
        stack.pop()
    selected=set(caps);native_owners=defaultdict(set);net=None;names={}
    with Path(route['path']).open() as f:
        for line in f:
            match=NET.match(line)
            if match:net=int(match[1]);names[net]=match[2];continue
            match=NODE.match(line)
            if match and int(match[1]) in selected:
                assert net is not None;native_owners[int(match[1])].add(net)
    for nid in selected:assert len(native_owners[nid])==truth['node_occupancy'].get(str(nid),0)
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design;receipt=json.loads((prepared/'receipt.json').read_text());assert sha(prepared/'csr/manifest.json')==receipt['manifest_sha256']==pp['csr_manifest_sha256']
    m,f=read(prepared/'csr',graph['sha256']);dest_by_edge=[0]*m['edges']
    for slot,eid in enumerate(f['edge_ids']):dest_by_edge[eid]=f['node_ids'][f['dest_ranks'][slot]]
    pred_owners=defaultdict(set)
    for row in pred['connections']:
        assert row['physical_edge_ids'] is not None
        used={row['source'],*(dest_by_edge[eid] for eid in row['physical_edge_ids'])}
        for nid in used&selected:pred_owners[nid].add(row['net_id'])
    for nid in selected:assert len(pred_owners[nid])==pred['node_occupancy'].get(str(nid),0)
    maps=base/'adder_tree_family_evaluation_2026-10-06'/design/'sparse_reset/spatial_maps.json';values=json.loads(maps.read_text())
    rows=[]
    for key in keys:
        capacity=sum(caps[nid] for nid in members[key]);assert capacity>0
        pt=Counter(net for nid in members[key] for net in pred_owners[nid]);nt=Counter(net for nid in members[key] for net in native_owners[nid])
        assert float(Fraction(sum(pt.values()),capacity))==values['prediction'][key]
        assert float(Fraction(sum(nt.values()),capacity))==values['native'][key]
        nets=set(pt)|set(nt)
        assert all(names[net]==ep['net_names'][str(net)] for net in nets)
        contributors=[{'net_id':net,'name':names[net],'prediction_node_touches':pt[net],'native_node_touches':nt[net],'delta_native_minus_prediction':nt[net]-pt[net]} for net in sorted(nets,key=lambda n:(-abs(nt[n]-pt[n]),n))]
        rows.append({'id':key,'capacity':capacity,'resource_count':len(members[key]),'prediction_touches':sum(pt.values()),'native_touches':sum(nt.values()),'prediction_score':values['prediction'][key],'native_score':values['native'][key],'net_contributions':contributors})
    assert sha(graph['path'])==graph['sha256'] and sha(route['path'])==route['sha256']
    out=base/'adder_tree_max_hotspot_resource_attribution_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
    report={'diagnosis_report_sha256':sha(diagnosis/'report.json'),'prediction_receipt_sha256':sha(predroot/'receipt.json'),'native_receipt_sha256':sha(native/'receipt.json'),'maps_sha256':sha(maps),'source_sha256':sha(__file__),'bins':rows,'selected_resources':len(selected),'all_selected_node_owner_counts_exact':True,'all_bin_scores_reconstructed_exact':True,'scope':'post-hoc native-versus-prediction local occupancy/net attribution, not causal or budget/repair proof'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'bins':len(rows),'selected_resources':len(selected)},indent=2)+'\n')
    print(json.dumps({'bins':len(rows),'resources':len(selected),'native_top_touch_totals':[[r['id'],r['prediction_touches'],r['native_touches']] for r in rows if r['id'] in {v['id'] for v in hot['native_top_rows']}]}),flush=True)


if __name__=='__main__':main()

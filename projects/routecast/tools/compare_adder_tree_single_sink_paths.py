"""Post-hoc native vs frozen shortest-cost paths for twelve single-sink nets."""
import json
import shutil
from pathlib import Path
from audit_native_route import NET,NODE
from prepared_csr import read
from pre_route_endpoints import sha


def main():
    base=Path('experiments');design='adder_tree_3L_128bits'
    cohort=base/'adder_tree_max_hotspot_fanout_diagnosis_2026-10-06/report.json';selected=json.loads(cohort.read_text());nets={r['net_id'] for r in selected['nets']};assert len(nets)==12 and all(r['fanout']==1 for r in selected['nets'])
    root=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset';p=json.loads((root/'protocol.json').read_text());r=json.loads((root/'receipt.json').read_text());assert sha(root/'prediction.json')==r['prediction_sha256'] and sha(root/'protocol.json')==r['protocol_sha256']
    native=base/'adder_tree_family_native_path_audit_2026-10-06'/design;np=json.loads((native/'protocol.json').read_text());nr=json.loads((native/'receipt.json').read_text());assert sha(native/'protocol.json')==nr['protocol_sha256'] and nr['physical_checks_pass']
    route=np['inputs']['evaluator_route'];assert sha(route['path'])==route['sha256'];assert np['inputs']['rr_graph']==p['inputs']['graph']
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design;assert sha(prepared/'csr/manifest.json')==p['csr_manifest_sha256']
    m,f=read(prepared/'csr',p['inputs']['graph']['sha256']);assert all(i==n for i,n in enumerate(f['node_ids']))
    native_nodes={n:[] for n in nets};net=None
    with Path(route['path']).open() as stream:
        for line in stream:
            match=NET.match(line)
            if match:net=int(match[1]);continue
            match=NODE.match(line)
            if match and net in nets:native_nodes[net].append((int(match[1]),match[2],int(match[3])))
    pred={v['net_id']:v for v in json.loads((root/'prediction.json').read_text())['connections'] if v['net_id'] in nets}
    needed={eid for row in pred.values() for eid in row['physical_edge_ids']};slots={eid:slot for slot,eid in enumerate(f['edge_ids']) if eid in needed}
    def metrics(nodes,edge_slots):
        span=sum(max(f['xhigh'][n]-f['xlow'][n],f['yhigh'][n]-f['ylow'][n])+1 for n in set(nodes) if f['types'][n] in (4,5))
        return {'hops':len(edge_slots),'channel_union_span':span,'additive_cost':sum(f['costs'][slot] for slot in edge_slots)}
    rows=[]
    for net in sorted(nets):
        source=pred[net]['source'];sink=pred[net]['sink'];nodes=native_nodes[net]
        assert nodes[0][0]==source and nodes[-1][0]==sink and sum(kind=='SINK' for _,kind,_ in nodes)==1
        assert len({n for n,_,_ in nodes})==len(nodes),'single-sink printed path repeats'
        native_slots=[]
        for (a,_,switch),(b,_,_) in zip(nodes,nodes[1:]):
            matches=[slot for slot in range(f['row_offsets'][a],f['row_offsets'][a+1]) if f['dest_ranks'][slot]==b and f['switch_ids'][slot]==switch]
            assert matches;native_slots.append(min(matches,key=lambda slot:f['edge_ids'][slot]))
        ps=[slots[eid] for eid in pred[net]['physical_edge_ids']];pn=[source]+[f['dest_ranks'][slot] for slot in ps]
        assert pn[-1]==sink
        pm=metrics(pn,ps);nm=metrics([n for n,_,_ in nodes],native_slots)
        assert pm['additive_cost']<=nm['additive_cost'],'shortest cost claim contradicted'
        rows.append({'net_id':net,'name':next(v['name'] for v in selected['nets'] if v['net_id']==net),'prediction':pm,'native':nm,'native_cost_minus_prediction':nm['additive_cost']-pm['additive_cost'],'native_node_ids':[n for n,_,_ in nodes],'prediction_node_ids':pn})
    assert sha(route['path'])==route['sha256']
    out=base/'adder_tree_max_single_sink_path_comparison_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
    report={'cohort_sha256':sha(cohort),'prediction_receipt_sha256':sha(root/'receipt.json'),'native_receipt_sha256':sha(native/'receipt.json'),'csr_manifest_sha256':p['csr_manifest_sha256'],'source_sha256':sha(__file__),'rows':rows,'scope':'post-hoc twelve single-sink paths under frozen additive length-switch objective; no exact electrical/native STA/repair claim'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'nets':12},indent=2)+'\n')
    print(json.dumps({'nets':12,'native_strictly_more_additive_cost':sum(row['native_cost_minus_prediction']>0 for row in rows),'native_longer_span':sum(row['native']['channel_union_span']>row['prediction']['channel_union_span'] for row in rows),'rows':[{'net':row['net_id'],'prediction':row['prediction'],'native':row['native']} for row in rows]}),flush=True)


if __name__=='__main__':main()

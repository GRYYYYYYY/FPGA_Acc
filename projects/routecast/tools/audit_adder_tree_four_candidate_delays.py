"""Four native-occupancy-compatible short paths: joint capacity and original XML RC."""
import json
import shutil
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
from selected_path_budgets import budgets
from streaming_prediction_audit import Edges
from prepared_csr import read


def main():
    start=time.monotonic();base=Path('experiments');design='adder_tree_3L_128bits'
    caproot=base/'adder_tree_max_single_sink_capacity_counterfactual_2026-10-06'
    cap=json.loads((caproot/'report.json').read_text());assert sha(caproot/'report.json')==json.loads((caproot/'receipt.json').read_text())['report_sha256']
    nets={row['net_id'] for row in cap['single_net_results'] if row['fits_original_native_capacity']};assert nets=={2453,2695,2797,2810}
    predroot=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset';pr=json.loads((predroot/'receipt.json').read_text());pp=json.loads((predroot/'protocol.json').read_text());assert sha(predroot/'prediction.json')==pr['prediction_sha256']
    candidates=[row for row in json.loads((predroot/'prediction.json').read_text())['connections'] if row['net_id'] in nets];assert len(candidates)==4
    native=base/'adder_tree_family_native_path_audit_2026-10-06'/design;np=json.loads((native/'protocol.json').read_text());nr=json.loads((native/'receipt.json').read_text());assert sha(native/'receipt.json')==cap['native_receipt_sha256']
    assert sha(native/'protocol.json')==nr['protocol_sha256'] and nr['physical_checks_pass']
    route=np['inputs']['evaluator_route'];graph_info=pp['inputs']['graph'];assert graph_info==np['inputs']['rr_graph']
    assert sha(route['path'])==route['sha256'] and sha(graph_info['path'])==graph_info['sha256']
    printed={};unions={};net=None
    with Path(route['path']).open() as stream:
        for line in stream:
            match=NET.match(line)
            if match:net=int(match[1]);unions.setdefault(net,set());continue
            match=NODE.match(line)
            if match:
                nid=int(match[1]);unions[net].add(nid)
                if net in nets:printed.setdefault(net,[]).append((nid,match[2],int(match[3])))
    wanted_pairs=set();pairs={}
    for row in candidates:
        nodes=printed[row['net_id']];assert nodes[0][0]==row['source'] and nodes[-1][0]==row['sink'] and len({n for n,_,_ in nodes})==len(nodes)
        pairs[row['connection_id']]=[(a,b,switch) for (a,_,switch),(b,_,_) in zip(nodes,nodes[1:])];wanted_pairs.update(pairs[row['connection_id']])
    wanted={eid for row in candidates for eid in row['physical_edge_ids']};records={};pair_ids={};count=0;stack=[]
    for event,element in ET.iterparse(graph_info['path'],events=('start','end')):
        if event=='start':stack.append(element);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if (element.tag,parent)==('edge','rr_edges'):
            triple=(int(element.get('src_node')),int(element.get('sink_node')),int(element.get('switch_id')))
            if triple in wanted_pairs and triple not in pair_ids:pair_ids[triple]=count;wanted.add(count)
            if count in wanted:records[count]=SimpleNamespace(source=triple[0],sink=triple[1],switch_id=triple[2])
            count+=1
        if parent in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(element);element.clear()
        stack.pop()
    assert set(pair_ids)==wanted_pairs and set(records)==wanted
    originals=[{**row,'physical_edge_ids':[pair_ids[pair] for pair in pairs[row['connection_id']]]} for row in candidates]
    wanted_nodes={r['source'] for r in candidates}|{r['sink'] for r in candidates}|{n for edge in records.values() for n in (edge.source,edge.sink)}
    nodes={};switches={};stack=[]
    for event,element in ET.iterparse(graph_info['path'],events=('start','end')):
        if event=='start':stack.append(element);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if (element.tag,parent)==('node','rr_nodes') and int(element.get('id')) in wanted_nodes:
            timing=element.find('timing');assert timing is not None and 'R' in timing.attrib and 'C' in timing.attrib
            nodes[int(element.get('id'))]=SimpleNamespace(timing=tuple(timing.attrib.items()))
        elif (element.tag,parent)==('switch','switches'):switches[int(element.get('id'))]=ET.tostring(element,encoding='unicode')
        if parent in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(element);element.clear()
        stack.pop()
    assert set(nodes)==wanted_nodes
    graph=SimpleNamespace(nodes=nodes,edges=Edges(records,count),switches=switches)
    before=budgets(graph,originals);after=budgets(graph,candidates)
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design
    assert sha(prepared/'csr/manifest.json')==pp['csr_manifest_sha256']
    m,f=read(prepared/'csr',graph_info['sha256'])
    truthpath=native/'physical_branches.json';assert sha(truthpath)==nr['outputs']['physical_branches.json']
    original_occupancy=Counter(n for used in unions.values() for n in used);assert original_occupancy==Counter({int(k):v for k,v in json.loads(truthpath.read_text())['node_occupancy'].items()})
    for row in candidates:unions[row['net_id']]={row['source']}|{records[eid].sink for eid in row['physical_edge_ids']}
    joint=Counter(n for used in unions.values() for n in used)
    overflow=sum(max(0,v-f['capacities'][n]) for n,v in joint.items())
    values=[{'net_id':row['net_id'],'connection_id':row['connection_id'],'native_exact_delay':[before[row['connection_id']].numerator,before[row['connection_id']].denominator],'candidate_exact_delay':[after[row['connection_id']].numerator,after[row['connection_id']].denominator],'within_native_path_budget':after[row['connection_id']]<=before[row['connection_id']]} for row in candidates]
    assert sha(route['path'])==route['sha256'] and sha(graph_info['path'])==graph_info['sha256']
    out=base/'adder_tree_four_candidate_exact_delay_gate_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
    result={'capacity_report_sha256':sha(caproot/'report.json'),'prediction_receipt_sha256':sha(predroot/'receipt.json'),'native_receipt_sha256':sha(native/'receipt.json'),'graph':graph_info,'source_sha256':sha(__file__),'values':values,'joint_overflow_units':overflow,'exact_budget_pass':sum(v['within_native_path_budget'] for v in values),'selected_nodes':len(nodes),'selected_edges':len(records),'wall_s':time.monotonic()-start,'repair_committed':False,'scope':'four post-hoc paths, independent original XML exact path RC and full native union capacity; not native STA/pin assignment/nonconfigurable or QoR certificate'}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'joint_overflow_units':overflow,'exact_budget_pass':result['exact_budget_pass']},indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('values','joint_overflow_units','exact_budget_pass','selected_nodes','selected_edges','wall_s')}),flush=True)


if __name__=='__main__':main()

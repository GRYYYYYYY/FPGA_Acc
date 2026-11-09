"""Selected original-XML exact budgets without full RR edge/node objects."""
import json,time
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
from selected_path_budgets import budgets
from streaming_prediction_audit import Edges
from pre_route_endpoints import sha

def run():
    base=Path('experiments');out=base/'conv_layer_expanded_owner_closure_exact_budgets_2026-10-06'
    parent=base/'conv_layer_length_switch_prediction_v2_2026-10-06';audit_root=Path(str(parent)+'_physical_audit');frontier=base/'conv_layer_expanded_owner_closure_2026-10-06/report.json'
    ar=json.loads((audit_root/'receipt.json').read_text());ap=json.loads((audit_root/'protocol.json').read_text())
    assert ar['protocol_sha256']==sha(audit_root/'protocol.json') and ar['result']['all_physical_and_union_checks_passed']
    selection=json.loads(frontier.read_text());prediction=json.loads((parent/'prediction.json').read_text())
    assert sha(parent/'prediction.json')==selection['prediction_sha256']==ap['inputs']['prediction']['sha256']
    ids=set(selection['whole_net_connection_ids']);nets=set(selection['affected_net_ids'])
    rows=[r for r in prediction['connections'] if r['connection_id'] in ids]
    assert len(rows)==len(ids) and {r['net_id'] for r in rows}==nets
    assert {r['connection_id'] for r in prediction['connections'] if r['net_id'] in nets}==ids
    bindings={str(frontier):sha(frontier),str(parent/'prediction.json'):sha(parent/'prediction.json')}
    out.mkdir()
    wanted={e for r in rows for e in r['physical_edge_ids']};records={};count=0;path=ap['inputs']['graph']['path']
    protocol={'inputs':ap['inputs'],'selection_sha256':bindings,'physical_receipt_sha256':sha(audit_root/'receipt.json'),'source_sha256':sha(__file__),'model':'exact serialized buffered zero-Cinternal path RC; includes source RC/2; no native labels, no integer rounding','scope':'owner-closure original predictor path budgets only; not tree branching load or native STA'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
    for phase in (0,1):
        stack=[]
        if phase:nodes={};switches={};wanted_nodes={r['source'] for r in rows}|{r['sink'] for r in rows}|{n for e in records.values() for n in (e.source,e.sink)}
        for event,e in ET.iterparse(path,events=('start','end')):
            if event=='start':stack.append(e);continue
            parent=stack[-2].tag if len(stack)>1 else None
            if phase==0 and e.tag=='edge' and parent=='rr_edges':
                if count in wanted:records[count]=SimpleNamespace(source=int(e.get('src_node')),sink=int(e.get('sink_node')),switch_id=int(e.get('switch_id')))
                count+=1
            elif phase==1 and e.tag=='node' and parent=='rr_nodes' and int(e.get('id')) in wanted_nodes:
                timing=e.find('timing');assert timing is not None and 'R' in timing.attrib and 'C' in timing.attrib
                nodes[int(e.get('id'))]=SimpleNamespace(timing=tuple(timing.attrib.items()))
            elif phase==1 and e.tag=='switch' and parent=='switches':
                sid=int(e.get('id'));assert sid not in switches;switches[sid]=ET.tostring(e,encoding='unicode')
            if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):stack[-2].remove(e);e.clear()
            stack.pop()
        if phase==0:assert set(records)==wanted
    assert set(nodes)==wanted_nodes
    graph=SimpleNamespace(nodes=nodes,edges=Edges(records,count),switches=switches)
    values=budgets(graph,rows);assert len(values)==len(ids)
    assert sha(path)==ap['inputs']['graph']['sha256'] and all(sha(p)==h for p,h in bindings.items())
    result=[{'connection_id':cid,'delay_seconds_numerator':d.numerator,'delay_seconds_denominator':d.denominator} for cid,d in sorted(values.items())]
    (out/'budgets.json').write_text(json.dumps(result)+'\n')
    r={'connections':len(values),'selected_nodes':len(nodes),'selected_edges':len(records),'all_switches':len(switches),'protocol_sha256':sha(out/'protocol.json'),'budgets_sha256':sha(out/'budgets.json'),'wall_s':time.monotonic()-start,'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

if __name__=='__main__':run()

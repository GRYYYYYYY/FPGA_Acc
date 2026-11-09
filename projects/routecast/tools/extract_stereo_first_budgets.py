"""Selected original-XML exact budgets without full RR edge/node objects."""
import json,time
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
from selected_path_budgets import budgets
from streaming_prediction_audit import Edges
from pre_route_endpoints import sha

def run():
    base=Path('experiments/stereo_prospective_validation_2026-10-05')
    out=base/'first_high_fanout_exact_budgets';out.mkdir()
    audit_root=base/'first_high_fanout_physical_audit'
    ar=json.loads((audit_root/'receipt.json').read_text());ap=json.loads((audit_root/'protocol.json').read_text())
    assert ar['protocol_sha256']==sha(audit_root/'protocol.json') and ar['physical_audit']['all_physical_and_union_checks_passed']
    snapshots=[json.loads(Path(p).read_text()) for p in ap['snapshots']]
    assert all(sha(p)==h for p,h in ap['snapshots'].items())
    rows=[{**r,'physical_edge_ids':s['net_result']['result']['paths'][str(r['sink'])]} for s in snapshots for r in s['connections']]
    wanted={e for r in rows for e in r['physical_edge_ids']};records={};count=0;path=ap['graph']['path']
    protocol={'inputs':ap,'physical_receipt_sha256':sha(audit_root/'receipt.json'),'source_sha256':sha(__file__),'model':'exact serialized buffered zero-Cinternal path RC; includes source RC/2; no native labels, no integer rounding','scope':'486 original predictor path budgets only; not tree branching load or native STA'}
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
    values=budgets(graph,rows);assert len(values)==486
    assert sha(path)==ap['graph']['sha256'] and all(sha(p)==h for p,h in ap['snapshots'].items())
    result=[{'connection_id':cid,'delay_seconds_numerator':d.numerator,'delay_seconds_denominator':d.denominator} for cid,d in sorted(values.items())]
    (out/'budgets.json').write_text(json.dumps(result)+'\n')
    r={'connections':len(values),'selected_nodes':len(nodes),'selected_edges':len(records),'all_switches':len(switches),'protocol_sha256':sha(out/'protocol.json'),'budgets_sha256':sha(out/'budgets.json'),'wall_s':time.monotonic()-start,'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

if __name__=='__main__':run()

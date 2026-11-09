"""Quantify packed per-edge ps rounding on actual candidate paths from XML local RC values."""
import argparse,csv,json,struct
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from persistent_vpr_timing import sha
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pair',type=Path);p.add_argument('output',type=Path);a=p.parse_args();pair=a.pair.resolve();m=json.loads(pair.read_text());mode,=m['modes'];base=pair.parent
    graph=Path(m['case'])/'rr_graph.xml';arch=Path(m['case'])/'architecture.xml';switches=ET.parse(arch).getroot().findall('./switchlist/switch')
    assert switches and all(s.attrib['type']=='mux' and float(s.attrib.get('Cinternal','0'))==0 for s in switches)
    tasks_path=base/'input.tasks';tasks={r[0]:r for r in struct.iter_unpack('<IIIIHHIII',tasks_path.read_bytes())};paths_path=base/(mode+'_0.paths.csv');paths=defaultdict(list)
    with paths_path.open() as stream:
        for r in csv.DictReader(stream):
            path=paths[int(r['task_id'])];assert int(r['path_index'])==len(path);path.append(int(r['resource_id']))
    used=set()
    for task_id,path in paths.items():
        previous=tasks[task_id][2]
        for node in path:used.add((previous,node));previous=node
    rc={};sw={};selected={};stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        if e.tag=='switch':
            timing=e.find('timing');assert e.attrib['type']=='mux';attrs={} if timing is None else timing.attrib;sw[int(e.attrib['id'])]=(float(attrs.get('R','0')),float(attrs.get('Tdel','0')))
        elif e.tag=='node':
            timing=e.find('timing');attrs={} if timing is None else timing.attrib;rc[int(e.attrib['id'])]=(float(attrs.get('R','0')),float(attrs.get('C','0')))
        elif e.tag=='edge':
            key=(int(e.attrib['src_node']),int(e.attrib['sink_node']))
            if key in used:selected.setdefault(key,int(e.attrib['switch_id']))
        if e.tag in ('switch','node','edge'):
            if len(stack)>1:stack[-2].remove(e)
            e.clear()
        stack.pop()
    assert set(selected)==used
    nodes_path=base/'input.nodes';edges_path=base/'input.edges';nodes=list(struct.iter_unpack('<IHH',nodes_path.read_bytes()));edges=list(struct.iter_unpack('<IHH',edges_path.read_bytes()));local={};packed={}
    for source,target in used:
        switch_r,tdel=sw[selected[(source,target)]];node_r,node_c=rc[target];delay=(tdel+(switch_r+.5*node_r)*node_c)*1e12
        begin,count,_=nodes[source];values=[edges[i][2] for i in range(begin,begin+count) if edges[i][0]==target];assert values and len(set(values))==1
        assert values[0]==max(0,min(65535,round(delay))),((source,target),delay,values)
        local[(source,target)]=delay;packed[(source,target)]=values[0]
    rows=[]
    for task_id,path in paths.items():
        root=tasks[task_id][2];assert rc[root][0]*rc[root][1]==0
        previous=root;continuous=0.;quantized=0
        for node in path:continuous+=local[(previous,node)];quantized+=packed[(previous,node)];previous=node
        error=quantized-continuous;assert abs(error)<=.5*len(path)+1e-7
        rows.append(dict(task_id=task_id,path_edges=len(path),xml_local_rc_sum_ps=continuous,packed_sum_ps=quantized,rounding_error_ps=error))
    errors=[r['rounding_error_ps'] for r in rows]
    report=dict(status='actual_path_integer_ps_rounding_reconstructed_from_xml_local_rc',tasks=len(rows),used_arcs=len(used),minimum_rounding_error_ps=min(errors),maximum_rounding_error_ps=max(errors),maximum_absolute_rounding_error_ps=max(abs(v) for v in errors),largest_errors=sorted(rows,key=lambda r:-abs(r['rounding_error_ps']))[:10],source_sha256={str(p):sha(p) for p in [pair,graph,arch,tasks_path,paths_path,nodes_path,edges_path,Path(__file__).resolve()]},scope='Every active packed edge checked against XML local RC formula and per-edge rounding. XML doubles,not bit-exact VPR float or full native Tatum/RC oracle;does not explain routing QoR causally or justify relaxing its original gate.',board_result=False,research_complete=False)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','largest_errors']}))

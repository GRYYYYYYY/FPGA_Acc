"""Bind all intercluster LUT input arcs on updated over-baseline endpoint paths."""
import csv,hashlib,json,re,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
from profile_sb_ex5p_native_STA_paths import parse
D=Path('work/native_joint_budget_ex5p_baseline_target_probe_20261016')
protocol=Path('work/native_joint_budget_net_repair_v2_20261016/protocol.json')
case=json.loads(protocol.read_text())['cases'][0]
native=Path(case['native_case']);packed=native/'circuit.net';place=native/'circuit.place';rr=native/'rr_graph.xml';blif=native/'circuit.blif'
root=E.parse(packed).getroot();parents={c:b for b in root.iter() for c in b}
def atom(name):
    found = [b for b in root.iter('block') if b.get('name') == name and (not b.findall('block')) and (b.find('outputs/port') is not None)]
    assert len(found) == 1
    return found[0]

def chain(node):
    out = []
    while node is not root:
        out.append(node)
        node = parents[node]
    return out

def port(block, name):
    found = [p for section in ['inputs', 'outputs', 'clocks'] for p in block.findall(section + '/port') if p.get('name') == name]
    assert len(found) == 1, (block.attrib, name)
    return (found[0].text or '').split()

def matches(block, reference):
    actual = block.get('instance', '')
    return actual == reference or ('[' not in reference and re.sub('\\[\\d+\\]$', '', actual) == reference)

def resolve(block, name, index, trace=None, seen=None):
    trace = [] if trace is None else trace
    seen = set() if seen is None else seen
    key = (id(block), name, index)
    assert key not in seen
    seen.add(key)
    tokens = port(block, name)
    assert index < len(tokens)
    token = tokens[index]
    trace.append(dict(block=block.get('name'), instance=block.get('instance'), port=name, index=index, value=token))
    if token == 'open':
        return (None, trace)
    if '->' not in token:
        return (token, trace)
    m = re.fullmatch('([^\\.]+)\\.([^\\[]+)\\[(\\d+)\\]', token.split('->')[0])
    assert m, token
    (component, nextport, nextindex) = (m[1], m[2], int(m[3]))
    parent = parents.get(block)

    def endpoint_matches(node):
        if not matches(node, component):
            return False
        ports = [po for section in ['inputs', 'outputs', 'clocks'] for po in node.findall(section + '/port') if po.get('name') == nextport]
        return len(ports) == 1 and nextindex < len((ports[0].text or '').split())
    if parent is not None and parent.tag == 'block' and endpoint_matches(parent):
        target = parent
    else:
        found = [b for b in block.findall('block') if endpoint_matches(b)]
        if not found and parent is not None:
            found = [b for b in parent.findall('block') if endpoint_matches(b)]
        assert len(found) == 1, (block.attrib, token, [v.attrib for v in found])
        target = found[0]
    return resolve(target, nextport, nextindex, trace, seen)
report=D/'native_validation/report_timing.setup.rpt'
paths=[p for p in parse(report.read_text()) if Decimal(p['arrival_ns'])>Decimal(str(case['baseline_cpd_ns']))]
definitions={}
for line in blif.read_text().splitlines():
    f=line.split()
    if f and f[0]=='.names':definitions[f[-1]]=f[1:-1]
tasks=list(csv.DictReader(open(case['connections'])))
positions={}
for line in place.read_text().splitlines():
    f=line.split()
    if len(f)>=6 and f[1].isdigit():positions[f[0]]=(int(f[1]),int(f[2]),int(f[4]))
needed={int(t['sink']) for t in tasks};nodes={};classes={}
for _,e in E.iterparse(rr,events=['end']):
    if e.tag=='block_type':
        if e.get('name')=='LAB':
            for i,c in enumerate(e.findall('pin_class')):
                for pin in c.findall('pin'):classes[pin.text]=i
        e.clear()
    elif e.tag=='node':
        n=int(e.get('id'))
        if n in needed:nodes[n]=dict(type=e.get('type'),loc={k:int(v) for k,v in e.find('loc').attrib.items() if k in ['xlow','ylow','layer','ptc']})
        e.clear()
    elif e.tag=='edge':e.clear()
rows=[]
for path in paths:
    for arc in path['arcs']:
        m=re.fullmatch(r'(.*)\.in\[(\d+)\] \(\.names\)',arc['target'])
        if not m:continue
        name,index=m[1],int(m[2]);net=definitions[name][index];sink=atom(name)
        rotation=sink.find("inputs/port_rotation_map[@name='in']")
        assert rotation is not None
        physical=[i for i,v in enumerate(rotation.text.split()) if v==str(index)];assert len(physical)==1
        resolved,trace=resolve(sink,'in',physical[0]);assert resolved==net
        cluster=chain(sink)[-1]
        intra=trace[-1]['instance']!=cluster.get('instance')
        row=dict(endpoint=path['endpoint'],net=net,sink_atom=name,logical_input=index,physical_input=physical[0],printed_arc_ns=arc['increment_ns'],intracluster=intra,packed_trace=trace)
        if not intra:
            last=trace[-1];cls=classes['LAB.'+last['port']+'['+str(last['index'])+']'];pos=positions[cluster.get('name')]
            selected=[t for t in tasks if t['net']==net and nodes[int(t['sink'])]['type']=='SINK' and tuple(nodes[int(t['sink'])]['loc'][k] for k in ['xlow','ylow','layer'])==pos and nodes[int(t['sink'])]['loc']['ptc']==cls]
            assert len(selected)==1,(net,selected)
            row.update(task=selected[0],sink_class=cls,position=pos)
        rows.append(row)
inputs=[protocol,report,packed,place,rr,blif,Path(case['connections']),Path(__file__),Path('tools/profile_sb_ex5p_native_STA_paths.py')]
output=dict(status='all_LUT_input_arcs_on_two_updated_overbaseline_paths_bound',paths=paths,arcs=rows,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},scope='LUT input arcs only; terminal output-pad arcs excluded. Packed wiring and RR SINK equivalence class task binding, no rerouting.',research_complete=False)
with (D/'updated_critical_tasks.json').open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ('packed_trace','position')} for r in rows],indent=2))

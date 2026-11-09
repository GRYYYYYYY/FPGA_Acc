"""Read-only packed-wiring binding of native STA LUT-input arcs to route tasks.

LUT inputs, latch D inputs and output-pad inputs are bound.
No routing decisions or case-specific IDs are encoded here.
"""
import csv,re,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
from native_setup_path_parser_v2 import parse


def make_binder(native_case, connections):
    native=Path(native_case)
    root=E.parse(native/'circuit.net').getroot()
    parents={child:node for node in root.iter() for child in node}
    def atom(name):
        found = [b for b in root.iter('block') if b.get('name') == name and (not b.findall('block'))]
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
    definitions={};latches={};outputs=set()
    for line in (native/'circuit.blif').read_text().replace(chr(92)+chr(10),' ').splitlines():
        f=line.split()
        if f and f[0]=='.names':definitions[f[-1]]=f[1:-1]
        if f and f[0]=='.latch':latches[f[2]]=f[1]
        if f and f[0]=='.outputs':outputs.update(f[1:])
    with Path(connections).open() as stream:tasks=list(csv.DictReader(stream))
    positions={};subblocks={}
    for line in (native/'circuit.place').read_text().splitlines():
        f=line.split()
        if len(f)>=6 and f[1].isdigit():
            positions[f[0]]=(int(f[1]),int(f[2]),int(f[4]));subblocks[f[0]]=int(f[3])
    needed={int(t['sink']) for t in tasks};nodes={};classes={}
    for _,e in E.iterparse(native/'rr_graph.xml',events=['end']):
        if e.tag=='block_type':
            for i,c in enumerate(e.findall('pin_class')):
                for pin in c.findall('pin'):classes[(e.get('name'),pin.text)]=i
            e.clear()
        elif e.tag=='node':
            n=int(e.get('id'))
            if n in needed:nodes[n]=dict(type=e.get('type'),loc={k:int(v) for k,v in e.find('loc').attrib.items() if k in ['xlow','ylow','layer','ptc']})
            e.clear()
        elif e.tag=='edge':e.clear()
    assert set(nodes)==needed
    by_net={}
    for task in tasks:by_net.setdefault(task['net'],[]).append(task)

    def bind(report,baseline_cpd_ns,domain_setup_constraints_ns=None):
        selected=[p for p in parse(Path(report).read_text(),domain_setup_constraints_ns) if Decimal(p['effective_delay_ns'])>Decimal(str(baseline_cpd_ns))]
        rows=[]
        for path in selected:
            for arc in path['arcs']:
                m=re.fullmatch(r'(.*)\.(in|D|outpad)\[(\d+)\] \(\.(names|latch|output)\)',arc['target'])
                if not m:continue
                name,portname,index,kind=m[1],m[2],int(m[3]),m[4];sink=atom(name)
                if kind=='names':
                    assert portname=='in';net=definitions[name][index]
                    rotation=sink.find("inputs/port_rotation_map[@name='in']");assert rotation is not None
                    physical=[i for i,v in enumerate(rotation.text.split()) if v==str(index)];assert len(physical)==1
                elif kind=='latch':
                    assert portname=='D' and index==0;net=latches[name];physical=[0]
                else:
                    assert portname=='outpad' and index==0;physical=[0]
                    net,_=resolve(sink,portname,0);assert net in outputs
                resolved,trace=resolve(sink,portname,physical[0]);assert resolved==net
                cluster=chain(sink)[-1];intra=trace[-1]['instance']!=cluster.get('instance')
                row=dict(endpoint=path['endpoint'],endpoint_arrival_ns=path['arrival_ns'],net=net,sink_atom=name,logical_input=index,physical_input=physical[0],printed_arc_ns=arc['increment_ns'],intracluster=intra,sink_kind=kind)
                if not intra:
                    last=trace[-1];kind=re.sub(r'\[\d+\]$','',cluster.get('instance'))
                    pin=kind+'.'+last['port']+'['+str(last['index'])+']'
                    if (kind,pin) not in classes:pin=kind+'['+str(subblocks[cluster.get('name')])+'].'+last['port']+'['+str(last['index'])+']'
                    cls=classes[kind,pin];pos=positions[cluster.get('name')]
                    matches_task=[t for t in by_net.get(net,[]) if nodes[int(t['sink'])]['type']=='SINK' and tuple(nodes[int(t['sink'])]['loc'][k] for k in ['xlow','ylow','layer'])==pos and nodes[int(t['sink'])]['loc']['ptc']==cls]
                    assert len(matches_task)==1,(net,matches_task)
                    row['task']=matches_task[0]
                rows.append(row)
        return dict(paths=selected,arcs=rows,scope='Over-baseline printed endpoint paths; LUT, latch-D and output-pad input arcs; no route changes. General nonzero-period SDC handling is not validated.')
    return bind

"""Independent complete input replay and mutation checks for output realization.

Does not import the certificate generator, its geometry reader, crossbar parser,
or packed-pin resolver. Original ignored-only rejection remains preserved.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import resource
import sys
import time
import xml.etree.ElementTree as ET
from xml.parsers import expat

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure

HEADER = re.compile(r'^\s*Net\s+\d+\s+\((.*)\)(?:: global net connecting:)?\s*$')
NODE = re.compile(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b.*?Switch:\s*(-?\d+)')


def traces(path):
    digests = {}; opins = defaultdict(set); name = None; digest = None
    for line in path.open():
        header = HEADER.match(line)
        if header:
            if digest is not None:
                digests[name] = digest.hexdigest()
            name = header[1]
            if name in digests:
                raise ValueError('duplicate NET section')
            digest = hashlib.sha256()
        elif line.lstrip().startswith('Net '):
            raise ValueError('unparsed NET header')
        node = NODE.match(line)
        if node:
            if name is None:
                raise ValueError('node without NET')
            digest.update((','.join(node.groups()) + '\n').encode())
            if node[2] == 'OPIN':
                opins[name].add(int(node[1]))
        elif line.lstrip().startswith('Node:'):
            raise ValueError('unparsed node')
    if digest is not None:
        digests[name] = digest.hexdigest()
    return digests, opins


def graph_witnesses(graph, wanted):
    grid = {}; pins = {}; nodes = {}; stack = []; tid = None; cid = -1
    class Finished(Exception):
        pass
    def start(tag, a):
        nonlocal tid, cid
        parent = stack[-1] if stack else None
        if tag == 'block_type' and parent == 'block_types':
            tid = int(a['id']); pins[tid] = {}; cid = -1
        if tag == 'pin_class' and parent == 'block_type':
            cid += 1
        if tag == 'pin' and parent == 'pin_class':
            ptc = int(a['ptc'])
            assert ptc not in pins[tid]
            pins[tid][ptc] = [cid, '']
        if tag == 'grid_loc' and parent == 'grid':
            key = (int(a['x']), int(a['y']), int(a.get('layer', '0')))
            assert key not in grid
            grid[key] = tuple(int(a[k]) for k in ('block_type_id','width_offset','height_offset'))
        if tag == 'node' and parent == 'rr_nodes':
            nid = int(a['id'])
            if nid in wanted:
                assert a['type'] == 'OPIN' and int(a['capacity']) > 0 and nid not in nodes
                nodes[nid] = dict(a)
        if tag == 'loc' and parent == 'node' and 'rr_nodes' in stack:
            if current_node[0] in wanted:
                nodes[current_node[0]]['loc'] = dict(a)
        if tag == 'node' and parent == 'rr_nodes':
            current_node[0] = int(a['id'])
        if tag == 'pin' and parent == 'pin_class':
            current_pin[0] = ptc
        stack.append(tag)
    def chars(s):
        if stack and stack[-1] == 'pin' and len(stack) > 1 and stack[-2] == 'pin_class':
            pins[tid][current_pin[0]][1] += s
    def end(tag):
        assert stack.pop() == tag
        if tag == 'rr_nodes':
            raise Finished()
    current_node = [None]; current_pin = [None]
    parser = expat.ParserCreate(); parser.StartElementHandler = start; parser.EndElementHandler = end
    parser.CharacterDataHandler = chars
    with graph.open('rb') as f:
        try:
            parser.ParseFile(f)
        except Finished:
            pass
    assert set(nodes) == wanted
    geometry = {}
    for nid, n in nodes.items():
        loc = n['loc']; x, y = int(loc['xlow']), int(loc['ylow']); layer = int(loc.get('layer','0'))
        assert int(loc['xhigh']) == x and int(loc['yhigh']) == y
        t, dx, dy = grid[x,y,layer]; cls, pin = pins[t][int(loc['ptc'])]
        m = re.fullmatch(r'([^.[\]]+)(?:\[(\d+)\])?\.([^.[\]]+)\[(\d+)\]', pin.strip())
        assert m is not None
        geometry[nid] = dict(x=x-dx, y=y-dy, layer=layer, physical_pin=int(loc['ptc']),
                             cls=cls, logical=m[1], z=int(m[2] or 0), port=m[3], bit=int(m[4]))
    return geometry


def declared_crossbars(arch):
    root = ET.parse(arch).getroot()
    lab = next(b for b in root.find('complexblocklist') if b.get('name') == 'LAB')
    output = next(p for p in lab.findall('output') if p.get('name') == 'data_out')
    assert output.get('equivalent') == 'full'
    width = int(output.get('num_pins'))
    result = {}
    def span(text, size):
        if text is None:
            return list(range(size))
        v = [int(x) for x in text.split(':')]
        lo, hi = min(v), max(v)
        assert 0 <= lo <= hi < size and len(v) in (1,2)
        return list(range(lo,hi+1))
    for mode in lab.findall('mode'):
        outputs = [edge for ic in mode.findall('interconnect') for edge in ic
                   if edge.get('output') == 'LAB.data_out']
        assert len(outputs) == 1 and outputs[0].tag == 'complete'
        edge = outputs[0]; allowed = set()
        for token in edge.get('input').split():
            m = re.fullmatch(r'(\w+)(?:\[([^\]]+)\])?\.(\w+)(?:\[([^\]]+)\])?',token)
            assert m
            child = next(c for c in mode.findall('pb_type') if c.get('name') == m[1])
            port = next(p for p in child.findall('output') if p.get('name') == m[3])
            for i in span(m[2],int(child.get('num_pb','1'))):
                for j in span(m[4],int(port.get('num_pins'))):
                    allowed.add(f'{m[1]}[{i}].{m[3]}[{j}]->{edge.get("name")}')
        result[mode.get('name')] = (width, allowed)
    return result


def packed_drivers(packed, records):
    root = ET.parse(packed).getroot(); blocks = {b.get('name'):b for b in root.findall('block')}
    parents = {c:b for b in root.iter('block') for c in b.findall('block')}
    ports = {b:{p.get('name'):(p.text or '').split() for s in ['inputs','outputs','clocks']
                for p in b.findall(s+'/port')} for b in root.iter('block')}
    resolved = {}; tokens = {}
    for name,r in records.items():
        d = r['pins'][0]; block = blocks[d['block']]; token = ports[block][d['port']][d['bit']]
        tokens[name] = (block.get('mode'),token)
        state = (block,d['port'],d['bit']); seen = set()
        while True:
            if state in seen:
                raise ValueError('packed reference cycle')
            seen.add(state); b,p,bit = state; value = ports[b][p][bit]
            if '->' not in value:
                assert value == name
                resolved[name] = value
                break
            source = value.split('->')[0]
            m = re.fullmatch(r'([^.]*)\.([^.[\]]+)\[(\d+)\]',source); assert m
            matches = [c for c in b.findall('block') if c.get('instance') == m[1]]
            if not matches:
                context = b
                while context is not None:
                    instance = context.get('instance')
                    if instance == m[1] or re.sub(r'\[\d+\]$','',instance) == m[1]:
                        matches = [context];break
                    context = parents.get(context)
            assert len(matches) == 1
            state = (matches[0],m[2],int(m[3]))
    return tokens, {n:b.get('mode') for n,b in blocks.items() if b.get('instance').startswith('LAB[')}


def verify_rows(rows, actual, drivers, geometry, tokens, contracts):
    required = {(name,nid) for name,ns in actual.items() for nid in ns
                if geometry[nid]['logical']=='LAB' and geometry[nid]['port']=='data_out'}
    seen = set(); physical_owners = {}
    for w in rows:
        name,nid = w['net'],w['opin']
        if (name,nid) not in required or (name,nid) in seen:
            raise ValueError('wrong, duplicate or absent actual OPIN')
        seen.add((name,nid)); d = drivers[name]; g = geometry[nid]
        if ((g['x'],g['y'],g['layer'],g['cls']) != (d['x'],d['y'],d['layer'],d['class'])
            or w['block'] != d['block'] or w['original_bit'] != d['bit'] or w['routed_bit'] != g['bit']):
            raise ValueError('root/class/logical driver/physical bit mismatch')
        mode,token = tokens[name]; width,allowed = contracts[mode]
        if w['original_local_driver_token'] != token or token not in allowed or not 0 <= g['bit'] < width:
            raise ValueError('crossbar source or port mismatch')
        key = (d['block'],g['bit'])
        if key in physical_owners and physical_owners[key] != name:
            raise ValueError('one physical output assigned to two NETs')
        physical_owners[key] = name
    if seen != required:
        raise ValueError('incomplete actual OPIN domain')
    for name,ns in actual.items():
        for nid in ns:
            if (name,nid) in required:
                continue
            d,g = drivers[name],geometry[nid]
            if (g['x'],g['y'],g['layer'],g['cls'],g['physical_pin']) != (d['x'],d['y'],d['layer'],d['class'],d['physical_pin']):
                raise ValueError('other physical output changed')
    return physical_owners


def main():
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30)); tick=time.perf_counter()
    src=R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15'
    case=R/'experiments/neuron_output_crossbar_realization_v1_2026-10-15'; proof=case/'verification.json'
    v=json.loads(proof.read_text()); assert v['all_pass'] and not v['label_accepted']
    for p,h in v['bindings'].items(): assert sha(p)==h,p
    native=R/'experiments/titan23_neuron_native_cold_label_v1_2026-10-14'
    command=json.loads((native/'launch.json').read_text())['command']
    graph=Path(command[command.index('--read_rr_graph')+1]); arch=Path(command[1])
    a,actual=traces(native/'output.route'); b,_=traces(src/'canonical/design.route'); assert a==b
    geometry=graph_witnesses(graph,{n for ns in actual.values() for n in ns})
    records={r['name']:r for r in map(json.loads,(src/'canonical/identity.jsonl').open())}
    drivers={n:r['pins'][0] for n,r in records.items()}
    tokens,modes=packed_drivers(src/'canonical/design.net',records)
    contracts=declared_crossbars(arch)
    owners=verify_rows(v['witnesses'],actual,drivers,geometry,tokens,contracts)
    # Rebuild every mismatch independently, including unused/open physical pins.
    old={};locations={}
    for name,d in drivers.items():
        if d['block'] in modes and d['port']=='data_out':
            old[d['block'],d['bit']]=name;locations[d['block']]=(d['x'],d['y'],d['layer'])
    expected=Counter()
    for block,mode in modes.items():
        x,y,layer=locations[block]
        for bit in range(contracts[mode][0]):
            before=old.get((block,bit),'unmapped');after=owners.get((block,bit),'unmapped')
            if before!='unmapped' and len(records[before]['pins'])==1:continue
            if before!=after:expected[after,block,x,y,'LAB','data_out',bit,layer,before]+=1
    pattern=re.compile(r"Fixed up net '([^']*)' mapping mismatch at clustered block '(.*)' pin 'grid\[(\d+)\]\[(\d+)\]\.([^.]*)\.([^\[]*)\[(\d+)\] - layer (\d+)' \(was net '([^']*)'\)")
    log=(src/'canonical/reload.log').read_text();observed=Counter();ignored=Counter()
    for m in pattern.finditer(log):
        n,b,x,y,t,p,i,l,old=m.groups();key=(n,b,int(x),int(y),t,p,int(i),int(l),old)
        if t=='LAB' and p=='data_out':observed[key]+=1
        else:
            assert n=='unmapped' and records[old]['ignored'];ignored[old,b,int(x),int(y),int(l),p,int(i)]+=1
    assert observed==expected
    allowed=Counter((r['name'],p['block'],p['x'],p['y'],p['layer'],p['port'],p['bit'])
                    for r in records.values() if r['ignored'] for p in r['pins'] if p['index']>0)
    assert not ignored-allowed
    assert sum(expected.values())+sum(ignored.values())==int(re.search(r'Found (\d+) mismatches',log)[1])
    fixes=int(re.search(r'Fixed (\d+) routing traces',log)[1]);assert fixes==sum(ignored.values())
    assert sha(src/'canonical/design.net')==sha(src/'canonical/design.net.post_routing')
    assert sha(native/'design.sdc')==sha(src/'canonical/design.sdc')
    native_log=(native/'native.log').read_text()
    for text in [native_log,log]:
        assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
    cpd=lambda text:re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]
    assert cpd(native_log)==cpd(log)
    rejected=[]
    for mutation in ['remove_multifanout_OPIN','wrong_NET','wrong_physical_bit','wrong_local_driver','duplicate_OPIN']:
        rows=list(v['witnesses']);index=next(i for i,w in enumerate(rows) if len(actual[w['net']])>1)
        changed=dict(rows[index])
        if mutation=='remove_multifanout_OPIN':rows.pop(index)
        elif mutation=='wrong_NET':changed['net']=next(n for n in actual if n!=changed['net']);rows[index]=changed
        elif mutation=='wrong_physical_bit':changed['routed_bit']+=1;rows[index]=changed
        elif mutation=='wrong_local_driver':changed['original_local_driver_token']='open';rows[index]=changed
        else:rows.append(changed)
        try:verify_rows(rows,actual,drivers,geometry,tokens,contracts)
        except (ValueError,KeyError):rejected.append(mutation)
        else:raise AssertionError('invalid certificate accepted: '+mutation)
    bindings={**closure([Path(__file__)]),str(proof):sha(proof),**v['bindings']}
    for p,h in bindings.items(): assert sha(p)==h,p
    result=dict(bindings=bindings,all_pass=True,actual_routed_NETs=len(actual),
                actual_OPINs=sum(map(len,actual.values())),full_original_physical_trace_digests_identical=True,
                independently_resolved_original_atom_driver_NETs=len(records),
                all_crossbar_OPINs_roots_classes_modes_drivers_and_complete_fanout_pass=True,
                all_native_mismatch_records_reproduced=True,output_mismatches=sum(expected.values()),
                authenticated_ignored_sink_mismatches=sum(ignored.values()),native_trace_fixups=fixes,
                invalid_certificate_rejections=rejected,SDC_byte_identical=True,CPD_ns=float(cpd(log)),
                native_FULL_and_STA_pass=True,packed_netlist_byte_identical=True,
                old_ignored_only_gate_pass=False,label_accepted=False,
                post_label_development_evidence=True,seconds=time.perf_counter()-tick,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='Independent complete architecture/packed-driver/actual-OPIN replay, unchanged physical route, original native FULL/STA and five rejected corruptions. Does not silently replace the rejected old canonical gate or constitute heldout/functional HDL/end-to-end gain evidence.')
    output=case/'independent_verification.json'
    with output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)


if __name__=='__main__':main()

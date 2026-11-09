"""All admitted neuron sink pins against original RR IPIN/root/class witnesses."""
import json
import resource
import sys
import xml.etree.ElementTree as E
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from rooted_native_sink_pin_v1 import root,resolve

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def main():
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    out=R/'experiments/neuron_rooted_native_pin_resolver_v1_2026-10-13';out.mkdir(exist_ok=False)
    demand=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13'
    proof_path=demand/'pin_manifest/verification.json';proof=json.loads(proof_path.read_text())
    assert proof['logical_pin_key_to_native_index_and_XML_physical_identity_pass']
    bindings={**closure([Path(__file__)]),**proof['bindings'],str(proof_path):sha(proof_path)}
    assert all(sha(p)==h for p,h in bindings.items())
    ep=json.loads((demand/'demand/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path'])
    rows=[json.loads(x) for x in Path(ep['inputs']['native_identity']['path']).read_text().splitlines()]
    native={r['net_id']:r for r in rows};alignment=json.loads((demand/'pin_manifest/pin_alignment.json').read_text())
    assert len(alignment)==77106
    wanted=set();contracts=[]
    for a in alignment:
        row=native[a['net_id']];pin=row['pins'][a['local_sink_pin']]
        assert not row['ignored'] and pin['index']==a['local_sink_pin']
        assert (pin['block'],pin['port'],pin['bit'],pin['physical_pin'])==(a['block'],a['port'],a['bit'],a['physical_pin'])
        key=(pin['x'],pin['y'],pin['layer'],pin['physical_pin'],pin['class'])
        wanted.add(key);contracts.append((a,row,key))
    sinks_wanted={a['rr_node'] for a in alignment};sinks={};ipins=defaultdict(list)
    grid={};classes={};stack=[];total_nodes=0
    for event,node in E.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(node);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if node.tag=='block_type' and parent=='block_types':
            tid=int(node.get('id'));assert tid not in classes;classes[tid]={}
            for cid,cls in enumerate(node.findall('pin_class')):
                for pin in cls.findall('pin'):
                    ptc=int(pin.get('ptc'));assert ptc not in classes[tid];classes[tid][ptc]=cid
            stack[-2].remove(node);node.clear()
        elif node.tag=='grid_loc' and parent=='grid':
            key=tuple(int(node.get(k,'0')) for k in ['x','y','layer']);assert key not in grid
            grid[key]=tuple(int(node.get(k)) for k in ['block_type_id','width_offset','height_offset'])
            stack[-2].remove(node);node.clear()
        elif node.tag=='node' and parent=='rr_nodes':
            nid=int(node.get('id'));assert nid==total_nodes;total_nodes+=1
            kind=node.get('type');info=dict(type=kind,loc=dict(node.find('loc').attrib))
            if nid in sinks_wanted:
                assert kind=='SINK' and int(node.get('capacity'))>0;sinks[nid]=info
            if kind=='IPIN':
                tid,x,y,layer=root(info,grid);physical=int(info['loc']['ptc']);cls=classes[tid][physical]
                key=(x,y,layer,physical,cls)
                if key in wanted:
                    assert int(node.get('capacity'))>0;ipins[key].append((nid,info))
            stack[-2].remove(node);node.clear()
        if node.tag=='rr_nodes':break
        stack.pop()
    assert total_nodes==3593250 and set(sinks)==sinks_wanted and set(ipins)==wanted
    checked=offset=variants=0
    for a,row,key in contracts:
        sink=sinks[a['rr_node']]
        for nid,ipin in ipins[key]:
            assert resolve(row,ipin,sink,grid,classes)==a['local_sink_pin'];variants+=1
        _,x,y,_=root(sink,grid);loc=sink['loc']
        offset+=not (int(loc['xlow'])<=x<=int(loc['xhigh']) and int(loc['ylow'])<=y<=int(loc['yhigh']))
        checked+=1
    assert checked==77106 and all(sha(p)==h for p,h in bindings.items())
    result=dict(bindings=bindings,all_pass=True,original_nodes=total_nodes,connections_checked=checked,
                matching_original_IPIN_variants_checked=variants,sink_pin_instances_with_bbox_excluding_root=offset,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='Complete pre-route native demand identity plus all matching original physical IPIN variants and rooted SINK classes. No actual routed IPIN selection, post-route packing identity, native canonical reload or QoR result yet.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='bindings'},flush=True)

if __name__=='__main__':main()

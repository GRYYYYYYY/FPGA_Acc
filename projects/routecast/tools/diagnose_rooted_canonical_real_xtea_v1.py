"""Real three-arm native traces versus certified canonical XTEA labels."""
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path
from audit_native_route import NODE
from rooted_canonical_route_text_v1 import render,physical_sequences
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def main():
    out=R/'experiments/rooted_canonical_real_xtea_diagnosis_v1_2026-10-13';out.mkdir(exist_ok=False)
    old=R/'experiments/xtea_retention_native_comparison_v1_2026-10-13'
    proof_path=old/'verification.json';proof=json.loads(proof_path.read_text())
    assert proof['all_three_native_physical_and_canonical_pass']
    assert all(sha(p)==h for p,h in proof['bindings'].items())
    bindings={**closure([Path(__file__)]),**proof['bindings'],str(proof_path):sha(proof_path)}
    ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
    graph=Path(json.loads(ep.read_text())['inputs']['graph']['path']);bindings[str(ep)]=sha(ep)
    wanted=set();inputs={}
    for arm in ['cold','control','retained']:
        route=old/arm/'output.route';canonical=old/(arm+'_canonical')/'design.route'
        identity=canonical.parent/'identity.jsonl';place=canonical.parent/'design.place'
        inputs[arm]=(route,canonical,identity,place)
        for p in inputs[arm]:assert bindings[str(p)]==sha(p)
        wanted.update(int(m[1]) for line in route.read_text().splitlines() if (m:=NODE.match(line)))
    nodes={};grid={};classes={};stack=[]
    for event,node in E.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(node);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if node.tag=='block_type' and parent=='block_types':
            tid=int(node.get('id'));classes[tid]={}
            for cid,cls in enumerate(node.findall('pin_class')):
                for pin in cls.findall('pin'):classes[tid][int(pin.get('ptc'))]=cid
            stack[-2].remove(node);node.clear()
        elif node.tag=='grid_loc' and parent=='grid':
            grid[tuple(int(node.get(k,'0')) for k in ['x','y','layer'])]=tuple(int(node.get(k)) for k in ['block_type_id','width_offset','height_offset'])
            stack[-2].remove(node);node.clear()
        elif node.tag=='node' and parent=='rr_nodes':
            nid=int(node.get('id'))
            if nid in wanted:nodes[nid]=dict(type=node.get('type'),loc=dict(node.find('loc').attrib))
            stack[-2].remove(node);node.clear()
        if node.tag=='rr_nodes':break
        stack.pop()
    assert set(nodes)==wanted;results=[]
    for arm,(route,canonical,identity,place) in inputs.items():
        rows=[json.loads(x) for x in identity.read_text().splitlines()];native={r['name']:r for r in rows}
        actual,pins=render(route.read_text().splitlines(),native,nodes,grid,classes,sha(place))
        expected=canonical.read_text().splitlines()
        (out/(arm+'.actual.route')).write_text('\n'.join(actual)+'\n')
        if actual!=expected:
            import difflib
            diff=list(difflib.unified_diff(expected,actual,fromfile='certified',tofile='candidate'))
            (out/(arm+'.diff')).write_text('\n'.join(diff)+'\n')
            print('DIFFERENCES',arm,len(expected),len(actual),'\n'.join(diff[:35]),flush=True)
            return
        assert physical_sequences(actual)==physical_sequences(route.read_text().splitlines())
        dest=out/(arm+'.route');dest.write_text('\n'.join(actual)+'\n');bindings[str(dest)]=sha(dest)
        results.append(dict(arm=arm,pins=pins,canonical_text_equal=True,physical_sequences_equal=True))
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,all_pass=True,arms=results,
        scope='All three real exposed-XTEA native route traces and actual post-route identities reproduced existing FULL/STA certified canonical files exactly. No new VPR execution and no neuron post-route result.'),indent=2)+'\n')
    print('REAL ROOTED CANONICAL PARITY PASS',results,flush=True)

if __name__=='__main__':main()

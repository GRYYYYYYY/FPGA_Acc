"""Real three-arm native traces versus certified canonical XTEA labels."""
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path
from audit_native_route import NODE
from rooted_canonical_route_text_v2 import render,physical_sequences
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def main():
    out=R/'experiments/rooted_canonical_native_geometry_real_xtea_v1_2026-10-13';out.mkdir(exist_ok=False)
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
    from rooted_canonical_native_reload_v1 import selected_geometry
    nodes,grid,classes=selected_geometry(graph,wanted)
    assert set(nodes)==wanted;results=[]
    for arm,(route,canonical,identity,place) in inputs.items():
        rows=[json.loads(x) for x in identity.read_text().splitlines()];native={r['name']:r for r in rows}
        actual,pins=render(route.read_text().splitlines(),native,nodes,grid,classes,sha(place))
        expected=canonical.read_text().splitlines()
        assert actual==expected,(arm,'canonical labels differ')
        assert physical_sequences(actual)==physical_sequences(route.read_text().splitlines())
        dest=out/(arm+'.route');dest.write_text('\n'.join(actual)+'\n');bindings[str(dest)]=sha(dest)
        results.append(dict(arm=arm,pins=pins,canonical_text_equal=True,physical_sequences_equal=True))
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,all_pass=True,arms=results,
        scope='All three real exposed-XTEA native route traces and actual post-route identities reproduced existing FULL/STA certified canonical files exactly. No new VPR execution and no neuron post-route result.'),indent=2)+'\n')
    print('REAL ROOTED CANONICAL PARITY PASS',results,flush=True)

if __name__=='__main__':main()

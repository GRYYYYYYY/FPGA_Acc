import json,sys,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha,placements
out=R/'experiments/freecores_fixed_place_v1_2026-10-08';rp=out/'receipt.json';r=json.loads(rp.read_text());assert all(sha(k)==v for k,v in r['bindings'].items());bindings={str(Path(__file__)):sha(Path(__file__)),str(rp):sha(rp),str(R/'tools/pre_route_endpoints.py'):sha(R/'tools/pre_route_endpoints.py')};rows=[]
assert [x['name'] for x in r['rows']]==['8051','xtea']
for row in r['rows']:
 assert row['exit_code']==0 and all(sha(k)==v for k,v in row['files'].items());w=out/row['name'];net=w/'design.net';place=w/'design.place';positions=placements(place,sha(net));root=E.parse(net).getroot();clusters=root.findall('block');assert len({b.get('name') for b in clusters})==len(clusters) and set(positions)=={b.get('name') for b in clusters};assert {x[4] for x in positions.values()}==set(range(len(positions)));assert all(positions[b.get('name')][4]==i for i,b in enumerate(clusters));assert 'VPR succeeded' in (w/'place.log').read_text() and not (w/'design.route').exists()
 for p in [net,place,w/'place.log']:bindings[str(p)]=sha(p)
 rows.append(dict(name=row['name'],clusters=len(clusters),placement_netlist_hash_cluster_identity_unique_slots_pass=True))
assert all(sha(k)==v for k,v in bindings.items())
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,both_complete_placements_pass=True,scope='Original packed cluster bijection/dense ID/net hash/unique coordinates and native placement success. RR site compatibility checked later; no placement optimality/functional HDL/characterized async timing or route/heldout/netgain proof.'),indent=2)+'\n');print('PASS placements',rows)

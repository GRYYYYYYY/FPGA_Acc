"""Recheck bindings and identity parity without calling the rebinding guard."""
import copy
import json
from pathlib import Path
from pre_route_endpoints import placements, sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/gf2_identity_rebinding_fresh_2026-10-06'
protocol=json.loads((out/'protocol.json').read_text())
receipt=json.loads((out/'receipt.json').read_text())
assert receipt['protocol_sha256']==sha(out/'protocol.json')
assert len(protocol['cases'])==len(receipt['probes'])==6
assert all(sha(p)==h for p,h in protocol['sources'].items())
tables=[];places=[]
for spec,probe in zip(protocol['cases'],receipt['probes']):
    assert (spec['width'],spec['round'])==(probe['width'],probe['round'])
    assert all(sha(p)==h for p,h in spec['inputs'].items())
    table=Path(probe['table'])
    assert sha(table)==probe['table_sha256'] and sha(table.parent/'identity.log')==probe['log_sha256']
    assert probe['exit_code']==1 and not (table.parent/'missing.route').exists()
    rows=[json.loads(line) for line in table.read_text().splitlines()]
    source=Path(spec['source'])
    assert rows==[json.loads(line) for line in (source/'identity.jsonl').read_text().splitlines()]
    tables.append(rows);places.append(placements(source/'design.place',sha(source/'design.net')))
checked=0
for i in range(0,6,2):
    for a,b in ((i,i+1),(i+1,i)):
        rebound=copy.deepcopy(tables[a])
        for row in rebound:
            for pin in row['pins']:
                old=places[a][pin['block']];new=places[b][pin['block']]
                assert old[2]==new[2] and old[4]==new[4]
                assert (pin['x'],pin['y'],pin['layer'])==(old[0],old[1],old[3])
                pin.update(x=new[0],y=new[1],layer=new[3]);checked+=1
        assert rebound==tables[b]
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),fresh_tables_checked=6,directional_pins_checked=checked,scope='Independent coordinate/static-field parity and hashes. Producer exit status retained, not independently observed. No route/STA or timing benefit verification.'),indent=2)+'\n')
print('verified',checked,'directional pins')

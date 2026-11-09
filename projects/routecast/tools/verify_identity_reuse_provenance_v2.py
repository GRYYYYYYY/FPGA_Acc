"""Independent seed-to-materialized identity and placement byte audit."""
import copy
import json
from pathlib import Path
from pre_route_endpoints import placements, sha
from native_place_serialization import canonical_place

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/gf2_identity_reuse_continuous_two_updates_v2_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and r['all_cases_retained']
assert len(p['cases'])==len(r['rows'])==3
rows=[]
for case,result in zip(p['cases'],r['rows']):
    assert result['width']==case['width'] and result['complete'] and result['error'] is None
    seed_path=Path(result['identity_seed']);assert sha(seed_path)==result['identity_seed_sha256']
    seed=json.loads(seed_path.read_text());proof=Path(seed['native_receipt'])
    assert sha(proof)==seed['native_receipt_sha256']
    native=json.loads(proof.read_text())
    assert native['exit_code']==1 and native['bindings']['inputs_sha256']==seed['bindings']['sha256']
    assert sha(seed['table'])==seed['table_sha256']==native['table_sha256']
    assert sha(seed['log'])==seed['log_sha256']==native['log_sha256']
    assert all(sha(path)==seed['bindings']['sha256'][name] for name,path in seed['bindings']['files'].items())
    original=[json.loads(line) for line in Path(seed['table']).read_text().splitlines()]
    for i,rd in enumerate(case['rounds']):
        sandbox=Path(rd['sandbox']);stem=f"gf2_d{case['width']}_{rd['prefix']}_native_import_2026-10-06"
        work=sandbox/'work'/stem;parent=sandbox/'experiments'/stem
        receipt=json.loads((parent/'receipt.json').read_text())
        assert receipt['native_success'] and receipt['exit_code']==0
        assert all(sha(path)==h for path,h in receipt['files_sha256'].items())
        entry=json.loads((work/'identity_reuse.json').read_text())
        assert entry['seed']==str(seed_path) and entry['seed_sha256']==result['identity_seed_sha256']
        assert entry['table_sha256']==sha(work/'identity.jsonl')
        assert entry['place_after_sha256']==sha(work/'design.place')
        assert sha(work/'design.net')==seed['bindings']['sha256']['net']
        assert sha(work/'design.blif')==seed['bindings']['sha256']['blif']
        ps=placements(work/'design.place',sha(work/'design.net'))
        rebound=copy.deepcopy(original)
        for net in rebound:
            for pin in net['pins']:
                x,y,z,layer,bid=ps[pin['block']];pin.update(x=x,y=y,layer=layer)
        assert rebound==[json.loads(line) for line in (work/'identity.jsonl').read_text().splitlines()]
        assert canonical_place(work/'design.place',work/'design.net').encode()==(work/'design.place').read_bytes()
        rows.append(dict(width=case['width'],round=i,pins=sum(len(n['pins']) for n in rebound),seed_sha256=sha(seed_path),import_receipt_sha256=sha(parent/'receipt.json')))
(out/'identity_provenance_verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent hashes, seed native proof, coordinate rebound and canonical formatting audit. Runtime guard assertions producer-side; no concurrent atomicity/general equivalence proof.'),indent=2)+'\n')
print('verified',sum(row['pins'] for row in rows),'directional pins')

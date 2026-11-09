"""Archived native evidence comparison; does not authorize cache reuse."""
import copy
import json
from pathlib import Path
from pre_route_endpoints import placements, sha

ROOT = Path(__file__).resolve().parents[1]

def main():
    base = ROOT / 'work/gf2_certified_continuous_two_updates_2026-10-06'
    results = []
    for width in (32, 64, 128):
        paths = [next((base / f'gf2_d{width}' / str(r) / 'work').glob('*native_import*/identity.jsonl')) for r in (0, 1)]
        tables = [list(map(json.loads, p.read_text().splitlines())) for p in paths]
        places = [placements(p.parent / 'design.place', sha(p.parent / 'design.net')) for p in paths]
        rebound = copy.deepcopy(tables[0])
        coordinate_changes = 0
        for row in rebound:
            for pin in row['pins']:
                x, y, z, layer, bid = places[1][pin['block']]
                old = places[0][pin['block']]
                assert old[2] == z and old[4] == bid, 'subtile/block index changed'
                assert (pin['x'], pin['y'], pin['layer']) == (old[0], old[1], old[3])
                coordinate_changes += (pin['x'], pin['y'], pin['layer']) != (x, y, layer)
                pin.update(x=x, y=y, layer=layer)
        bindings = []
        for p in paths:
            bindings.append({str(f.relative_to(ROOT)): sha(f) for f in (p, p.parent/'design.net', p.parent/'design.place')})
        results.append(dict(width=width, bindings=bindings,
                            packed_net_identical=sha(paths[0].parent/'design.net') == sha(paths[1].parent/'design.net'),
                            net_count=len(rebound), pin_count=sum(len(r['pins']) for r in rebound),
                            changed_pin_coordinates=coordinate_changes,
                            rebound_matches_native=rebound == tables[1]))
    out = ROOT/'experiments/gf2_identity_rebinding_diagnosis_2026-10-06'
    out.mkdir(exist_ok=True)
    report = dict(source_sha256=sha(Path(__file__)), cases=results,
                  scope='Archived two-layout comparison only. No cache integration, timing benefit, tile compatibility proof, or arbitrary packing/subtile generalization.')
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k != 'bindings'} for r in results], indent=2))

if __name__ == '__main__':
    main()

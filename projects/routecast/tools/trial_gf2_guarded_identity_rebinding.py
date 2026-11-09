"""Check guarded rebinding against archived native tables and negative probes."""
import copy
import json
from pathlib import Path
from guarded_identity_rebinding import rebind_identity
from pre_route_endpoints import placements, physical_maps, sha

ROOT = Path(__file__).resolve().parents[1]

def main():
    rows = []
    base = ROOT/'work/gf2_certified_continuous_two_updates_2026-10-06'
    for width in (32,64,128):
        paths = [next((base/f'gf2_d{width}'/str(r)/'work').glob('*native_import*/identity.jsonl')) for r in (0,1)]
        tables = [[json.loads(s) for s in p.read_text().splitlines()] for p in paths]
        nets = [p.parent/'design.net' for p in paths]
        assert sha(nets[0]) == sha(nets[1])
        places = [placements(p.parent/'design.place',sha(n)) for p,n in zip(paths,nets)]
        ep = ROOT/f'experiments/gf2_d{width}_placement_swap_2026-10-06/endpoints.json'
        g = json.loads(ep.read_text())['inputs']['graph']
        graph = Path(g['path']); assert sha(graph) == g['sha256']
        maps = physical_maps(graph)
        assert rebind_identity(tables[0],*places,maps) == tables[1]
        assert rebind_identity(tables[1],places[1],places[0],maps) == tables[0]
        rejected = []
        block = tables[0][0]['pins'][0]['block']
        for label in ('subtile','block_index','absent_tile','pin','class','coordinate'):
            table = copy.deepcopy(tables[0]); target = dict(places[1])
            if label in ('subtile','block_index','absent_tile'):
                pos = list(target[block]); index = {'subtile':2,'block_index':4,'absent_tile':0}[label]
                pos[index] += 10000; target[block] = tuple(pos)
            else:
                field = {'pin':'physical_pin','class':'class','coordinate':'x'}[label]
                table[0]['pins'][0][field] += 10000
            try:
                rebind_identity(table,places[0],target,maps)
            except ValueError:
                rejected.append(label)
            else:
                raise AssertionError('unsafe probe accepted: '+label)
        files = [*paths,*nets,*(p.parent/'design.place' for p in paths),ep,graph]
        rows.append(dict(width=width,native_table_parity_both_directions=True,rejected=rejected,
                         inputs={str(p):sha(p) for p in files}))
    out = ROOT/'experiments/gf2_guarded_identity_rebinding_2026-10-06';out.mkdir(exist_ok=True)
    report = dict(cases=rows,sources={str(p):sha(p) for p in (Path(__file__),ROOT/'tools/guarded_identity_rebinding.py',ROOT/'tools/pre_route_endpoints.py')},
                  scope='Archived same-NET same-RR empirical parity and producer negative probes. Not live native verification, provenance certificate, integrated cache, or timing evidence.')
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print([(r['width'],r['native_table_parity_both_directions'],len(r['rejected'])) for r in rows])

if __name__ == '__main__': main()

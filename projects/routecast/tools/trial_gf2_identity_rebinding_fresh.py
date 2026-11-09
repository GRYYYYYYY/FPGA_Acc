"""Fresh isolated native identity probes for guarded GF2 rebinding."""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from guarded_identity_rebinding import rebind_identity
from pre_route_endpoints import physical_maps, placements, sha

ROOT = Path(__file__).resolve().parents[1]

def main():
    out = ROOT/'experiments/gf2_identity_rebinding_fresh_2026-10-06'
    out.mkdir()
    specs = []
    base = ROOT/'work/gf2_certified_continuous_two_updates_2026-10-06'
    for width in (32,64,128):
        for r, prefix in enumerate(('native_seeded','selected_reverse')):
            sandbox = base/f'gf2_d{width}'/str(r)
            parent = sandbox/f'experiments/gf2_d{width}_{prefix}_native_import_2026-10-06/receipt.json'
            receipt = json.loads(parent.read_text())
            source = sandbox/f'work/gf2_d{width}_{prefix}_native_import_2026-10-06'
            cmd = receipt['identity_command']
            binary = Path(cmd[0]); assert sha(binary) == receipt['identity_binary_sha256']
            graph = Path(cmd[cmd.index('--read_rr_graph')+1])
            inputs = [parent,binary,Path(cmd[1]),graph,*(source/n for n in ('design.blif','design.net','design.place','identity.jsonl'))]
            specs.append(dict(width=width,round=r,source=str(source),command=cmd,
                              inputs={str(p):sha(p) for p in inputs}))
    protocol = dict(cases=specs,sources={str(p):sha(p) for p in (Path(__file__),ROOT/'tools/guarded_identity_rebinding.py',ROOT/'tools/pre_route_endpoints.py')},
                    scope='Six fresh identity-only probes, not route/STA verification or lifecycle timing. Exit1 expected for absent route.')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    results = []
    env = {k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
    for s in specs:
        work = out/f"gf2_d{s['width']}_{s['round']}";work.mkdir()
        source = Path(s['source'])
        for name in ('design.blif','design.net','design.place'):
            shutil.copyfile(source/name,work/name)
        table = work/'identity.jsonl'; log = work/'identity.log'
        start = time.perf_counter()
        with log.open('w') as stream:
            code = subprocess.run(s['command'],cwd=work,env={**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)},stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
        elapsed = time.perf_counter()-start
        assert code == 1 and table.exists()
        native = [json.loads(line) for line in table.read_text().splitlines()]
        archived = [json.loads(line) for line in (source/'identity.jsonl').read_text().splitlines()]
        assert native == archived
        assert all(sha(p)==h for p,h in s['inputs'].items())
        results.append(dict(width=s['width'],round=s['round'],exit_code=code,probe_seconds=elapsed,
                            table=str(table),table_sha256=sha(table),log_sha256=sha(log),archived_parity=True))
    comparisons = []
    for i in range(0,6,2):
        a,b = specs[i:i+2];source = [Path(s['source']) for s in (a,b)]
        assert sha(source[0]/'design.net') == sha(source[1]/'design.net')
        ps = [placements(p/'design.place',sha(p/'design.net')) for p in source]
        graph = Path(a['command'][a['command'].index('--read_rr_graph')+1])
        assert str(graph) == b['command'][b['command'].index('--read_rr_graph')+1]
        maps = physical_maps(graph)
        ts = [[json.loads(line) for line in Path(r['table']).read_text().splitlines()] for r in results[i:i+2]]
        assert rebind_identity(ts[0],*ps,maps) == ts[1]
        assert rebind_identity(ts[1],ps[1],ps[0],maps) == ts[0]
        comparisons.append(dict(width=a['width'],both_directions_equal=True,pins=sum(len(n['pins']) for n in ts[0])))
    assert all(sha(p)==h for s in specs for p,h in s['inputs'].items())
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),probes=results,comparisons=comparisons),indent=2)+'\n')
    print(json.dumps(comparisons))

if __name__ == '__main__': main()

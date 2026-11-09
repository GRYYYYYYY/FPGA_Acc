"""Fresh profiled replays; profiler overhead precludes speedup interpretation."""
import cProfile
import json
import pstats
import time
from pathlib import Path
from bound_identity_reuse import reuse
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/gf2_identity_reuse_continuous_two_updates_v2_2026-10-06'
out=ROOT/'experiments/gf2_bound_identity_reuse_profile_2026-10-06';out.mkdir()
p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text())
assert json.loads((base/'verification.json').read_text())['receipt_sha256']==sha(base/'receipt.json')
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(base/'receipt.json'),source_sha256=sha(Path(__file__)),scope='Six serial profiled guarded reuse replays, inclusive function times overlap. Not integrated timing or native comparison.'),indent=2)+'\n')
rows=[]
for case,row in zip(p['cases'],r['rows']):
    for i,rd in enumerate(case['rounds']):
        sandbox=Path(rd['sandbox']);stem=f"gf2_d{case['width']}_{rd['prefix']}_native_import_2026-10-06"
        receipt_path=sandbox/'experiments'/stem/'receipt.json'
        receipt=json.loads(receipt_path.read_text());work=sandbox/'work'/stem
        profile=cProfile.Profile();start=time.perf_counter()
        table=profile.runcall(reuse,row['identity_seed'],row['identity_seed_sha256'],receipt['identity_command'],work)
        elapsed=time.perf_counter()-start
        assert table==[json.loads(line) for line in (work/'identity.jsonl').read_text().splitlines()]
        dump=out/f"gf2_d{case['width']}_{i}.prof";profile.dump_stats(str(dump))
        stats=pstats.Stats(profile)
        functions=[]
        for (file,line,name),(primitive,calls,self_s,total_s,callers) in stats.stats.items():
            if name in ('sha','physical_maps','rebind_identity','placements','bindings'):
                functions.append(dict(file=file,line=line,name=name,calls=calls,self_s=self_s,inclusive_s=total_s))
        rows.append(dict(width=case['width'],round=i,profiled_wall_s=elapsed,functions=functions,
                         stage_receipt_sha256=sha(receipt_path),profile_sha256=sha(dump)))
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
for row in rows:
    print(row['width'],row['round'],round(row['profiled_wall_s'],4),[(f['name'],round(f['inclusive_s'],4)) for f in row['functions']])

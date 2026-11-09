import json,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';old=base/'native_other_net_contexts_2026-10-06';out=base/'native_move_release_contexts_2026-10-06';out.mkdir();receipt=json.loads((old/'receipt.json').read_text());protocol=json.loads((base/'native_candidate_retention_diverse_benchmark_2026-10-06/protocol.json').read_text());start=time.perf_counter();frames=[]
for frame in receipt['frames']:
 design=frame['design'];step=frame['step'];p=old/f'{design}_{step}.json';assert sha(p)==frame['context_sha256'];ctx=json.loads(p.read_text());assert all(sha(f)==h for f,h in ctx['inputs_sha256'].items());table=next(Path(f) for f in ctx['inputs_sha256'] if f.endswith('.tsv') and not f.endswith('resources.tsv'));pins=[l.split('\t') for l in table.read_text().splitlines()[2:]];blocks={}
 for row in pins:blocks.setdefault(int(row[0]),set()).update((int(row[2]),int(row[3])))
 total={int(n):v for n,v in ctx['total_occupancy'].items()};unions={int(n):set(v) for n,v in ctx['own_net_nodes'].items()};residual={int(n):v for n,v in ctx['residual_demand'].items()};moves=[]
 for i,(a,b) in enumerate(protocol['pairs'][design]):
  dirty={n for n,used in blocks.items() if a in used or b in used};assert dirty<=set(unions);released=Counter(n for net in dirty for n in unions[net]);other=Counter(total)
  for n,v in released.items():assert other[n]>=v;other[n]-=v
  other=+other;expected=Counter(n for net,used in unions.items() if net not in dirty for n in used);expected.update(residual);assert other==+expected
  moves.append({'pair_index':i,'pair':[a,b],'dirty_native_nets':sorted(dirty),'released_net_node_memberships':sum(released.values()),'other_demand':dict(other)})
 file=out/f'{design}_{step}.json';file.write_text(json.dumps({'design':design,'epoch':ctx['epoch'],'step':step,'moves':moves,'source_context_sha256':sha(p),'source_context':str(p),'scope':'Release all routable NETs touching either moved block; preserve unaffected NET unions/residual reservations. Ignores unsupported macro/heterogeneous movement and non-routable clock remapping.'},indent=2)+'\n');frames.append({'design':design,'step':step,'move_contexts':len(moves),'sha256':sha(file)})
(out/'receipt.json').write_text(json.dumps({'frames':frames,'contexts':sum(x['move_contexts'] for x in frames),'wall_s':time.perf_counter()-start,'protocol_sha256':sha(base/'native_candidate_retention_diverse_benchmark_2026-10-06/protocol.json'),'source_sha256':sha(Path(__file__))},indent=2)+'\n');print('verified',sum(x['move_contexts'] for x in frames),'move-release contexts')

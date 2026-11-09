"""Explicit bound old-to-target partial seed conversion; no legality claim."""
import json,re,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2]
protocol=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
c=next(x for x in json.loads(protocol.read_text())['cases'] if (x['width'],x['index'])==(32,2))
old,target=[json.loads(Path(c[k]).read_text()) for k in ('old','target')]
assert old['inputs']['net']==target['inputs']['net'] and old['graph_sha256']==target['graph_sha256']
inputs={p:h for p,h in c['inputs'].items()};assert all(sha(p)==h for p,h in inputs.items())
original={q['connection_id']:q for q in old['connections']};assert len(original)==len(old['connections'])
assert {q['connection_id'] for q in target['connections']}==original.keys()
dirty={q['net_id'] for q in target['connections'] if (q['source'],q['sink'])!=(original[q['connection_id']]['source'],original[q['connection_id']]['sink'])}
assert old['net_names']==target['net_names']
removed={old['net_names'][str(net)] for net in dirty}
source=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.route';inputs[str(source)]=sha(source)
paths=physical_paths(source);assert removed<=paths.keys()
lines=source.read_text().splitlines(keepends=True);sections=[];header=[];current=None
pattern=re.compile(r'^Net\s+(\d+)\s+\((.*)\)\s*$')
for line in lines:
 m=pattern.match(line)
 if m:
  if current is not None:sections.append(current)
  current=(int(m[1]),m[2],[line])
 elif current is None:header.append(line)
 else:current[2].append(line)
if current is not None:sections.append(current)
assert len({name for _,name,_ in sections})==len(sections)
assert all(old['net_names'][str(net)]==name for net,name,_ in sections)
place=Path(target['inputs']['place']['path']);header[0]=f'Placement_File: design.place Placement_ID: SHA256:{sha(place)}\n'
out=ROOT/'experiments/native_target_partial_seed_2026-10-07';out.mkdir(exist_ok=False)
partial=out/'partial.route';partial.write_text(''.join(header)+''.join(''.join(ls) for _,name,ls in sections if name not in removed))
remaining=physical_paths(partial)
assert {name:Counter(ps) for name,ps in remaining.items()}=={name:Counter(ps) for name,ps in paths.items() if name not in removed}
actual=Counter((name,p[0][0],p[-1][0]) for name,ps in remaining.items() for p in ps)
expected=Counter((target['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in target['connections'] if q['net_id'] not in dirty)
assert actual==expected
assert all(sha(p)==h for p,h in inputs.items())
report=dict(inputs=inputs,source_sha256=sha(Path(__file__)),partial_route_sha256=sha(partial),removed_net_names=sorted(removed),removed_nets=len(removed),retained_nets=len(remaining),retained_connections=sum(actual.values()),required_connections=len(target['connections']),all_retained_named_paths_preserved=True,all_retained_target_endpoints_match=True,scope='Explicit placement-bound partial artifact: exclude whole endpoint-changed NETs, prove remaining original paths target endpoints and same packed net identity. Header rewritten only after this conversion; incomplete route is not FULL/STA legal or accepted. Native loader/resume with missing NETs still requires dedicated delay and state handling.')
(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(report['removed_nets'],report['retained_nets'],report['retained_connections'])

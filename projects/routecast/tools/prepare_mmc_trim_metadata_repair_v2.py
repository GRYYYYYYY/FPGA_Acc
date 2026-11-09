"""Repair stale global-block metadata in the failed trim control, not route paths."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from partial_seed_state import publish_partial_seed
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/mmc_trim_metadata_repair_v2_2026-10-21';D.mkdir(exist_ok=True)
old=R/'experiments/mmc_native_trim_seed_v1_2026-10-18/seed.route'
ep=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json'
meta=json.loads(ep.read_text());place=Path(meta['inputs']['place']['path'])
receipt=R/'experiments/mmc_native_trim_seed_v1_2026-10-18/receipt.json'
retained=set(json.loads(receipt.read_text())['retained_net_names'])
excluded=set(meta['net_names'].values())-retained
assert retained and excluded
# Preserve global metadata even when the preceding NET is excluded.
import re
from native_route_ledger_import_compact import physical_paths
locations={}
for line in place.read_text().splitlines():
 parts=line.split()
 if len(parts)==6 and parts[5].startswith('#'):
  locations[parts[0]]=(int(parts[5][1:]),tuple(map(int,(parts[1],parts[2],parts[4]))))
output=[];updates=[];checked=0
pattern=re.compile(r'^Block (\S+) \(#(\d+)\) at \((\d+),(\d+),(\d+)\)')
for line in old.read_text().splitlines(keepends=True):
 m=pattern.match(line)
 if m:
  checked+=1;number,loc=locations[m[1]];assert number==int(m[2])
  before=tuple(map(int,m.group(3,4,5)))
  if before!=loc:
   updates.append({'block':m[1],'old':before,'new':loc})
   line=re.sub(r'at \([^)]*\)',f'at ({loc[0]},{loc[1]},{loc[2]})',line,count=1)
 output.append(line)
with (D/'seed.route').open('x') as f:f.write(''.join(output))
assert physical_paths(old)==physical_paths(D/'seed.route')
proof={'physical_paths_exact':True,'global_block_coordinate_changes':updates,'checked_global_blocks':checked,'retained_connections':json.loads(receipt.read_text())['selected_connections']}
assert updates
# Independent textual delta: only the declared global Block coordinate lines may differ.
a=old.read_text().splitlines();b=(D/'seed.route').read_text().splitlines();assert len(a)==len(b)
import re
changes=[]
for i,(x,y) in enumerate(zip(a,b),1):
 if x==y:continue
 assert x.startswith('Block ') and y.startswith('Block ')
 assert re.sub(r'at \([^)]*\)','at (COORD)',x,count=1)==re.sub(r'at \([^)]*\)','at (COORD)',y,count=1)
 changes.append(i)
assert len(changes)==len(proof['global_block_coordinate_changes'])
proof.update({'changed_lines':changes,'all_non_coordinate_text_identical':True,'original_failure_preserved':True,'native_admitted':False,'scope':'New explicit control candidate. Only global-block metadata coordinates updated to target placement; all retained RR paths and endpoints exact. Original trim failure preserved. Requires fresh native full/physical/canonical validation; no outcome or timing claim.','bindings':{str(p):sha(p) for p in [Path(__file__),old,ep,place,receipt,D/'seed.route']}})
(D/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({k:proof[k] for k in ['retained_connections','checked_global_blocks','changed_lines','all_non_coordinate_text_identical','native_admitted']},indent=2))

"""Physical-only complete oldnative seed for unchanged-placement replay."""
import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_no_move_native_seed_v1_2026-10-18';gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(gp.read_text());epfile=Path(g['previous_endpoint']);ep=json.loads(epfile.read_text());route=Path(g['previous_native_route']);readyfile=gp.with_name('readiness_verification_v1.json');ready=json.loads(readyfile.read_text());assert ready['native_canonical_semantic_pass'] and ready['ignored_pin_fixups']==330 and all(sha(p)==h for p,h in ready['bindings'].items());allowed={ep['net_names'][str(q['net_id'])] for q in ep['connections']};header=[];chunks=[];current=None;lines=[];HEADER=re.compile(r'^Net\s+(\d+)\s+\((.*)\)(.*)$')
for line in route.read_text().splitlines():
 m=HEADER.match(line)
 if m:
  if current is not None and current in allowed:chunks.append((current,lines))
  current=m[2] if not m[3].strip() else '';lines=[line]
 elif current is None:header.append(line)
 else:lines.append(line)
if current is not None and current in allowed:chunks.append((current,lines))
assert len(chunks)==len(allowed)==55300 and {n for n,ls in chunks}==allowed
assert all(not line.startswith('Block ') for n,ls in chunks for line in ls)
header[0]='Placement_File: design.place Placement_ID: SHA256:'+ep['inputs']['place']['sha256'];output=D/'seed.route'
with output.open('x') as f:f.write('\n'.join(header+[line for n,ls in chunks for line in ls])+'\n')
# Separate terminal-path import comparison validates full physical source coverage.
a=physical_paths(route);b=physical_paths(output);assert {n:a[n] for n in allowed}==b
actual={(name,path[0][0],path[-1][0]) for name,paths in b.items() for path in paths};expected={(ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']};assert actual==expected and sum(map(len,b.values()))==115572
bindings={**ready['bindings'],**closure([Path(__file__)]),str(readyfile):sha(readyfile),str(gp):sha(gp),str(epfile):sha(epfile),str(route):sha(route),str(output):sha(output),str(D/'protocol.json'):sha(D/'protocol.json')};assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all55300physical_NET_sections_preserved=True,all115572native_terminal_paths_byte_sequence_equal=True,no_global_Block_envelope=True,placement_changed=False,seed=str(output)),f,indent=2)
print('NO MOVE COMPLETE SEED VERIFIED',len(allowed),len(actual),flush=True)

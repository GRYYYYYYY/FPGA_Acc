"""Lean no-estimator control: wholeNET trim of original native route text."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from audit_native_route import NET
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_trim_seed_v1_2026-10-18';D.mkdir(exist_ok=False);start=time.perf_counter();G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18';P=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18';proofpath=P/'staged_input_verification_v1.json';proof=json.loads(proofpath.read_text());assert proof['all_native_logical_NET_local_pin_identities_preserved'] and all(sha(p)==h for p,h in proof['bindings'].items());geometry=json.loads((G/'protocol.json').read_text());old=json.loads(Path(geometry['previous_endpoint']).read_text());newfile=P/'demand/endpoints.json';new=json.loads(newfile.read_text());route=Path(geometry['previous_native_route']);routehash=sha(route);dirty=set(proof['affected']['affected_net_ids']);allowed={new['net_names'][str(q['net_id'])] for q in new['connections'] if q['net_id'] not in dirty};oldq={q['connection_id']:q for q in old['connections']};selected=[];pending=[]
for q in new['connections']:
 if q['net_id'] in dirty:pending.append(q['connection_id'])
 else:assert q==oldq[q['connection_id']];selected.append(q['connection_id'])
assert not set(selected)&set(pending) and set(selected)|set(pending)==set(oldq);header=[];chunks=[];current=None;lines=[]
for line in route.read_text().splitlines():
 m=NET.match(line)
 if m:
  if current is not None and current in allowed:chunks.append((current,lines))
  current=m[2];lines=[line]
 elif current is None:header.append(line)
 else:lines.append(line)
if current is not None and current in allowed:chunks.append((current,lines))
assert len({name for name,lines in chunks})==len(chunks)==len(allowed);assert {name for name,lines in chunks}==allowed;assert header[0].startswith('Placement_File:');header[0]='Placement_File: design.place Placement_ID: SHA256:'+new['inputs']['place']['sha256'];out=D/'seed.route'
with out.open('x') as f:f.write('\n'.join(header+[line for name,lines in chunks for line in lines])+'\n')
assert sha(route)==routehash
bindings={**proof['bindings'],str(proofpath):sha(proofpath),str(G/'protocol.json'):sha(G/'protocol.json'),str(route):routehash,str(newfile):sha(newfile),str(out):sha(out),str(Path(__file__)):sha(__file__)}
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,retained_net_names=sorted(allowed),selected_connection_ids=selected,pending_connection_ids=pending,wholeNET_dirty_count=len(dirty),selected_connections=len(selected),pending_connections=len(pending),trim_seconds_before_receipt=time.perf_counter()-start,policy='Retain complete unchanged original native NET trace blocks exactly; only update placement header, no RR/RC search/floor, estimator history or feedback. All dirty closures pending. Current pin/logical identity inherited from full target input proof.',scope='Seed generation only; independent printed path/current-pin/capacity proof and native/canonical completion still pending. No target native route generated.'),f,indent=2);f.write('\n')
print('MMC TRIM SEED',len(selected),'selected',len(pending),'pending',len(allowed),'NETs',flush=True)

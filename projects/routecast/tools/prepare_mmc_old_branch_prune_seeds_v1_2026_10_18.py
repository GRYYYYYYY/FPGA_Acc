"""Cheap old-native branch retention: no new RR/RC/floor search."""
import json,sys,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from native_route_ledger_import_compact import physical_paths
from old_native_branch_prune_codec_v1 import scan,render
from audit_native_route import NODE
D=R/'experiments/mmc_old_branch_prune_seeds_v1_2026-10-18';D.mkdir();cache=Cache();rows=[];cp=R/'experiments/old_native_branch_prune_codec_core_v1_2026-10-18/verification.json';core=json.loads(cp.read_text());assert core['status']=='pass';G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(G.read_text());oldfile=Path(g['previous_endpoint']);old=json.loads(oldfile.read_text());oldroute=Path(g['previous_native_route']);proofpath=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/native/mmc/verification.json';proof=json.loads(proofpath.read_text());assert proof['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and proof['original_native_FULL_check_pass'] and proof['overflow_units']==0;bindings={**closure([Path(__file__)]),**core['bindings'],str(cp):sha(cp),**proof['bindings'],str(proofpath):sha(proofpath),str(G):sha(G),str(oldfile):sha(oldfile),str(oldroute):sha(oldroute)}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,case_order=['case_01','case_02','case_03'],policy='Keep every old physical terminal path whose CID/net/source/sink is unchanged; omit only directly changed queries. Unchanged wholeNET sections copied verbatim, partialNETs prune old branches in original sink order using old printed templates. No new graph XML parse, RC/floor search, model feedback or capacity prioritization. Authenticate graph epoch and source input proofs.',scope='Supplemental cheap-control seed preparation on exposed layouts, not a retrofit of completed15arm utility screen. Current original binary rejects partialNET seed delay maps; new isolated lookahead build requires no-seed/full-NET equivalence and final complete native/FULL/physical/canonical gates before any utility inference.'),f,indent=2)
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items());before=physical_paths(oldroute);header,sections,templates=scan(oldroute.read_text());oldqs={q['connection_id']:q for q in old['connections']};keys={(old['net_names'][str(q['net_id'])],q['source'],q['sink']):q['connection_id'] for q in old['connections']};assert len(keys)==len(oldqs)==115572;seen=set()
 for name,paths in before.items():
  assert {n for line in sections[name] if (m:=NODE.match(line)) for n in [int(m[1])]}=={n for path in paths for n,_ in path}
  for path in paths:cid=keys[name,path[0][0],path[-1][0]];assert cid not in seen;seen.add(cid)
 assert seen==set(oldqs)
 for case in ['case_01','case_02','case_03']:
  tick=time.perf_counter();I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case;ip=I/'staged_input_verification_v1.json';v=json.loads(ip.read_text());assert v['all_native_logical_NET_local_pin_identities_preserved'] and all(sha(p)==h for p,h in v['bindings'].items());epfile=I/'demand/endpoints.json';ep=json.loads(epfile.read_text());newqs={q['connection_id']:q for q in ep['connections']};assert ep['graph_sha256']==old['graph_sha256'] and newqs.keys()==oldqs.keys();selected={cid for cid in oldqs if oldqs[cid]==newqs[cid]};pending=set(newqs)-selected;assert pending==set(v['affected']['changed_connection_ids']);chunks=[];complete=partial=0
  for name,oldpaths in before.items():
   kept=[path for path in oldpaths if keys[name,path[0][0],path[-1][0]] in selected]
   if not kept:continue
   if len(kept)==len(oldpaths):chunks.append(sections[name]);complete+=1
   else:chunks.append([sections[name][0],'',*render(kept,templates[name]),'','']);partial+=1
  W=D/case;W.mkdir();h=list(header);assert h[0].startswith('Placement_File:');h[0]='Placement_File: design.place Placement_ID: SHA256:'+ep['inputs']['place']['sha256'];text=chr(10).join(h+[line for chunk in chunks for line in chunk])+chr(10);assert not any(line.startswith('Block ') for line in text.splitlines())
  with (W/'seed.route').open('x') as f:f.write(text)
  b={**bindings,**v['bindings'],str(ip):sha(ip),str(epfile):sha(epfile),str(D/'protocol.json'):sha(D/'protocol.json'),str(W/'seed.route'):sha(W/'seed.route')};row=dict(case=case,selected_connections=len(selected),pending_connections=len(pending),retained_complete_NETs=complete,retained_partial_NETs=partial,preparation_seconds=time.perf_counter()-tick)
  with (W/'receipt.json').open('x') as f:json.dump(dict(bindings=b,**row,selected_connection_ids=sorted(selected),pending_connection_ids=sorted(pending),no_new_RC_floor_search=True,independent_audit_pending=True,scope='PartialNET source branches only; no new route completion or native support claim.'),f,indent=2)
  rows.append(row);print('OLD BRANCH SEED',row,flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
with (D/'generation_complete.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,all3_branch_pruned_seeds_generated=True,independent_audits_pending=True),f,indent=2)

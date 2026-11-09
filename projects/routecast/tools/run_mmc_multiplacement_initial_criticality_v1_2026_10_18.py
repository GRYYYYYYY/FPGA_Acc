"""Paired old/new-placement initial native criticality observations, no routing."""
import json,sys,os,subprocess,time,shutil,math,struct,resource
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
D=R/'experiments/mmc_multiplacement_initial_criticality_v1_2026-10-18';D.mkdir();B=R/'build/native_initial_criticality_snapshot_v2_2026-10-10';oldproof=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10/verification.json';bp=B/'receipt.json';b=json.loads(bp.read_text());p=json.loads(oldproof.read_text());binary=B/'sequence_vpr';cache=Cache();rows=[];snapshots={};bindings={**closure([Path(__file__)]),**b['bindings'],**p['bindings'],str(bp):sha(bp),str(oldproof):sha(oldproof),str(binary):b['binary_sha256']}
g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());oldmeta=json.loads(Path(g['previous_endpoint']).read_text());oldsrc=Path(oldmeta['inputs']['net']['path']).parent;command=json.loads((oldproof.parent/'startup.json').read_text())['command'];assert command[0]==str(binary) and command[command.index('--read_rr_graph')+1]==oldmeta['inputs']['graph']['path']
oldcriticalities={x['connection_id']:x for x in json.loads((oldproof.parent/'initial_connection_criticalities.json').read_text())};oldkeys={(x['net'],x['local_sink_pin']):x['connection_id'] for x in oldcriticalities.values()};assert len(oldkeys)==115572
cases=['old','case_01','case_02','case_03'];inputs={}
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
with cache.installed():
 assert p['nonignored_pin_keys_exactly_manifest'] and all(sha(x)==h for x,h in bindings.items())
 for case in cases:
  W=D/case;W.mkdir();src=oldsrc if case=='old' else R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'mmc';manifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries' if case=='old' else R/'experiments/mmc_multiplacement_feedback_inputs_v1_2026-10-18'/case/'target.queries'
  if case!='old':
   ip=src.parent/'staged_input_verification_v1.json';iv=json.loads(ip.read_text());assert iv['all_native_logical_NET_local_pin_identities_preserved'] and all(sha(x)==h for x,h in iv['bindings'].items());bindings.update(iv['bindings']);bindings[str(ip)]=sha(ip)
  for name in ['design.blif','design.net','design.place']:
   shutil.copyfile(src/name,W/name);assert sha(src/name)==sha(W/name);bindings[str(src/name)]=sha(src/name);bindings[str(W/name)]=sha(W/name)
  bindings[str(manifest)]=sha(manifest);inputs[case]=dict(source=str(src),manifest=str(manifest),working_directory=str(W))
 with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,command=command,order=cases,inputs=inputs,child_address_space_bytes=32*2**30,timeout_seconds=None,observation='Existing verified REAL criticality wrapper enumerates all clustered sink pins at first invocation and exits0 before returning to connection routing. No route generated. Clear every ROUTECAST variable except initial snapshot path.',scope='Paired diagnostic on exposed layouts; tests global pre-routing timing signal, not candidate quality, complete STA guarantee, native FULL/route legality, heldout or speed gain.'),f,indent=2)
 for case in cases:
  W=Path(inputs[case]['working_directory']);manifest=Path(inputs[case]['manifest']);queries={}
  for line in manifest.read_text().splitlines():
   w=line.split()
   if w[0]=='Q':
    cid,net,pin,source,sink=map(int,w[1:]);assert cid not in queries and oldkeys[net,pin]==cid;queries[cid]=(net,pin,source,sink)
  assert len(queries)==115572;env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_INITIAL_CRITICALITY']=str(W/'criticality.tsv');print('INITIAL CRITICALITY START',case,flush=True);tick=time.perf_counter()
  with (W/'native.log').open('x') as log:status=subprocess.run(command,cwd=W,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit,timeout=None).returncode
  elapsed=time.perf_counter()-tick;(W/'terminal.json').write_text(json.dumps(dict(exit_code=status,seconds=elapsed)))
  assert status==0 and 'ROUTECAST INITIAL CRITICALITY SNAPSHOT 119473' in (W/'native.log').read_text() and not list(W.glob('*.route'))
  observed={}
  for index,line in enumerate((W/'criticality.tsv').read_text().splitlines(),1):
   w=line.split();assert len(w)==10 and w[0]=='C' and int(w[1])==index;key=int(w[2]),int(w[4]);assert key not in observed;value=float(w[5]);assert math.isfinite(value) and 0<=value<=float(w[6])+1e-7 and w[8] in ['0','1'] and w[9] in ['0','1'];observed[key]=w
  assert len(observed)==119473 and {key for key,w in observed.items() if w[8]=='0'}==set(oldkeys);assert sum(w[8]=='1' for w in observed.values())==3901
  records=[]
  for cid,(net,pin,source,sink) in sorted(queries.items()):
   w=observed[net,pin];prior=oldcriticalities[cid];assert int(w[3])==prior['global_pin'] and w[6]==prior['maximum_text'] and w[7]==prior['exponent_text'];records.append(dict(connection_id=cid,net=net,local_sink_pin=pin,global_pin=int(w[3]),source_rr=source,target_rr=sink,criticality_float32_text=w[5],maximum_text=w[6],exponent_text=w[7]))
  if case=='old':assert all(x==oldcriticalities[x['connection_id']] for x in records)
  else:assert set(observed)==set(snapshots['old']) and all(w[2:5]+w[6:]==snapshots['old'][key][2:5]+snapshots['old'][key][6:] for key,w in observed.items())
  snapshots[case]=observed
  with (W/'initial_connection_criticalities.json').open('x') as f:json.dump(records,f,separators=(',',':'))
  changed=[x for x in records if struct.pack('f',float(x['criticality_float32_text']))!=struct.pack('f',float(oldcriticalities[x['connection_id']]['criticality_float32_text']))];dirty=set() if case=='old' else set(json.loads((Path(inputs[case]['source']).parent/'staged_input_verification_v1.json').read_text())['affected']['affected_net_ids']);changednets={x['net'] for x in changed};delta=[abs(float(x['criticality_float32_text'])-float(oldcriticalities[x['connection_id']]['criticality_float32_text'])) for x in records];row=dict(case=case,status='SNAPSHOT_ONLY_EXIT0_NO_ROUTE',seconds=elapsed,all_sink_pins=len(observed),physical_queries=len(records),changed_float32_criticalities=len(changed),changed_NETs=len(changednets),changed_queries_outside_endpoint_closure=sum(x['net'] not in dirty for x in changed),changed_NETs_outside_endpoint_closure=len(changednets-dirty),max_abs_criticality_delta=max(delta),mean_abs_criticality_delta=sum(delta)/len(delta));rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2));print('INITIAL CRITICALITY DONE',row,flush=True)
  for file in W.iterdir():
   if file.is_file():bindings[str(file)]=sha(file)
 assert all(sha(x)==h for x,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,old_replay_equal_archived_initial_criticalities=True,all4_no_route_generated_and_all119473pin_classifications_pass=True,independent_comparison_audit_pending=True,digest=cache.snapshot(),scope='Initial native criticality snapshot only. No route generated or FULL claim; no global explanation proven from correlation or exposed-data promotion/latency/STA claim.'),f,indent=2)

"""Fresh fixed-placement cohort wall time, both arms complete canonical audits.
Versioned adapters preserve the frozen producers; no historical RR/model reuse.
"""
import ast,json,os,subprocess,sys,time,shutil,re
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
from canonical_reload_pin_index_expat_v3 import canonical_reload,binary as canonical_binary,identity
# Authenticate SHA-specific complete model and handoff admission; no MMC case gates.
ADMISSION=[R/'experiments/sha1_frozen_model_v1_2026-10-10/verification.json',R/'experiments/sha1_native_handoff_v1_2026-10-10/verification.json']
for path,gate in zip(ADMISSION,['complete_candidate_physical_and_events_pass','complete_seed_bytes_pin_bindings_selection_and_pending_equal']):
 proof=json.loads(path.read_text());assert proof[gate]
 assert all(sha(k)==v for k,v in proof['bindings'].items())
ROOT=R/'experiments/sha_resident_cpu_profile_seed_complete_workflow_v1_2026-10-10' 
ROOT.mkdir();AD=ROOT/'adapters';AD.mkdir()
pr=R/'experiments/sha1_frozen_model_v1_2026-10-10/protocol.json'
p=json.loads(pr.read_text());assert p['required']==6273;p['cases']=['sha1'];assert all(sha(k)==v for k,v in p['bindings'].items())
B=R/'build/native_live_seed_cpu_profile_v1_2026-10-10/sequence_vpr';ARCH=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
SOURCES=['native_live_seed_cpu_profile_adapter_v1.py','prepare_live_native_manifest_v1.py','run_native_live_seed_cpu_profile_model_v1.py','capture_sha_second_swap_rr_only_v1.py','prepare_freecores_native_demand_v1.py','verify_freecores_rr_endpoints_v1.py','verify_freecores_native_demand_v1.py','run_sha_resident_cpu_profile_seed_handoff_v1.py','verify_resident_demand_frame_physical_v4.py','verify_resident_events_actual_old_joint_fallback_linear_v9.py','run_shared_overflow_guard_audits_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_resident_events_actual_old_linear_direct_lattice_v12.py','verify_sha1_native_cold_expat_v1.py','verify_sha1_cold_canonical_ignored_pins_v1.py','select_resident_native_seed_subset_v1.py']
bindings={**{str(p):sha(p) for p in ADMISSION},**closure([Path(__file__),*[R/'tools'/x for x in SOURCES],R/'tools/native_resume_prototype/canonical_reload_pin_index_expat_v3.py']),str(pr):sha(pr),str(B):sha(B),str(ARCH):sha(ARCH),str(canonical_binary):sha(canonical_binary),str(identity):sha(identity)}
# All adapters created/frozen before either arm starts. Absolute project root preserves imports.
adapters={}
for mode in ['cold','seed']:
 base=ROOT/mode;base.mkdir()
 repl={'sha1_rr_only_v1_2026-10-10':str(base.relative_to(R/'experiments')/'rr'),'sha1_native_demand_v1_2026-10-10':str(base.relative_to(R/'experiments')/'demand'),'sha1_native_cold_v1_2026-10-10':str(base.relative_to(R/'experiments')/'native'),'sha1_cold_canonical_v1_2026-10-10':str(base.relative_to(R/'experiments')/'canonical')}
 for name in ['capture_sha_second_swap_rr_only_v1.py','verify_sha1_native_cold_expat_v1.py','verify_sha1_cold_canonical_ignored_pins_v1.py']:
  code=(R/'tools'/name).read_text().replace("R=Path(__file__).resolve().parents[1]",f'R=Path({str(R)!r})')
  for old,new in repl.items():code=code.replace(old,new)
  dest=AD/(mode+'_'+name);dest.write_text(code);bindings[str(dest)]=sha(dest);adapters[mode,name]=dest
fixed=R/'experiments/sha1_fixed_place_v1_2026-10-10'
for name in p['cases']:
 for f in ['design.blif','design.net','design.place']:bindings[str(fixed/name/f)]=sha(fixed/name/f)
protocol=dict(optimization='Thread CPU and wall profiling; Borrowed global-edge const storage full preflight; Profiling instrumentation; Known-source direct native edge getters; Single resident native RR search with freshly computed prices, full model audits before seed import, same-process routing; Python estimate transactions and full seed handoff; namespace-aware Expat v3 complete native and canonical branch audit scans; indexed actual-old budgets and exact undo-stack fallback; hybrid singleton balanced bidirectional v2 and multi-target forward radix, indexed native name membership v2 and seed serializer v2, canonical pin index v2 in both arms; complete audits retained; actual-old linear fallback event audit v9 and frame audit v4 with exact immutable Fraction electrical caching use complete direct readonly XML-array unique-pair RC lattice scans and authenticated channel spans; current-arm resident graph handoff with model and native seed selection/serialization in one subprocess, complete validations retained; two independent XML readers loaded once per current-arm audit subprocess, unchanged complete frame and actual-old fallback event audit bodies',bindings=bindings,cases=p['cases'],arm_order=['cold','seed'],timer='Single continuous perf_counter per full SHA arm: starts before fresh RR export/copy/extract; ends after complete native physical and canonical independent ignored-pin audits plus final binding authentication. All subprocess launch, export/mapping/scope audits and hash costs inside. Seed additionally exact initial floors/model/two feedback rounds/full frame+event audits/unchanged selection+serialization. One native service process waits through model/selection/serialization/full model audits, then imports seed and continues routing without an extra unseeded route. Native_process_seconds seed diagnostic denotes resume-to-finish only, not whole native lifetime; full lifetime overlaps model/audits and is not added separately. No cached historical RR/model/path/price. Pack/place upstream common excluded. Adapter preparation/protocol creation common excluded. Final receipt and stage-file SHA archival after both arm timers excluded; stage observations/write costs remain inside arm timers.',limitations='Single sequential full SHA trial with hybrid prospective model and indexed canonical reload; complete candidate SHA states and events independently certified, fresh run has its own full event audit, cold then seed, no process/cache stability inference or silicon/HDL/strict-heldout timing claim. Earlier label outcomes already known; this is a cost measurement, not prospective accuracy evidence. All failures retained, no retries.',timeout_per_stage_seconds=1200)
(ROOT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[];stages=[]
def run(cmd,log,cwd=R,extra=None):
 stage_tick=time.perf_counter()
 with log.open('w') as f:
  result=subprocess.run([str(x) for x in cmd],cwd=cwd,env={**env,**(extra or {})},stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 stages.append(dict(log=str(log),seconds=time.perf_counter()-stage_tick,exit_code=result.returncode))
 (ROOT/'stages.json').write_text(json.dumps(stages,indent=2)+'\n')
 assert result.returncode==0,(cmd,result.returncode,str(log))
for mode in protocol['arm_order']:
 base=ROOT/mode;tick=time.perf_counter();row=dict(arm=mode,status='RUNNING');rows.append(row);(ROOT/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
 try:
  run([sys.executable,adapters[mode,'capture_sha_second_swap_rr_only_v1.py']],base/'export.log')
  for name in p['cases']:
   rr=base/'rr'/name;front=base/'demand'/name
   run([sys.executable,R/'tools/verify_freecores_rr_endpoints_v1.py',rr,base/'rr/receipt.json'],base/(name+'_rr_audit.log'))
   run([sys.executable,R/'tools/prepare_freecores_native_demand_v1.py',rr,front],base/(name+'_scope.log'))
   run([sys.executable,R/'tools/verify_freecores_native_demand_v1.py',front,rr/'endpoints.json'],base/(name+'_scope_audit.log'))
   epfile=front/'endpoints.json';ep=json.loads(epfile.read_text());native=base/'native'/name;native.mkdir(parents=True)
   for f in ['design.blif','design.net','design.place']:shutil.copyfile(rr/f,native/f)
   extra={};required=len(ep['connections']);graph=rr/'rr_graph.xml'
   if mode=='seed':
    resident=base/'model'/name;handoff=base/'handoff'/name
    run([sys.executable,R/'tools/run_sha_resident_cpu_profile_seed_handoff_v1.py',name,epfile,handoff,native,resident],base/(name+'_model_native_seed.log'))
    shared=json.loads((resident/'shared_audit_receipt.json').read_text());assert shared['all_three_complete_audits_pass'] and shared['complete_audit_bodies_AST_preserved'] and shared['fresh_independent_graph_context'];assert all(sha(k)==h for k,h in shared['bindings'].items())
    handoff_receipt=json.loads((handoff/'receipt.json').read_text())
    for section in ['bindings','files']:assert all(sha(k)==h for k,h in handoff_receipt[section].items())
    assert handoff_receipt['required_connections']==required and handoff_receipt['selected_connections']+handoff_receipt['pending_connections']==required
    extra={'ROUTECAST_NATIVE_SEED':str(native/'seed.route')}
   cmd=[str(B),str(ARCH),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
   if mode=='seed':
    sr=json.loads((native/'service_receipt.json').read_text());assert sr['seed_imported'] and sr['exit_code']==0 and sr['command']==cmd
    for section in ['bindings','files']:assert all(sha(k)==h for k,h in sr[section].items())
    seconds=sr['seed_resume_to_finish_seconds']
   else:
    nt=time.perf_counter();run(cmd,native/'native.log',native,extra);seconds=time.perf_counter()-nt
   log=(native/'native.log').read_text();assert 'VPR succeeded' in log and ('NET-aware seed imported' in log)==(mode=='seed')
   receipt=dict(exit_code=0,status='NATIVE_SUCCESS_PENDING_INDEPENDENT_AUDIT',bindings={str(graph):sha(graph),str(epfile):sha(epfile)},files={str(f):sha(f) for f in native.iterdir() if f.is_file()},command=cmd,native_process_seconds=seconds,diagnostic_cpd_ns=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]),wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]))
   (native/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');run([sys.executable,adapters[mode,'verify_sha1_native_cold_expat_v1.py'],name],base/(name+'_native_audit.log'))
   (base/'canonical').mkdir(exist_ok=True);inv=Inventory(graph);candidate=dict(files=receipt['files'],command=cmd,width=128,decision='R',cpd_ns=receipt['diagnostic_cpd_ns']);canonical_tick=time.perf_counter();result=canonical_reload(candidate,native,base/'canonical'/name,inv);assert result['semantic_consistency_gate_pass']
   stages.append(dict(arm=mode,stage='canonical_reload_complete',seconds=time.perf_counter()-canonical_tick))
   (ROOT/'stages.json').write_text(json.dumps(stages,indent=2)+'\n')
   canonical=base/'canonical';canonical.mkdir(exist_ok=True);cp=canonical/'receipt.json';data=json.loads(cp.read_text()) if cp.exists() else dict(bindings={},rows=[]);data['rows'].append(dict(name=name,mode=mode,status='SEMANTIC_CANONICAL_PASS',canonical=result));cp.write_text(json.dumps(data,indent=2)+'\n');print(mode,name,'native+canonical PASS',flush=True)
  run([sys.executable,adapters[mode,'verify_sha1_cold_canonical_ignored_pins_v1.py']],base/'ignored_audit.log')
  assert all(sha(k)==v for k,v in bindings.items());row.update(status='COMPLETE_VERIFIED',continuous_arm_seconds=time.perf_counter()-tick)
 except Exception as error:
  row.update(status='FAILED_OR_TIMEOUT',error=repr(error),elapsed_seconds=time.perf_counter()-tick)
 (ROOT/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(mode,row,flush=True)
 if row['status']!='COMPLETE_VERIFIED':break
(ROOT/'receipt.json').write_text(json.dumps(dict(bindings=bindings,files={str(ROOT/'stages.json'):sha(ROOT/'stages.json')} if (ROOT/'stages.json').is_file() else {},rows=rows,scope=protocol['limitations']),indent=2)+'\n')

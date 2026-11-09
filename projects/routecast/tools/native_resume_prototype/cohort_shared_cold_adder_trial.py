"""Frozen development feedback strategy; cold labels evaluated only afterwards."""
import json,os,re,shutil,subprocess,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from canonical_reload_inventory import canonical_reload
from prepare_canonical_inventory import prepare_canonical
from audit_shared_inventory import audit
from shared_rr_inventory import SharedRRInventory
from source_binding import closure
from partial_seed_state import publish_partial_seed
from fractions import Fraction as F
from reusable_rr_floor_context import ReusableRRFloors
from shared_inventory_exchange import exchange
from current_global_budget_buffered import repair
from serialize_shared_inventory import serialize
ROOT=Path(__file__).resolve().parents[2];mode=sys.argv[1];assert mode in ('workflow','cold')
width=32;index=int(sys.argv[2]);assert index in range(1,10)
start=time.perf_counter();out=ROOT/f'experiments/native_resume_shared_cold_adder_step{index}_{mode}_2026-10-07';out.mkdir(exist_ok=False)
source=ROOT/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits'
targetfile=ROOT/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{(index-1)%3+1}_endpoints.json';target=json.loads(targetfile.read_text())
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
original=shared/'build_tileplace_vpr/vpr/vpr';private=ROOT/'build/native_resume_singlepass_floor_2026-10-07/routecast_resume_vpr';binary=private
arch=shared/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';graph=Path(target['inputs']['graph']['path']);place=Path(target['inputs']['place']['path']);net=Path(target['inputs']['net']['path'])
inputs={str(p):sha(p) for p in (targetfile,source/'design.blif',place,net,graph,binary,arch)}
assert sha(graph)==target['graph_sha256'] and all(sha(v['path'])==v['sha256'] for v in target['inputs'].values())
if mode=='workflow':
 oldfile=Path(globals().get('previous_endpoint',ROOT/'experiments/adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json'));old=json.loads(oldfile.read_text());seed=Path(globals().get('previous_seed',source/'design.route'))
 assert old['inputs']['net']==target['inputs']['net'] and old['graph_sha256']==target['graph_sha256'] and old['net_names']==target['net_names']
 inputs.update({str(p):sha(p) for p in (oldfile,seed)})
 oldrows={q['connection_id']:q for q in old['connections']};assert {q['connection_id'] for q in target['connections']}==oldrows.keys()
 removed={target['net_names'][str(q['net_id'])] for q in target['connections'] if (q['source'],q['sink'])!=(oldrows[q['connection_id']]['source'],oldrows[q['connection_id']]['sink'])}
if mode=='workflow':
 report_input=Path(globals().get('previous_report',source/'report_timing.setup.rpt'));old_log=Path(globals().get('previous_log',source/'vpr_stdout.log'));assert 'VPR succeeded' in old_log.read_text();inputs.update({str(p):sha(p) for p in (report_input,old_log)})
floor_begin=time.perf_counter()
kernel=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor'
ctx=globals().get('shared_floor_context')
if ctx is None:ctx=ReusableRRFloors(targetfile,kernel,out/'floor_context')
floor_result=ctx.query(targetfile)
inventory=globals().get('shared_inventory')
if inventory is None:inventory=SharedRRInventory(ctx)
pairs={}
for answer in floor_result['answers']:
 q=answer['query'];key=(q['source'],q['sink']);value=answer['minimum_integer'];assert key not in pairs or pairs[key]==value;pairs[key]=value
floor_file=out/'rr_floors.txt'
with floor_file.open('w') as stream:
 stream.write(f'ROUTECAST_FLOORS_SECONDS_V1 {ctx.digest} {ctx.n} {len(pairs)}\n')
 for (src,sink),value in sorted(pairs.items()):stream.write(f'{src} {sink} {float(F(value,ctx.rc.scale)):.17g}\n')
inputs.update(ctx.bindings);inputs[str(floor_file)]=sha(floor_file)
floor_stage=dict(stage='independent_target_rr_floor_preparation',seconds=time.perf_counter()-floor_begin,construction_seconds=0 if globals().get('shared_floor_context') is not None else ctx.construction_seconds,query_seconds=floor_result['total_seconds'],connections=len(floor_result['answers']),distinct_pairs=len(pairs),floor_file_sha256=sha(floor_file))
protocol=dict(mode=mode,inputs=inputs,sources=closure([Path(__file__)]),policy='Endpoint-changed wholeNET release plus old published native worst-path output NET if endpoint-stable and present in seed; no target first attempt or target cold labels read. One initial private-native FULL/STA with exact identity conversion and physical/endpoint proof; workflow intermediate original-native analysis deferred to final proof, then workflow-only full-NET compiled exchange and current-own-report conditioned positive-gap wholeNET global-wire-budget repair using the same context, serialization, original-native synchronization and final canonical FULL/STA/resource/endpoint proof. Development diagnostic fixed rule, missing NET delay1ns; same privately corrected CBRR index and initial delay tolerance1.01 and state-triggered wholeNET and single marking pass with subsequent clearing and independent target RR floor binary in both modes, not unchanged original cold.',scope='Prepared endpoints/mapped design/packed NET/original seed+RR; includes independently constructed target RR floors (separate once-per-sequence contexts on both sides), hashing, conversion, all native attempts, feedback, selected canonical and full physical/endpoint proof; excludes original mapping/seed routing/endpoint extraction/RR generation/compile. Continuous complete serial observation; both floor initialization and all workflow-only exchange/conversion/native proof paid.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');stages=[floor_stage]
def norm(p):return {name:Counter(ps) for name,ps in physical_paths(p).items() if ps}
def partial(excluded,name):
 begin=time.perf_counter();p=out/name;receipt=publish_partial_seed(seed,place,targetfile,excluded,p)
 stages.append(dict(stage=name,seconds=time.perf_counter()-begin,removed_nets=len(excluded),retained_connections=receipt['retained_connections'],sha256=receipt['output_sha256'],state_adapter=receipt));return p

def native(name,seedfile=None):
 begin=time.perf_counter();work=out/name;work.mkdir()
 for p,n in ((source/'design.blif','design.blif'),(net,'design.net'),(place,'design.place')):shutil.copyfile(p,work/n)
 cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','300','--num_workers','1','--check_route','full','--max_router_iterations','100','--seed','1']
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 env['ROUTECAST_RR_FLOORS_FILE']=str(floor_file)
 if seedfile:env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=str(seedfile),ROUTECAST_RESUME_ALLOW_PARTIAL='1')
 with (work/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 text=(work/'run.log').read_text();assert code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
 result=dict(work=str(work),cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),width=width,decision='R',command=cmd,exit_code=code,files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
 stages.append(dict(stage=name,seconds=time.perf_counter()-begin,native=result));return result
feedback=None
if mode=='workflow':
 begin=time.perf_counter();report_path=Path(globals().get('previous_report',source/'report_timing.setup.rpt'))
 report=report_path.read_text().split('#Path 2')[0]
 match=re.search(r'^Endpoint\s*:\s*out:(\S+)\.outpad\[0\]',report,re.M)
 candidate=match[1] if match else None
 eligible=bool(candidate and candidate not in removed and candidate in norm(seed))
 feedback=dict(net=candidate,eligible=eligible,report_sha256=sha(report_path));stages.append(dict(stage='old_critical_predecision',seconds=time.perf_counter()-begin,decision=feedback))
 if eligible:removed.add(candidate)
 selected=native('first',partial(removed,'first_seed.route'))
else:selected=native('first')
begin=time.perf_counter();work=Path(selected['work']);metadata=dict(selected);metadata['cpd_ns']=float(selected['cpd_ns'])
if mode=='workflow':canonical=prepare_canonical(metadata,work,out/'canonical',inventory);assert canonical['native_analysis_performed'] is False
else:
 canonical=canonical_reload(metadata,work,out/'canonical',inventory);assert canonical['mismatches']==canonical['fixups']==0
route=out/'canonical/design.route';a=audit(graph,route,inventory);assert a['overflow_units']==0 and len(a['connections'])==len(target['connections'])
paths=norm(route);assert paths==norm(work/'output.route')
actual=Counter((n,p[0][0],p[-1][0]) for n,ps in paths.items() for p,count in ps.items() for _ in range(count))
expected=Counter((target['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in target['connections']);assert actual==expected
if mode=='cold':assert int(re.findall(r'Total wirelength:\s*(\d+)',(out/'canonical/reload.log').read_text())[-1])==selected['wirelength']
stages.append(dict(stage='selected_canonical_physical_endpoint_proof',seconds=time.perf_counter()-begin,original_native_intermediate_analysis_performed=mode=='cold'))

if mode=='workflow':
 begin=time.perf_counter();before_cpd=selected['cpd_ns'];before_wire=selected['wirelength'];ex=exchange(ctx,targetfile,out/'canonical/design.route',out/'exchange',inventory);candidate=ex['records'];gb=repair(ctx,inventory,targetfile,candidate,out/'canonical/report_timing.setup.rpt',before_wire,out/'global_budget');candidate=gb['records'];native_out=out/'exchange_native';native_out.mkdir()
 for file in ('design.blif','design.net','design.place'):shutil.copyfile(out/'canonical'/file,native_out/file)
 serialized,_=serialize(dict(records=candidate),targetfile,out/'canonical/identity.jsonl',native_out/'design.place',inventory);(native_out/'design.route').write_text(serialized);expected_paths=norm(native_out/'design.route')
 cmd=canonical['command'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 with (native_out/'native.log').open('w') as stream:code=subprocess.run(cmd,cwd=native_out,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
 log=(native_out/'native.log').read_text();assert code==0 and 'VPR succeeded' in log;cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1];wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);shutil.copyfile(native_out/'design.route',native_out/'output.route');metadata_cmd=list(cmd);metadata_cmd[metadata_cmd.index('--analysis')]='--route'
 metadata=dict(width=width,decision='R',command=metadata_cmd,cpd_ns=float(cpd),files={str(file):sha(file) for file in native_out.iterdir() if file.is_file()});canonical=canonical_reload(metadata,native_out,out/'exchange_canonical',inventory);assert canonical['fixups']==canonical['mismatches']==0;assert norm(out/'exchange_canonical/design.route')==expected_paths
 a=audit(graph,out/'exchange_canonical/design.route',inventory);assert a['overflow_units']==0 and len(a['connections'])==len(target['connections']);actual=Counter((n,p[0][0],p[-1][0]) for n,ps in expected_paths.items() for p,count in ps.items() for _ in range(count));assert actual==expected
 selected=dict(selected,work=str(native_out),cpd_ns=cpd,wirelength=wire)
 stages.append(dict(stage='shared_context_exchange_materialization_native_and_full_proof',seconds=time.perf_counter()-begin,exchange_conversion_seconds=ex['conversion_seconds'],compiled_child_seconds=ex['compiled_child_seconds'],exchange_total_seconds=ex['total_seconds'],before_cpd_ns=before_cpd,before_wirelength=before_wire,final_cpd_ns=cpd,final_wirelength=wire,unchanged_floor_cache=ex['unchanged_floor_cache'],global_budget_seconds=gb['total_seconds'],global_budget_accepted_nets=[row['net'] for row in gb['rows'] if row['accepted']],global_budget_wire=gb['final_wire']))

assert all(sha(p)==h for p,h in {**protocol['inputs'],**protocol['sources']}.items())
result=dict(protocol_sha256=sha(out/'protocol.json'),mode=mode,internal_seconds=time.perf_counter()-start,stages=stages,feedback=feedback,selected_work=selected['work'],cpd_ns=selected['cpd_ns'],wirelength=selected['wirelength'],canonical=canonical,physical_audit=a,all_target_endpoints_match=True,raw_canonical_paths_preserved=True,files={str(f):sha(f) for f in out.rglob('*') if f.is_file()},scope=protocol['scope'])
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(mode,result['internal_seconds'],result['cpd_ns'],result['wirelength'],feedback)

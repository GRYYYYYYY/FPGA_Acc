"""Frozen development feedback strategy; cold labels evaluated only afterwards."""
import json,os,re,shutil,subprocess,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from loaded_native_canonical_reload import canonical_reload
from stream_native_route_audit_cached import audit
from freeze_priority_family import closure
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];mode=sys.argv[1];assert mode in ('workflow','cold')
start=time.perf_counter();tag=sys.argv[2];assert tag in ('p0','p1','p2','p3')
out=ROOT/f'experiments/native_resume_precritical_repeat_{tag}_{mode}_2026-10-07';out.mkdir(exist_ok=False)
source=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128'
targetfile=ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target_endpoints.json';target=json.loads(targetfile.read_text())
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
original=shared/'build_tileplace_vpr/vpr/vpr';private=ROOT/'build/native_resume_target_partial_v7_2026-10-07/routecast_resume_vpr';binary=private if mode=='workflow' else original
arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';graph=Path(target['inputs']['graph']['path']);place=Path(target['inputs']['place']['path']);net=Path(target['inputs']['net']['path'])
inputs={str(p):sha(p) for p in (targetfile,source/'design.blif',place,net,graph,binary,arch)}
assert sha(graph)==target['graph_sha256'] and all(sha(v['path'])==v['sha256'] for v in target['inputs'].values())
if mode=='workflow':
 oldfile=ROOT/'experiments/mux_live_placement_updates_2026-10-06/w32/original_endpoints.json';old=json.loads(oldfile.read_text());seed=source/'design.route'
 assert old['inputs']['net']==target['inputs']['net'] and old['graph_sha256']==target['graph_sha256'] and old['net_names']==target['net_names']
 inputs.update({str(p):sha(p) for p in (oldfile,seed)})
 oldrows={q['connection_id']:q for q in old['connections']};assert {q['connection_id'] for q in target['connections']}==oldrows.keys()
 removed={target['net_names'][str(q['net_id'])] for q in target['connections'] if (q['source'],q['sink'])!=(oldrows[q['connection_id']]['source'],oldrows[q['connection_id']]['sink'])}
if mode=='workflow':
 report_input=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32/canonical/report_timing.setup.rpt'
 old_receipt=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/receipt.json'
 old_proof=json.loads(old_receipt.read_text());old_row=next(x for x in old_proof['rows'] if x['width']==32)
 assert sha(report_input)==old_row['files'][str(report_input)]
 inputs.update({str(p):sha(p) for p in (report_input,old_receipt)})
protocol=dict(mode=mode,inputs=inputs,sources=closure([Path(__file__)]),policy='Endpoint-changed wholeNET release plus old published native worst-path output NET if endpoint-stable and present in seed; no target first attempt or target cold labels read. Exactly one native attempt then selected proof. Development retrospective fixed rule, missing NET delay1ns.',scope='Prepared endpoints/mapped design/packed NET/original seed+RR; includes hashing, conversion, all native attempts, feedback, selected canonical and full physical/endpoint proof; excludes original mapping/seed routing/endpoint extraction/RR generation/compile. Single serial observation.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');stages=[]
def norm(p):return {name:Counter(ps) for name,ps in physical_paths(p).items() if ps}
def partial(excluded,name):
 begin=time.perf_counter();lines=seed.read_text().splitlines(keepends=True);lines[0]=f'Placement_File: design.place Placement_ID: SHA256:{sha(place)}\n';keep=True;output=[]
 for line in lines:
  m=re.match(r'^Net\s+\d+\s+\((.*)\)\s*$',line)
  if m:keep=m[1] not in excluded
  if keep:output.append(line)
 p=out/name;p.write_text(''.join(output));paths=norm(p);assert paths=={n:ps for n,ps in norm(seed).items() if n not in excluded}
 actual=Counter((n,path[0][0],path[-1][0]) for n,ps in paths.items() for path,count in ps.items() for _ in range(count))
 expected=Counter((target['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in target['connections'] if target['net_names'][str(q['net_id'])] not in excluded)
 assert actual==expected
 stages.append(dict(stage=name,seconds=time.perf_counter()-begin,removed_nets=len(excluded),retained_connections=sum(actual.values()),sha256=sha(p)));return p

def native(name,seedfile=None):
 begin=time.perf_counter();work=out/name;work.mkdir()
 for p,n in ((source/'design.blif','design.blif'),(net,'design.net'),(place,'design.place')):shutil.copyfile(p,work/n)
 cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--check_route','full','--max_router_iterations','100','--seed','1']
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 if seedfile:env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=str(seedfile),ROUTECAST_RESUME_ALLOW_PARTIAL='1')
 with (work/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 text=(work/'run.log').read_text();assert code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
 result=dict(work=str(work),cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),width=32,decision='R',command=cmd,exit_code=code,files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
 stages.append(dict(stage=name,seconds=time.perf_counter()-begin,native=result));return result
feedback=None
if mode=='workflow':
 begin=time.perf_counter();report_path=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32/canonical/report_timing.setup.rpt'
 report=report_path.read_text().split('#Path 2')[0]
 match=re.search(r'^Endpoint\s*:\s*out:(\S+)\.outpad\[0\]',report,re.M)
 candidate=match[1] if match else None
 eligible=bool(candidate and candidate not in removed and candidate in norm(seed))
 feedback=dict(net=candidate,eligible=eligible,report_sha256=sha(report_path));stages.append(dict(stage='old_critical_predecision',seconds=time.perf_counter()-begin,decision=feedback))
 if eligible:removed.add(candidate)
 selected=native('first',partial(removed,'first_seed.route'))
else:selected=native('first')
begin=time.perf_counter();work=Path(selected['work']);metadata=dict(selected);metadata['cpd_ns']=float(selected['cpd_ns'])
canonical=canonical_reload(metadata,work,out/'canonical');assert canonical['mismatches']==canonical['fixups']==0
route=out/'canonical/design.route';a=audit(graph,route);assert a['overflow_units']==0 and len(a['connections'])==len(target['connections'])
paths=norm(route);assert paths==norm(work/'output.route')
actual=Counter((n,p[0][0],p[-1][0]) for n,ps in paths.items() for p,count in ps.items() for _ in range(count))
expected=Counter((target['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in target['connections']);assert actual==expected
assert int(re.findall(r'Total wirelength:\s*(\d+)',(out/'canonical/reload.log').read_text())[-1])==selected['wirelength']
stages.append(dict(stage='selected_canonical_physical_endpoint_proof',seconds=time.perf_counter()-begin))
assert all(sha(p)==h for p,h in {**protocol['inputs'],**protocol['sources']}.items())
result=dict(protocol_sha256=sha(out/'protocol.json'),mode=mode,internal_seconds=time.perf_counter()-start,stages=stages,feedback=feedback,selected_work=selected['work'],cpd_ns=selected['cpd_ns'],wirelength=selected['wirelength'],canonical=canonical,physical_audit=a,all_target_endpoints_match=True,raw_canonical_paths_preserved=True,files={str(f):sha(f) for f in out.rglob('*') if f.is_file()},scope=protocol['scope'])
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(mode,result['internal_seconds'],result['cpd_ns'],result['wirelength'],feedback)

"""Fixed wholeNET identity crossover, both trees and cases, all native audits."""
import json,sys,os,subprocess,shutil,time,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
from shared_compact_native_inventory_v1 import Inventory
from canonical_reload_ignored_invariants_v1 import canonical_reload,binary as CB,identity
S=R/'experiments/freecores_common_NET_seed_v1_2026-10-08';rp=S/'receipt.json';r=json.loads(rp.read_text());assert all(sha(k)==h for group in ['bindings','files'] for k,h in r[group].items()) and all(x['all_wholeNET_greedy_capacity_and_full_query_partition_checks_pass'] for x in r['rows']);D=R/'experiments/freecores_common_NET_native_v1_2026-10-08';D.mkdir();B=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';ARCH=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';bindings={**closure([Path(__file__)]),str(rp):sha(rp),str(B):sha(B),str(ARCH):sha(ARCH),str(CB):sha(CB),str(identity):sha(identity)}
# Freeze ignored-pin adapters before any new route labels.
adapters={}
for mode in ['baseline','no_ipin']:
 out=D/mode;out.mkdir();(out/'canonical').mkdir();code=(R/'tools/verify_freecores_seed_canonical_ignored_pins_v1.py').read_text().replace("R/'experiments/freecores_seed_canonical_v1_2026-10-08'",repr(str(out/'canonical')));code=code.replace("out="+repr(str(out/'canonical')), "out=Path("+repr(str(out/'canonical'))+")");dest=D/(mode+'_ignored_pin_audit.py');dest.write_text(code);bindings[str(dest)]=sha(dest);adapters[mode]=dest
protocol=dict(bindings=bindings,cases=['8051','xtea'],tree_modes=['baseline','no_ipin'],order='8051 baseline,8051 no_ipin,xtea baseline,xtea no_ipin; then both complete ignored-pin audits',timeout_seconds=1200,scope='Development crossover conditioned on common admitted wholeNET set. Same retained/pending CID sets, only input trees differ. Native routing still all required; no discarded physical query. No tail-label selection or tuning. Single diagnostic component timers not fresh continuous workflow or stable gain; all failures retained.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for name in protocol['cases']:
 graph=R/'experiments/freecores_rr_only_v1_2026-10-08'/name/'rr_graph.xml';epfile=R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json';ep=json.loads(epfile.read_text());required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);xml=Inventory(graph);xml.validate(graph,ep['graph_sha256']);bindings[str(graph)]=sha(graph);bindings[str(epfile)]=sha(epfile)
 subsets=[json.loads((S/name/m/'subset.json').read_text()) for m in protocol['tree_modes']];assert subsets[0]['pending']==subsets[1]['pending'] and {x['connection_id'] for x in subsets[0]['records']}=={x['connection_id'] for x in subsets[1]['records']}
 for mode in protocol['tree_modes']:
  w=D/mode/name;w.mkdir();src=S/name/mode;row=dict(name=name,tree_mode=mode,status='FAILED_OR_TIMEOUT');tick=time.perf_counter()
  for f in ['design.blif','design.net','design.place','seed.route']:shutil.copyfile(src/f,w/f)
  cmd=[str(B),str(ARCH),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
  try:
   nt=time.perf_counter()
   with (w/'native.log').open('w') as f:code=subprocess.run(cmd,cwd=w,env={**env,'ROUTECAST_NATIVE_SEED':str(w/'seed.route')},stdout=f,stderr=subprocess.STDOUT,timeout=1200).returncode
   row.update(exit_code=code,native_seconds=time.perf_counter()-nt);text=(w/'native.log').read_text();assert code==0 and 'VPR succeeded' in text and 'NET-aware seed imported feasible=1' in text and 'Completed routing consistency check successfully.' in text
   a=audit(graph,w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections']);assert observed==required and a['overflow_units']==0;(w/'physical_audit.json').write_text(json.dumps(a)+'\n');cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);row.update(iterations=int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]),wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),diagnostic_cpd_ns=cpd,all_required_connections=sum(required.values()),complete_native_FULL_and_physical_audit_pass=True)
   files={str(f):sha(f) for f in w.iterdir() if f.is_file()};candidate=dict(files=files,command=cmd,width=128,decision='R',cpd_ns=cpd);canonical=canonical_reload(candidate,w,D/mode/'canonical'/name,xml);assert canonical['semantic_consistency_gate_pass'];crp=D/mode/'canonical/receipt.json';cp=json.loads(crp.read_text()) if crp.exists() else dict(bindings={},rows=[]);cp['rows'].append(dict(name=name,mode=mode,status='SEMANTIC_CANONICAL_PASS',canonical=canonical));crp.write_text(json.dumps(cp,indent=2)+'\n');row.update(status='COMPLETE_PHYSICAL_AND_CANONICAL_PASS',canonical=canonical)
  except Exception as error:row['error']=repr(error)
  row.update(component_native_plus_audit_seconds=time.perf_counter()-tick,files={str(f):sha(f) for f in w.iterdir() if f.is_file()});rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,mode,row['status'],row.get('iterations'),row.get('error'),flush=True)
ignored=[]
for mode in protocol['tree_modes']:
 with (D/(mode+'_ignored.log')).open('w') as f:code=subprocess.run([sys.executable,str(adapters[mode])],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1200).returncode
 ignored.append(dict(tree_mode=mode,exit_code=code));print('ignored',mode,code,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,ignored=ignored,all_complete_native_physical_canonical_and_ignored_pass=all(x['status']=='COMPLETE_PHYSICAL_AND_CANONICAL_PASS' for x in rows) and all(x['exit_code']==0 for x in ignored)),indent=2)+'\n')

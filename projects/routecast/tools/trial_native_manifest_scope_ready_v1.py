"""Complete native getter/pin preflight; controlled EOF, no searches or routing."""
from pathlib import Path
import json,os,subprocess,shutil,resource,selectors,time
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];P=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10';B=R/'build/native_live_seed_manifest_scope_v1_2026-10-10';O=R/'experiments/native_manifest_scope_ready_v1_2026-10-10';O.mkdir(exist_ok=True);build=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==build['binary_sha256'] and all(sha(p)==h for p,h in build['source_sha256'].items());results=[];bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(B/'receipt.json'):sha(B/'receipt.json'),str(B/'sequence_vpr'):sha(B/'sequence_vpr')}
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
for case,variant in [('sha1','valid'),('mmc','valid'),('sha1','wrong_nodes'),('sha1','wrong_edges'),('sha1','wrong_queries'),('sha1','missing_pin')]:
 proof=json.loads((P/(case+'.verification.json')).read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings.update(proof['bindings']);ep=json.loads(Path(proof['endpoint']).read_text());work=O/(case+'_'+variant);work.mkdir();text=(P/(case+'.queries')).read_text();lines=text.splitlines();dims=lines[0].split()
 if variant.startswith('wrong_'):
  field={'wrong_nodes':1,'wrong_edges':2,'wrong_queries':3}[variant];dims[field]=str(int(dims[field])+1);lines[0]=' '.join(dims)
 elif variant=='missing_pin':
  i=next(i for i,l in enumerate(lines) if l.startswith('Q '));del lines[i];dims[3]=str(int(dims[3])-1);lines[0]=' '.join(dims)
 manifest=work/'queries.txt';manifest.write_text('\n'.join(lines)+'\n');source=Path(ep['inputs']['net']['path']).parent
 for n in ['design.blif','design.net','design.place']:shutil.copyfile(source/n,work/n)
 arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';graph=Path(ep['inputs']['graph']['path']);command=[str(B/'sequence_vpr'),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
 rr,rw=os.pipe();sr,sw=os.pipe();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_INPROCESS_QUERIES=str(manifest),ROUTECAST_INPROCESS_FLOORS=str(work/'unused.tsv'),ROUTECAST_LIVE_REQUEST_FD=str(rr),ROUTECAST_LIVE_RESPONSE_FD=str(sw));tick=time.perf_counter()
 with (work/'native.log').open('w') as log:
  proc=subprocess.Popen(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,pass_fds=(rr,sw),preexec_fn=no_core);os.close(rr);os.close(sw)
  sel=selectors.DefaultSelector();sel.register(sr,selectors.EVENT_READ);assert sel.select(timeout=120),'native response timeout';data=os.read(sr,4096).decode();sel.close();os.close(rw);os.close(sr);code=proc.wait(timeout=30)
 native=(work/'native.log').read_text();assert code!=0 and not (work/'output.route').exists() and 'VPR succeeded' not in native
 if variant=='valid':
  nets=len({q['net_id'] for q in ep['connections']});assert data==f"READY\t{nets}\t{len(ep['connections'])}\n" and 'controller disconnected' in native
 else:
  assert not data and any(x in native for x in ['unsupported manifest graph dimensions','manifest edge count mismatch','incomplete manifest scope','query NET coverage mismatch','query pin coverage mismatch'])
 bindings.update({str(p):sha(p) for p in [manifest,work/'native.log',arch,*(work/n for n in ['design.blif','design.net','design.place'])]});row=dict(case=case,variant=variant,ready=data.strip(),exit_code=code,elapsed_seconds=time.perf_counter()-tick,no_route_created=True);results.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,results=results,complete_valid_native_pin_and_global_getter_preflights_pass=True,malformed_scope_rejected_before_ready=True,scope='All valid manifest queries pinbound before READY, all native globaledges getter/capacity/rowchecked. EOF intentionally aborts before price/search/seed/native routing; no floor/path/feedback/performance proof.'),indent=2)+'\n')

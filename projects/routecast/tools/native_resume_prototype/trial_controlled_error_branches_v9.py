"""Actual native terminal-pin mismatch and strict incomplete-NET rejection."""
import json,os,re,shutil,subprocess,sys,time,resource
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
resource.setrlimit(resource.RLIMIT_CORE,(0,0));E=R/'experiments';D=E/'native_controlled_error_branches_v9_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();bindings=closure([Path(__file__)]);rows=[]
for authority in (E/'adder_native_controlled_seed_recovery_v1_2026-10-09/verification.json',E/'native_controlled_error_modes_v9_2026-10-09/verification.json'):
 doc=json.loads(authority.read_text());assert all(sha(p)==h for p,h in doc['bindings'].items());bindings.update(doc['bindings']);bindings[str(authority)]=sha(authority)
plans=json.loads((E/'adder_cross_place_hybrid_native_v1_2026-10-09/protocol.json').read_text())['plans'];binary=R/'build/native_resume_controlled_error_v9_2026-10-09/routecast_resume_vpr';cases=[]
for plan in plans:
 step=plan['step'];seed=Path(plan['seed']);lines=seed.read_text().splitlines(keepends=True);first=next(i for i,line in enumerate(lines) if line.startswith('Net '));end=next(i for i in range(first+1,len(lines)) if lines[i].startswith('Net '));indices=[i for i in range(first,end) if ' SINK ' in lines[i] and 'Net_pin_index:' in lines[i]];assert len(indices)>=2
 a,b=indices[:2];pa=int(re.search(r'Net_pin_index:\s*(\d+)',lines[a])[1]);pb=int(re.search(r'Net_pin_index:\s*(\d+)',lines[b])[1]);assert pa!=pb
 for idx,pin in ((a,pb),(b,pa)):lines[idx]=re.sub(r'(Net_pin_index:\s*)\d+',lambda m:m[1]+str(pin),lines[idx])
 mutated=''.join(lines);assert sum(x!=y for x,y in zip(seed.read_text().splitlines(),mutated.splitlines()))==2
 corrupt=D/f'step_{step}_swapped.route';corrupt.write_text(mutated);bindings[str(corrupt)]=sha(corrupt);cmd=list(plan['command']);cmd[0]=str(binary);meta=json.loads(Path(plan['endpoints']).read_text());graph=Path(meta['inputs']['graph']['path']);cases.append(dict(name=f'terminal_{step}',seed=str(corrupt),command=cmd,graph=str(graph),place=meta['inputs']['place']['path'],branch_partial=True,expected='Resume sink terminal mismatch (NET '))
prior=E/'native_controlled_error_modes_v9_2026-10-09/v9_partial';doc=json.loads((prior/'command.json').read_text());cmd=doc['command'];graph=Path(cmd[cmd.index('--read_rr_graph')+1]);cases.append(dict(name='strict_incomplete',seed=doc['seed'],command=cmd,graph=str(graph),place=str(prior/'design.place'),branch_partial=False,expected='Resume incomplete NET (NET '))
for case in cases:
 assert all(sha(p)==h for p,h in bindings.items());w=D/case['name'];w.mkdir();graph=Path(case['graph'])
 for name in ('design.blif','design.net'):shutil.copyfile(graph.with_name(name),w/name)
 shutil.copyfile(case['place'],w/'design.place');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=case['seed'],ROUTECAST_RESUME_ALLOW_PARTIAL='1')
 if case['branch_partial']:env['ROUTECAST_RESUME_ALLOW_BRANCH_PARTIAL']='1'
 (w/'protocol.json').write_text(json.dumps(case,indent=2)+'\n')
 with (w/'run.log').open('x') as log:code=subprocess.run(case['command'],cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 text=(w/'run.log').read_text();assert code==1 and case['expected'] in text and 'terminate called' not in text and 'ROUTECAST_RESUME_LOADED_TREES' not in text,(case['name'],code,text[-1500:])
 for p in w.iterdir():
  if p.is_file():bindings[str(p)]=sha(p)
 row=dict(name=case['name'],exit_code=code,expected_diagnostic=case['expected'],controlled_error=True);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Actual three swapped legal sink-pin identities and strict rejection of known branch-partial seed. SOURCE mismatch branch not covered; no native internal recovery, online search, independent timing success or speedup.'),indent=2)+'\n')

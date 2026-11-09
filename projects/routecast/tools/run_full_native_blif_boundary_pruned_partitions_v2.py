"""Complete disjoint target partitioning of actual native/ABC boundary miter."""
import concurrent.futures,hashlib,json,re,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_blif_all_boundaries_v1_2026-10-09';D=E/'full_native_blif_boundary_pruned_partitions_v2_2026-10-09';D.mkdir(exist_ok=True)
a=json.loads((P/'preflight.json').read_text());text=(P/'miter.v').read_text();pairs=a['pairs'];groups=[pairs[i:i+64] for i in range(0,len(pairs),64)];yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
assert len({x[0] for g in groups for x in g})==len(pairs)==2385
definitions=dict(re.findall(r'wire (\w+); assign \1 = ([^;]+);',text))
assert definitions
report={'preflight_sha256':hashlib.sha256((P/'preflight.json').read_bytes()).hexdigest(),'miter_sha256':hashlib.sha256((P/'miter.v').read_bytes()).hexdigest(),'yosys_sha256':hashlib.sha256(yosys.read_bytes()).hexdigest(),'partition_width':64,'timeout_seconds':20,'workers':4,'total_targets':len(pairs),'planned_groups':len(groups),'results':[],'scope':'All disjoint native/ABC target nets preserved, same arbitrary state/macro boundaries and exact definitions. Terminal timeouts are unresolved; no Full/init/four-state claim.'}
(D/'partition_plan.json').write_text(json.dumps({'groups':[[x[0] for x in g] for g in groups],**{k:v for k,v in report.items() if k!='results'}},indent=2)+'\n')
def run(item):
 i,g=item;v=D/f'p{i:02d}.v';log=D/f'p{i:02d}.log';expression=' | '.join(f'({n} ^ {b})' for _,n,b in g);roots=[signal for _,n,b in g for signal in [n,b]];needed=set();inputs=set();todo=list(roots)
 while todo:
  signal=todo.pop()
  if signal.startswith('in'):inputs.add(signal);continue
  if signal in needed:continue
  assert signal in definitions, signal
  needed.add(signal);todo.extend(re.findall(r'\b(?:n\d+|a\d+|in\d+)\b',definitions[signal]))
 part='module check_selectors('+','.join('input '+signal for signal in sorted(inputs))+',output bad);\n'+'\n'.join('wire '+signal+'; assign '+signal+' = '+definitions[signal]+';' for signal in sorted(needed))+'\nassign bad = '+expression+';\nendmodule\n'
 v.write_text(part)
 cmd=[str(yosys),'-p',f'read_verilog {v}; hierarchy -top check_selectors; proc; opt; check -assert; sat -prove bad 0'];start=time.monotonic()
 try:
  with log.open('w') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=20)
  s=log.read_text();status='passed' if proc.returncode==0 and 'SAT proof finished - no model found: SUCCESS!' in s else 'counterexample' if proc.returncode==0 and 'SAT proof finished - model found: FAIL!' in s else 'error';code=proc.returncode
 except subprocess.TimeoutExpired:status='terminal_timeout';code=None
 return {'partition':i,'targets':[x[0] for x in g],'status':status,'exit_code':code,'seconds':time.monotonic()-start,'retained_definitions':len(needed),'arbitrary_boundary_inputs':len(inputs),'miter_sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'log':str(log.relative_to(R))}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for result in pool.map(run,enumerate(groups)):
  report['results'].append(result);(D/'partition_results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'partition':result['partition'],'status':result['status'],'targets':len(result['targets'])}),flush=True)
covered=[x for r in report['results'] for x in r['targets']];assert sorted(covered)==sorted(x[0] for x in pairs) and len(covered)==len(set(covered));report['complete_coverage']=True;report['status_target_counts']={status:sum(len(r['targets']) for r in report['results'] if r['status']==status) for status in ['passed','terminal_timeout','counterexample','error']};(D/'partition_results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['status_target_counts']),flush=True)

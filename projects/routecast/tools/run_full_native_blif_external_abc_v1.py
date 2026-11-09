"""Independent ABC iprove on all terminal SAT subpartitions, exact miters."""
import concurrent.futures,hashlib,json,re,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_blif_boundary_subpartitions_v3_2026-10-09';D=E/'full_native_blif_external_abc_v1_2026-10-09';D.mkdir(exist_ok=True);parent=P/'partition_results.json';j=json.loads(parent.read_text());jobs=[r for r in j['results'] if r['status']=='terminal_timeout'];base=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend';yosys=base/'bin/yosys';abc=base/'abc/abc'
report={'parent_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'yosys_sha256':hashlib.sha256(yosys.read_bytes()).hexdigest(),'abc_sha256':hashlib.sha256(abc.read_bytes()).hexdigest(),'results':[],'scope':'Exact previously unresolved miters translated by techmap/aigmap to combinational AIG, independently solved by ABC iprove. Only explicit UNSATISFIABLE is proof. No Full/init/four-state claim.'}
def run(r,negative=False):
 idx=r['partition'];stem=f'p{idx:02d}'+('_negative' if negative else '');v=P/f'p{idx:02d}.v';text=v.read_text();assert hashlib.sha256(v.read_bytes()).hexdigest()==r['miter_sha256']
 if negative:
  expr=re.search(r'assign bad = ([^\n]+);',text)[1];v=D/(stem+'.v');v.write_text(text.replace('assign bad = '+expr+';','assign bad = ~('+expr+');',1))
 aig=D/(stem+'.aig');prepare=D/(stem+'_prepare.log');log=D/(stem+'.log');start=time.monotonic();status='error';code=None
 try:
  with prepare.open('w') as f:p=subprocess.run([str(yosys),'-p',f'read_verilog {v}; hierarchy -top check_selectors; proc; opt; techmap; opt; aigmap; write_aiger {aig}'],stdout=f,stderr=subprocess.STDOUT,timeout=20)
  assert p.returncode==0
  with log.open('w') as f:p=subprocess.run([str(abc),'-c',f'read_aiger {aig}; strash; iprove'],stdout=f,stderr=subprocess.STDOUT,timeout=20)
  s=log.read_text();code=p.returncode;status='passed' if code==0 and re.search(r'^UNSATISFIABLE\b',s,re.M) else 'counterexample' if code==0 and re.search(r'^SATISFIABLE\b',s,re.M) else 'undecided'
 except subprocess.TimeoutExpired:status='terminal_timeout'
 return {'partition':idx,'targets':r['targets'],'negative':negative,'status':status,'exit_code':code,'seconds':time.monotonic()-start,'miter_sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'aig_sha256':hashlib.sha256(aig.read_bytes()).hexdigest() if aig.exists() else None,'log':str(log.relative_to(R))}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for r in pool.map(run,jobs):
  report['results'].append(r);(D/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'partition':r['partition'],'status':r['status']}),flush=True)
report['negative_control']=run(jobs[0],True);assert report['negative_control']['status']=='counterexample'
covered=[b for r in report['results'] for b in r['targets']];assert len(covered)==len(set(covered))==224
report['status_target_counts']={s:sum(len(r['targets']) for r in report['results'] if r['status']==s) for s in ['passed','counterexample','undecided','terminal_timeout','error']};(D/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'counts':report['status_target_counts'],'negative_control':report['negative_control']['status']}),flush=True)

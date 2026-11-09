"""Frozen single-source frontend preparation, not predictive validation."""
import datetime,hashlib,json,os,resource,subprocess,time
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1];S=R/'experiments/wbuart_source_candidate_v2_2026-10-20';O=R/'experiments/wbuart_frontend_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False)
 tree=json.loads((S/'tree.json').read_text());commit=json.loads((S/'commit.json').read_text());entries={e['path']:e for e in tree['tree']};trees={'':tree['sha'],**{n:e['sha'] for n,e in entries.items() if e['type']=='tree'}}
 for prefix,expected in trees.items():
  children=[]
  for n,e in entries.items():
   parent=str(PurePosixPath(n).parent);parent='' if parent=='.' else parent
   if parent==prefix:children.append((PurePosixPath(n).name,e))
  content=b''.join(e['mode'].lstrip('0').encode()+b' '+n.encode()+b'\0'+bytes.fromhex(e['sha']) for n,e in sorted(children,key=lambda item:(item[0]+('/' if item[1]['type']=='tree' else '')).encode()))
  assert hashlib.sha1(b'tree '+str(len(content)).encode()+b'\0'+content).hexdigest()==expected
 assert tree['sha']==commit['commit']['tree']['sha']
 proof=json.loads((S/'hierarchy_fileset_verification_v1.json').read_text());assert proof['exit_status']==0
 files=[S/'upstream/rtl'/n for n in proof['files']]
 for p in files:
  b=p.read_bytes();e=entries[str(p.relative_to(S/'upstream'))];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==e['sha']
 y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';lib=R/'experiments/prospective_external_family_runtime_v1_2026-10-18/tcl-root/usr/lib/x86_64-linux-gnu'
 script='read_verilog '+' '.join(str(p) for p in files)+'\nhierarchy -check -top wbuart\nsynth -top wbuart -flatten -lut 6\ncheck -assert\nstat\nwrite_json '+str(O/'mapped.json')+'\n'
 (O/'frontend.ys').write_text(script)
 protocol={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':commit['sha'],'git_tree_objects_recomputed':len(trees),'top':'wbuart','parameters':'Upstream defaults, unchanged RTL','command':[str(y),'-Q','-T','-s',str(O/'frontend.ys')],'timeout_seconds':180,'address_space_limit_bytes':8*2**30,'selection':'One frozen default six-LUT frontend run; no width/seed/parameter search and no route labels.','bindings':{str(p):sha(p) for p in [*files,y,Path(__file__),O/'frontend.ys',lib/'libtcl8.6.so',S/'upstream/wbuart32.core']},'scope':'Development input preparation only. Strict unseen, source-to-mapped functional equivalence, HDL4-state and physical implementation are not established by frontend success.'}
 save('protocol.json',protocol);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(lib)+':'+env.get('LD_LIBRARY_PATH','')
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 start=time.perf_counter();timeout=False
 with (O/'frontend.log').open('x') as f:
  p=subprocess.Popen(protocol['command'],cwd=O,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit,start_new_session=True)
  try:rc=p.wait(timeout=180)
  except subprocess.TimeoutExpired:
   import signal
   timeout=True;os.killpg(p.pid,signal.SIGTERM);rc=p.wait()
 for n,h in protocol['bindings'].items():assert sha(Path(n))==h
 cells={};ports={}
 if rc==0:
  mapped=json.loads((O/'mapped.json').read_text());m=mapped['modules']['wbuart'];ports=m['ports']
  for cell in m['cells'].values():cells[cell['type']]=cells.get(cell['type'],0)+1
 save('verification.json',{'status':'FRONTEND_PREPARATION_PASS_PENDING_FUNCTIONAL_AUDIT' if rc==0 else 'FRONTEND_PREPARATION_FAILED_RETAINED','exit_status':rc,'timeout':timeout,'seconds':time.perf_counter()-start,'cell_types':cells,'port_bits':{n:len(p['bits']) for n,p in ports.items()},'bindings':{n:sha(O/n) for n in ['protocol.json','frontend.log']+(['mapped.json'] if rc==0 else [])},'strict_unseen_certified':False,'new_route_labels':False,'functional_equivalence_proven':False})
 print('FRONTEND_TERMINAL',rc,cells,flush=True)
if __name__=='__main__':main()

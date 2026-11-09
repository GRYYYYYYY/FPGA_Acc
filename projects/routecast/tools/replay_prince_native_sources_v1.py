"""Two fixed exact-source cold repeat controls; no width/seed/budget changes."""
import json,subprocess,shutil,os,resource,re,time
from pathlib import Path
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_native_source_replay_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def sequences(p):
 d={};name=None
 for line in p.read_text().splitlines():
  m=NET.match(line)
  if m:name=m[2];assert name not in d;d[name]=[]
  m=NODE.match(line)
  if m:assert name is not None;d[name].append((int(m[1]),m[2],int(m[3])))
 return d
def main():
 D.mkdir(exist_ok=False);pp=E/'prince_native_cohort_v1_2026-10-20/protocol.json';p=json.loads(pp.read_text());jobs=[];bindings={str(pp):sha(pp),str(Path(__file__)):sha(__file__)}
 for j in p['jobs']:
  if j['frame']!='source' or j['width']==96:continue
  src=Path(j['directory']);out=D/f"w{j['width']}";out.mkdir();cmd=j['command'].copy();cmd[cmd.index('--write_rr_graph')+1]=str(out/'rr_graph.xml')
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(src/name,out/name);assert sha(out/name)==sha(src/name);bindings[str(src/name)]=sha(src/name)
  for f in [src/'output.route',src/'native.log',src/'rr_graph.xml',Path(cmd[0]),Path(cmd[1])]:bindings[str(f)]=sha(f)
  jobs.append(dict(width=j['width'],source=str(src),output=str(out),command=cmd))
 (D/'protocol.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,policy='Exactly one independent cold repeat of each already legal source width128/160. Same initial packed netlist, placement, binary, architecture, width, seed1, worker1, max100 and default termination; output directory and graph output path only differ. No retry, tuning, target replacement or timing gain claim.'),indent=2)+'\n');rows=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 for j in jobs:
  src=Path(j['source']);out=Path(j['output']);tick=time.perf_counter()
  with (out/'native.log').open('x') as log:code=subprocess.call(j['command'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  text=(out/'native.log').read_text();old=(src/'native.log').read_text();passed=code==0 and 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text
  rows.append(dict(width=j['width'],exit_code=code,native_full_pass=passed,all_NET_node_type_switch_sequences_identical=passed and sequences(out/'output.route')==sequences(src/'output.route'),graph_bytes_identical=sha(out/'rr_graph.xml')==sha(src/'rr_graph.xml'),diagnostic_CPD_text_identical=re.findall(r'Final critical path delay[^\n]*',text)==re.findall(r'Final critical path delay[^\n]*',old),process_seconds=time.perf_counter()-tick,files={str(f):sha(f) for f in out.iterdir() if f.is_file()}));print('SOURCE_REPEAT',rows[-1]['width'],rows[-1]['all_NET_node_type_switch_sequences_identical'],flush=True)
 assert all(sha(f)==h for f,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Two exact-source repeat observations only. Equality supports reproducibility in these runs, not universal native determinism. No target placement repeat, unseen evidence, physical timing or full-paid gain.'),indent=2)+'\n')
if __name__=='__main__':main()

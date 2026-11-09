"""Only source placement/route inputs; no target labels or target-native history."""
import json,hashlib,os,sys,shutil,subprocess,time,struct,math,resource,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'source_final_history_parity_v1_2026-10-20';B=R/'build/native_source_final_history_observer_v1_2026-10-20';S=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 receipt=json.loads((B/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items());assert sha(B/'sequence_vpr')==receipt['binary_sha256'];manifest=S/'source_manifest.json';m=json.loads(manifest.read_text());case=m['cases'][0];assert case['case']=='w160/source';original=Path(case['output']);D.mkdir(exist_ok=False);work=D/'work';work.mkdir();bindings={str(manifest):sha(manifest),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__)):sha(__file__),str(original/'verification.json'):sha(original/'verification.json')}
 for key,name in [('blif','design.blif'),('net','design.net'),('place','design.place')]:p=Path(case['inputs'][key]);shutil.copyfile(p,work/name);bindings[str(p)]=sha(p)
 cmd=list(case['command']);cmd[0]=str(B/'sequence_vpr');graph=Path(cmd[cmd.index('--read_rr_graph')+1]);bindings[str(graph)]=sha(graph);env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_EXPORT_SOURCE_FINAL_HISTORY']='1';(D/'protocol.json').write_text(json.dumps(dict(command=cmd,bindings=bindings,environment_set={'ROUTECAST_EXPORT_SOURCE_FINAL_HISTORY':'1'},source_only=True,scope='Full source cold native run, exact initial/first/final output parity. No target cases or labels. Export is final negotiated history after best-tree restore, not state of best iteration.'),indent=2)+'\n');start=time.perf_counter()
 with (work/'native.log').open('x') as log:code=subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits).returncode
 (D/'terminal.json').write_text(json.dumps(dict(exit_status=code,native_seconds=time.perf_counter()-start),indent=2)+'\n');assert code==0
 parity={}
 for name in ['initial_connections.tsv','first_iteration.route','output.route']:
  parity[name]=sha(work/name)==sha(original/name);assert parity[name],name;bindings[str(original/name)]=sha(original/name);bindings[str(work/name)]=sha(work/name)
 caps={}
 for _,e in ET.iterparse(graph):
  if e.tag=='node' and e.get('capacity') is not None:caps[int(e.get('id'))]=int(e.get('capacity'))
  e.clear()
 rows=[];hist=Counter();nonunit=fractional=0;history=work/'source_final_rr_history.tsv'
 with history.open() as f:
  header=f.readline().strip().split('\t');assert header[:2]==['F','SOURCE_ROUTER_END_AFTER_BEST_RESTORE']
  for line in f:
   tag,node,cap,occ,bits,hexvalue=line.strip().split('\t');node=int(node);cap=int(cap);occ=int(occ);value=struct.unpack('!f',bytes.fromhex(bits))[0];assert tag=='N' and node==len(rows) and cap==caps[node] and occ>=0 and math.isfinite(value) and value>=1 and value==float.fromhex(hexvalue);rows.append(node);hist[value]+=1;nonunit+=value!=1;fractional+=not value.is_integer()
 assert set(rows)==set(caps);assert all(sha(p)==h for p,h in bindings.items());bindings[str(history)]=sha(history);result=dict(status='SOURCE_FINAL_HISTORY_EXACT_ROUTE_PARITY_AND_ALL_NODE_F32_EXPORT_PASS',nodes=len(rows),iterations=int(header[2]),nonunit_history_nodes=nonunit,fractional_history_nodes=fractional,maximum_history=max(hist),history_value_histogram=[dict(value=k,nodes=v) for k,v in sorted(hist.items())],exact_output_parity=parity,bindings=bindings,scope='Source-only final negotiated history available before all target forecasts. No predictor conversion, target quality or native QoR improvement claim; float bits preserved without rounding into model costs.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['history_value_histogram','bindings']},indent=2))
if __name__=='__main__':main()

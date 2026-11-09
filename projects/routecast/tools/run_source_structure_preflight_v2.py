"""Raw source hierarchy/process preflight; no mapping, placement or route labels."""
import json,os,resource,subprocess,sys,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def quoted(p):return '"'+str(p).replace('\\','\\\\').replace('"','\\"')+'"'
def limits():
 resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def integer(v):return int(v,2) if isinstance(v,str) else int(v)
def main():
 manifest_path,output=sys.argv[1:];manifest=load(Path(manifest_path));output=Path(output);output.mkdir();binary=Path(manifest['yosys_binary']);assert sha(binary)==manifest['yosys_sha256'];results=[]
 env=os.environ.copy()
 lib=Path(manifest['runtime_library'])
 assert sha(lib)==manifest['runtime_library_sha256']
 env['LD_LIBRARY_PATH']=str(lib.parent)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 for case in manifest['cases']:
  source=Path(case['source']);assert sha(source)==case['source_sha256'];folder=output/case['name'];folder.mkdir();snapshot=folder/source.name;snapshot.write_bytes(source.read_bytes());assert sha(snapshot)==case['source_sha256'];commands=folder/'commands.ys';payload=folder/'proc.json';commands.write_text('\n'.join([f'read_verilog -sv -I{source.parent} {quoted(snapshot)}','hierarchy -check -auto-top','proc','check -assert',f'write_json {quoted(payload)}'])+'\n');start=time.perf_counter()
  with (folder/'yosys.log').open('x') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(commands)],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  row=dict(name=case['name'],family=case['family'],source=str(source),source_sha256=case['source_sha256'],exit_code=code,seconds=time.perf_counter()-start,native_architecture_admitted=False,strict_unseen_admitted=False)
  if code==0:
   design=load(payload);counts=Counter(c['type'] for m in design['modules'].values() for c in m.get('cells',{}).values());tops=[name for name,m in design['modules'].items() if integer(m.get('attributes',{}).get('top',0))];seq={k:v for k,v in counts.items() if k in ['$dff','$adff','$dffe','$adffe','$sdff','$sdffe','$dffsr','$dffsre','$aldff','$aldffe','$dlatch','$adlatch','$dlatchsr']};row.update(status='RAW_HIERARCHY_PROC_CHECK_PASS_MAPPING_PENDING',modules=len(design['modules']),top_modules=tops,cell_type_counts=dict(counts),sequential_cell_counts=seq,raw_payload_sha256=sha(payload))
  else:row['status']='RAW_FRONTEND_FAILED_RETAINED_NO_REPLACEMENT'
  (folder/'terminal.json').write_text(json.dumps(row,indent=2)+'\n');results.append(row);(output/'progress.json').write_text(json.dumps(results,indent=2)+'\n');print('SOURCE_STRUCTURE_PREFLIGHT',case['name'],code,row['seconds'],flush=True)
 (output/'results.json').write_text(json.dumps(dict(results=results,scope='Pre-route source parser/hierarchy/proc structural observations only. No synthesized packedsize,sourceequivalence,targetclock/architecture/strictunseen or nativeperformance admission.',bindings={str(Path(manifest_path)):sha(manifest_path),str(Path(__file__)):sha(__file__)}),indent=2)+'\n')
if __name__=='__main__':main()

"""Identical frozen boundary replay with baseline and logging-only plugins."""
import json,hashlib,os,subprocess,resource,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'parmys_source_provenance_replay_v1_2026-10-21';P=E/'preserved_source_ram_mapping_v1_2026-10-21';B=E/'private_parmys_provenance_build_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);original=binary.parents[1]/'share/yosys/plugins/parmys.so';private=B/'parmys_provenance.so';arch=E/'async_reset_arch_candidate_v2_2026-10-08/architecture.xml';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');protocol={'scope':'Same frozen preserved source boundaries, same operations, baseline versus logging-only private plugin. No new optimization/repair, native labels or source changes. Compare actual output graphs before using instrumentation as evidence.','bindings':{str(p):sha(p) for p in [Path(__file__),binary,runtime,original,private,arch,*[P/n/'preserved_boundary.json' for n in ['mcml','mkDelayWorker32B']]]}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for n in ['mcml','mkDelayWorker32B']:
  for label,plugin in [('original',original),('instrumented',private)]:
   f=D/n/label;f.mkdir(parents=True);ys=f/'commands.ys';ys.write_text(f'plugin -i "{plugin}"\nparmys_arch -a {arch}\ndesign -reset\nread_json "{P/n/"preserved_boundary.json"}"\nparmys -a {arch} -nopass\nopt\ncheck -assert\nwrite_json "{f/"mapped.json"}"\n')
   def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
   tick=time.monotonic()
   with (f/'yosys.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT,preexec_fn=limits)
   rows.append({'source':n,'arm':label,'exit_code':code,'seconds':time.monotonic()-tick});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(n,label,code,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()

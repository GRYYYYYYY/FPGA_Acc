"""Actual source entry with preserved RAM primitives, no reset technology mapping."""
import json,hashlib,subprocess,os,resource,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'preserved_source_ram_mapping_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);manifest=E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json';m=json.loads(manifest.read_text());binary=Path(m['yosys_binary']);library=Path(m['primitive_library']);runtime=Path(m['runtime_library']);plugin=binary.parents[1]/'share/yosys/plugins/parmys.so';arch=E/'async_reset_arch_candidate_v2_2026-10-08/architecture.xml';cases=[c for c in m['cases'] if c['name'] in ['mcml','mkDelayWorker32B']];assert len(cases)==2
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');protocol={'scope':'Both previously selected source designs containing external VTR RAM primitives. Original source/library/plugin/architecture. Explicit keep_hierarchy on RAM, pre-mapper checkpoint. No reset conversion, source edits, pack/place/route or semantic equivalence claim. AS8GiB/core0, no elapsed timeout.','cases':cases,'bindings':{str(p):sha(p) for p in [Path(__file__),manifest,binary,library,runtime,plugin,arch,*[Path(c['source']) for c in cases]]}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for c in cases:
  f=D/c['name'];f.mkdir();source=Path(c['source']);assert sha(source)==c['source_sha256'];ys=f/'commands.ys';ys.write_text(f'plugin -i "{plugin}"\nread_verilog -nomem2reg "{library}"\nsetattr -mod -set keep_hierarchy 1 single_port_ram dual_port_ram\nparmys_arch -a {arch}\nread_verilog "{source}"\nhierarchy -check -top {c["name"]}\nproc\nopt\nmemory -nomap\nflatten\nopt\ncheck -assert\nwrite_json "{f/"preserved_boundary.json"}"\nparmys -a {arch} -nopass\nopt\ncheck -assert\nwrite_json "{f/"mapped.json"}"\n')
  def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  tick=time.monotonic()
  with (f/'yosys.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT,preexec_fn=limits)
  row={'case':c['name'],'exit_code':code,'seconds':time.monotonic()-tick,'functional_equivalence_proven':False,'native_admitted':False}
  for file,key in [('preserved_boundary.json','boundary_types'),('mapped.json','mapped_types')]:
   if (f/file).exists():
    design=json.loads((f/file).read_text());row[key]=dict(Counter(cell['type'] for cell in design['modules'][c['name']].get('cells',{}).values()))
  rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(c['name'],code,row['seconds'],flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()

"""Isolated Tcl runtime extraction and read-only source hierarchy admission."""
import hashlib,json,os,re,subprocess,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=R/'experiments/prospective_external_family_source_v2_2026-10-18';vp=source/'source_verification.json';v=json.loads(vp.read_text());assert v['hierarchy_exit_status']==127
 for asset in v['assets']:assert sha(asset['path'])==asset['sha256']
 out=R/'experiments/prospective_external_family_runtime_v1_2026-10-18';out.mkdir(exist_ok=False);version='8.6.12+dfsg-1build1';meta=subprocess.check_output(['apt-cache','show','libtcl8.6='+version],text=True);fields=dict(line.split(': ',1) for line in meta.splitlines() if ': ' in line and not line.startswith(' '));assert fields['Version']==version and fields['Architecture']=='amd64';filename=fields['Filename'];assert filename.startswith('pool/') and '..' not in Path(filename).parts
 with (out/'package_metadata.txt').open('x') as f:f.write(meta)
 url='https://archive.ubuntu.com/ubuntu/'+filename
 with urllib.request.urlopen(url,timeout=40) as f:data=f.read()
 assert hashlib.sha256(data).hexdigest()==fields['SHA256'];deb=out/Path(filename).name
 with deb.open('xb') as f:f.write(data)
 prefix=out/'tcl-root';subprocess.run(['dpkg-deb','-x',str(deb),str(prefix)],check=True);lib=prefix/'usr/lib/x86_64-linux-gnu';library=lib/'libtcl8.6.so';assert library.is_file();tool=Path(v['yosys_path']);assert sha(tool)==v['yosys_sha256'];env=os.environ.copy();env['LD_LIBRARY_PATH']=str(lib)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 tcl=prefix/'usr/share/tcltk/tcl8.6'
 if tcl.is_dir():env['TCL_LIBRARY']=str(tcl)
 script=(source/'closure_check.ys').read_text()
 with (out/'closure_check.ys').open('x') as f:f.write(script)
 with (out/'closure_check.log').open('x') as f:code=subprocess.call([str(tool),'-Q','-T','-s',str(out/'closure_check.ys')],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
 result=dict(status='source_closure_hierarchy_pass_strict_family_pending' if code==0 else 'source_closure_hierarchy_failed',source_verification=str(vp),pinned_commit=v['pinned_commit'],source_units=v['RTL_compilation_units'],hierarchy_exit_status=code,local_runtime_package=dict(name='libtcl8.6',version=version,url=url,sha256=sha(deb)),runtime_shared_library_sha256=sha(library),system_packages_modified=False,shared_project_files_modified=False,strict_unseen_families_certified=0,new_native_labels_read=False,new_technology_synthesis_placement_route_jobs=False,bindings={str(p):sha(p) for p in [Path(__file__),vp,deb,out/'package_metadata.txt',out/'closure_check.ys',out/'closure_check.log',library]},scope='Exact original RTL and package checksums; library path applies only to this subprocess. Read-only frontend hierarchy check, not technology synthesis, benchmark outcome or strict unseen admission.')
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print('ISOLATED FRONTEND HIERARCHY EXIT',code,flush=True)
 if code:raise SystemExit(code)
if __name__=='__main__':main()

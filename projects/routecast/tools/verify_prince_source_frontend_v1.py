"""Independent recursive Git-tree reconstruction and original-RTL hierarchy check."""
import json,hashlib,os,subprocess,time
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_candidate_source_v2_2026-10-20';D=E/'prince_source_frontend_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);v=read(S/'verification.json');tree=read(S/'official_tree.json');commit=read(S/'official_commit.json');assert v['revision']==commit['sha']==read(E/'prince_candidate_source_v1_2026-10-20/official_commit.json')['sha'];entries={r['path']:r for r in tree['tree']};directories=['']+[name for name,r in entries.items() if r['type']=='tree'];checked=0
 for directory in directories:
  rows=[r for name,r in entries.items() if str(PurePosixPath(name).parent)==(directory or '.')];payload=b''
  for row in sorted(rows,key=lambda r:(PurePosixPath(r['path']).name+('/' if r['type']=='tree' else '')).encode()):
   name=PurePosixPath(row['path']).name;payload+=row['mode'].lstrip('0').encode()+b' '+name.encode()+b'\x00'+bytes.fromhex(row['sha'])
  got=hashlib.sha1(b'tree '+str(len(payload)).encode()+b'\x00'+payload).hexdigest();expected=entries[directory]['sha'] if directory else commit['commit']['tree']['sha'];assert got==expected;checked+=1
 for a in v['assets']:
  b=Path(a['path']).read_bytes();assert sha(a['path'])==a['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()==entries[a['relative']]['sha']
 assert set(v['RTL_compilation_units'])=={'src/rtl/prince.v','src/rtl/prince_core.v'} and v['explicit_includes']==['"prince_round_functions.vh"'];assert 'BSD 2-Clause License' in (S/'upstream/LICENSE').read_text();core=(S/'upstream/prince.core').read_text();assert 'license: BSD-2-Clause' in core and all(name in core for name in v['RTL_compilation_units']) and 'src/rtl/prince_round_functions.vh' in core and 'toplevel : prince' in core
 old=read(E/'prospective_external_family_source_v2_2026-10-18/source_verification.json');tool=Path(old['yosys_path']);runtime=E/'prospective_external_family_runtime_v1_2026-10-18/tcl-root/usr/lib/x86_64-linux-gnu';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 script='read_verilog -I'+str(S/'upstream/src/rtl')+' '+' '.join(str(S/'upstream'/name) for name in v['RTL_compilation_units'])+'\nhierarchy -check -top prince\nstat\n';(D/'hierarchy.ys').write_text(script);tick=time.perf_counter()
 with (D/'hierarchy.log').open('x') as log:code=subprocess.call([str(tool),'-Q','-T','-s',str(D/'hierarchy.ys')],env=env,stdout=log,stderr=subprocess.STDOUT)
 files=[Path(__file__),S/'verification.json',S/'official_tree.json',S/'official_commit.json',D/'hierarchy.ys',D/'hierarchy.log',tool,*[Path(a['path']) for a in v['assets']]];result={'status':'PASS_PINNED_GIT_TREE_BLOBS_AND_ORIGINAL_RTL_HIERARCHY' if code==0 else 'FRONTEND_CLOSURE_FAILED_SOURCE_INTEGRITY_PASSED','revision':v['revision'],'git_trees_rebuilt':checked,'assets_reauthenticated':len(v['assets']),'hierarchy_exit':code,'component_seconds':time.perf_counter()-tick,'compilation_units':v['RTL_compilation_units'],'include':'src/rtl/prince_round_functions.vh','top':'prince','strict_unseen_admitted':False,'new_native_labels':False,'bindings':{str(p):sha(p) for p in files},'scope':'Original RTL frontend hierarchy only; not synthesis or functional-equivalence proof, no place/route labels. Historical source-hash/lineage audit remains open.'};(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PRINCE_SOURCE_FRONTEND',code,checked,len(v['assets']))
if __name__=='__main__':main()

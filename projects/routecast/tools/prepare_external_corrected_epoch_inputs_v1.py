"""Fresh source checkpoint and matched warm initializers in corrected native epoch."""
import json,sys,hashlib,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_corrected_native_epoch_v1_2026-10-19';OLD=E/'prospective_external_family_supplementary_development_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label,argv):
 with (D/(label+'.log')).open('x') as log:subprocess.run([sys.executable,*map(str,argv)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
def main():
 native=D/'native/w160/source';vp=native/'verification.json';v=read(vp);assert v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and v['canonical']['semantic_consistency_gate_pass'];assert all(sha(k)==h for k,h in v['bindings'].items());old=read(OLD/'source_checkpoints/w160/receipt.json');checkpoint=D/'source_checkpoint';cases=[];bindings={str(vp):sha(vp),str(D/'epoch_audit.json'):sha(D/'epoch_audit.json'),str(Path(__file__).resolve()):sha(__file__)}
 for name in ['prepare_external_native_source_checkpoint_v1.py','verify_external_native_source_checkpoint_xml_v1.py','prepare_external_warm_initializers_v1.py','verify_external_warm_initializers_xml_v1.py']:p=R/'tools'/name;bindings[str(p)]=sha(p)
 bundle=read(E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json');lookup={r['case']:r for r in bundle['rows']}
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';r=lookup[case];cases.append(dict(case=case,endpoint=r['endpoint'],floor_proof=r['floor_proof'],warm=str(D/'warm'/case)))
 (D/'preparation_protocol.json').write_text(json.dumps(dict(source_route=str(native/'output.route'),source_endpoint=old['source_endpoint'],source_floor=old['floor_proof'],source_checkpoint=str(checkpoint),cases=cases,bindings=bindings,scope='Fresh source-derived budgets and both raw/native warm branches; exact graph-only floors and presearch timing reuse per epoch audit. Existing corrected-native cold labels not used by initializer. Development only, all3 plus original unavailable6 retained. No feedback scoring or utility acceptance.'),indent=2)+'\n')
 run('source_checkpoint',[R/'tools/prepare_external_native_source_checkpoint_v1.py',old['source_endpoint'],native/'output.route',old['floor_proof'],checkpoint]);run('source_checkpoint_xml',[R/'tools/verify_external_native_source_checkpoint_xml_v1.py',checkpoint])
 def warm(c):
  label=c['case'].replace('/','_');out=Path(c['warm']);out.parent.mkdir(parents=True,exist_ok=True);run(label+'_warm',[R/'tools/prepare_external_warm_initializers_v1.py',c['endpoint'],checkpoint,c['floor_proof'],out])
  for method in ('raw_min','native_retained'):run(label+'_'+method+'_xml',[R/'tools/verify_external_warm_initializers_xml_v1.py',out/method])
  print('WARM_PREPARATION_AUDITED',c['case'],flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(warm,cases))
 assert all(sha(k)==h for k,h in bindings.items());(D/'preparation_terminal.json').write_text(json.dumps(dict(status='NEW_CORRECTED_NATIVE_SOURCE_AND_ALL3_MATCHED_WARM_XML_AUDITS_COMPLETE',source_checkpoint=str(checkpoint),cases=cases,scope='Preparation only; no corrected-epoch forecast metrics or complete paid workflow acceptance.'),indent=2)+'\n');print('PREPARATION_COMPLETE')
if __name__=='__main__':main()

"""Corrected preload native qualification on existing source layouts only."""
import concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
from export_external_excess_preload_v1 import encode
R=Path(__file__).resolve().parents[1];E=R/'experiments';O=E/'wbuart_utility_source_parity_v1_2026-10-20';B=R/'build/wbuart_corrected_utility_native_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);b=json.loads((B/'receipt.json').read_text());binary=Path(b['binary']);assert sha(binary)==b['binary_sha256']
 for n,h in b['bindings'].items():assert sha(Path(n))==h
 old_manifest=E/'wbuart_native_sources_v1_2026-10-20/manifest.json';old=json.loads(old_manifest.read_text());cases=[];refs={};runner=R/'tools/run_wbuart_native_utility_case_v1.py';bindings={str(p):sha(p) for p in [Path(__file__),runner,R/'tools/export_external_excess_preload_v1.py',B/'receipt.json',binary,old_manifest]}
 for c in old['cases']:
  w=c['width'];source=Path(c['output']);ref=json.loads((source/'verification.json').read_text());assert ref['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';refs[w]=source;ep=Path(c['endpoint']);e=json.loads(ep.read_text());domain=E/'wbuart_quality_domains_v1_2026-10-20'/f'w{w:03d}/verification.json';d=json.loads(domain.read_text());resource=[json.loads(x) for x in (domain.parent/'resources.jsonl').read_text().splitlines()];checkpoint=E/'wbuart_source_checkpoints_v1_2026-10-20'/f'w{w:03d}/source/initial.json';state=json.loads(checkpoint.read_text());assert state['overflow_units']==0;preload=O/'source_preloads'/f'w{w:03d}';preload.mkdir(parents=True);forecast=encode(resource,{int(n):v for n,v in state['ledger'].items()},e['graph_sha256'],d['graph_nodes']);zero=encode(resource,{},e['graph_sha256'],d['graph_nodes']);assert forecast==zero
  for name,text in [('forecast.risk',forecast),('zero.risk',zero)]:(preload/name).write_text(text)
  proof={'status':'FIXED_EXCESS_AND_ZERO_PRELOAD_INPUTS_EXPORTED_NATIVE_READBACK_PENDING','graph_sha256':e['graph_sha256'],'nodes':d['graph_nodes'],'positive_entries':0,'role':'Source zero-excess qualification fixture from independently verified legal source; not candidate target forecast.','bindings':{str(p):sha(p) for p in [checkpoint,domain,preload/'forecast.risk',preload/'zero.risk']}};(preload/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
  for arm in ['disabled','zero']:
   command=c['command'].copy();command[0]=str(binary);cases.append(dict(c,case=f'w{w:03d}/source/{arm}',role='source_qualification_only',output=str(O/'native'/f'w{w:03d}'/arm),command=command,utility_arm=arm,target_case=f'w{w:03d}/source',graph_nodes=d['graph_nodes'],preload_directory=str(preload)))
  for p in [source/'verification.json',source/'output.route',ep,domain,checkpoint,preload/'verification.json']:bindings[str(p)]=sha(p)
 manifest={'schema':'WBUART_FROZEN_NATIVE_UTILITY_V1','native_execution_admitted':True,'phase':'source_qualification','cases':cases,'bindings':bindings,'policy':'All3 existing source layouts x disabled/zero, same corrected native core and original fixed300 iteration/seed1/worker1 commands. Full physical/canonical/trace audits and all-node zero readback. Require original corrected source path byte parity and exact iterations/WL/CPD. No target labels or parameter changes.'};mp=O/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
 def run(c):
  log=O/(c['case'].replace('/','_')+'.log')
  with log.open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),c['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  vp=Path(c['output'])/'verification.json';v=json.loads(vp.read_text()) if vp.exists() else {};row={'case':c['case'],'exit_status':rc,'status':v.get('status'),'error':v.get('error'),'verification':str(vp)};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (O/'terminal.json').write_text(json.dumps({'rows':rows,'all_native_pass':all(r['exit_status']==0 for r in rows),'target_labels_generated':False},indent=2)+'\n')
 for c,row in zip(cases,rows):
  assert row['exit_status']==0;out=Path(c['output']);v=json.loads(Path(row['verification']).read_text());ref=json.loads((refs[c['width']]/'verification.json').read_text());assert v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and v['independent_trace_replay_pass'];assert sha(out/'output.route')==sha(refs[c['width']]/'output.route') and all(v[k]==ref[k] for k in ['iterations','wirelength','diagnostic_cpd_ns'])
 (O/'verification.json').write_text(json.dumps({'status':'ALL3_SOURCE_DISABLED_ZERO_PHYSICAL_CANONICAL_TRACE_AND_ORIGINAL_PATH_PARITY_PASS','rows':rows,'bindings':{str(mp):sha(mp),**{r['verification']:sha(Path(r['verification'])) for r in rows}},'new_target_labels':False,'nonzero_utility_qualified':False,'strict_unseen_admitted':False},indent=2)+'\n');print('SOURCE_UTILITY_PARITY_PASS',flush=True)
if __name__=='__main__':main()

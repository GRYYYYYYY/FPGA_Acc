"""Frozen source/all9 allMAP on/off observational qualification."""
import json,hashlib,concurrent.futures,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_allnet_map_batch_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);receipt=R/'build/wbuart_allnet_map_query_v1_2026-10-20/receipt.json';br=read(receipt);assert sha(br['binary'])==br['binary_sha256'];contract=E/'allnet_map_binary_contract_v1_2026-10-20/verification.json';assert all(sha(p)==h for p,h in read(contract)['bindings'].items());runner=R/'tools/run_wbuart_allnet_map_case_v1.py';jobs=[];allcases=[]
 for group,original in [('source',E/'wbuart_map_probe_on_qualification_v1_2026-10-20/manifest.json'),('target',E/'wbuart_map_probe_targets_v1_2026-10-20/manifest.json')]:
  base=read(original);cases=[]
  for c in base['cases']:
   if group=='source' and c['utility_arm']!='disabled':continue
   for enabled in [False,True]:
    name=c['target_case'];mode='on' if enabled else 'off';row=dict(c,case=name+'/'+mode,output=str(D/group/name/mode),allmap_enabled=enabled,reference_output=c['output']);row['command']=[br['binary'],*c['command'][1:]]
    if group=='target' and name=='w096/episode_01':row['output']=str(E/'wbuart_allnet_map_preflight_v1_2026-10-20'/mode);row['reuse']=True
    cases.append(row)
  base['cases']=cases;base['bindings']={str(p):sha(p) for p in [original,receipt,contract,runner,Path(__file__),Path(br['binary'])]};mp=D/(group+'_manifest.json');mp.write_text(json.dumps(base,indent=2)+'\n')
  for row in cases:
   allcases.append(row)
   if not row.get('reuse'):jobs.append((mp,row))
 def run(job):
  mp,row=job;log=D/(row['case'].replace('/','_')+'.log')
  with log.open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),row['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  print(row['case'],rc,flush=True);return {'case':row['case'],'exit_status':rc,'verification':str(Path(row['output'])/'verification.json')}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,jobs))
 (D/'terminal.json').write_text(json.dumps({'rows':results},indent=2)+'\n');assert all(x['exit_status']==0 for x in results)
 bindings={};rows=[]
 for c in allcases:
  out=Path(c['output']);ref=Path(c['reference_output']);v=read(out/'verification.json');old=read(ref/'verification.json');assert v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
  for n in ['output.route','owner_trace.tsv','expected_cost.tsv']:assert sha(out/n)==sha(ref/n),(c['case'],n)
  for k in ['native_work','iterations','wirelength','diagnostic_cpd_ns']:assert v[k]==old[k],(c['case'],k)
  rows.append({'case':c['case'],'output':str(out),'reused':c.get('reuse',False)})
  for p in [out/'verification.json',ref/'verification.json',out/'output.route',out/'owner_trace.tsv',out/'expected_cost.tsv']:
   bindings[str(p)]=sha(p)
  if c['allmap_enabled']:bindings[str(out/'allmap.bin')]=sha(out/'allmap.bin')
 for p in [D/'source_manifest.json',D/'target_manifest.json']:bindings[str(p)]=sha(p)
 (D/'verification.json').write_text(json.dumps({'status':'ALL3_SOURCE_ALL9_TARGET_ON_OFF_FULL_NATIVE_BYTE_TRACE_WORK_QOR_PARITY_PASS','rows':rows,'bindings':bindings,'scope':'Native observational exporter qualification; all matrices interpolation/domain verification and allNET model integration pending.'},indent=2)+'\n');print('ALLMAP_BATCH_PASS',len(rows),flush=True)
if __name__=='__main__':main()

"""Bounded native first-iteration acquisition with all costs and outcomes retained."""
import json,os,shutil,subprocess,time,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
def main():
 begin=time.perf_counter();spec=R/'experiments/mmc_native_first_iteration_protocol_v1_2026-10-18/protocol.json';p=json.loads(spec.read_text());assert all(sha(k)==h for k,h in p['bindings'].items());bp=R/'build/native_iteration_state_observer_v1_2026-10-10/receipt.json';b=json.loads(bp.read_text());assert all(sha(k)==h for k,h in b['bindings'].items());out=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';out.mkdir();stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(out/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=stat[19]))+'\n');bindings={**p['bindings'],str(spec):sha(spec),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};rows=[]
 for case in p['cases']:
  folder=out/case;folder.mkdir();(folder/'states').mkdir();stage=time.perf_counter()
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(R/f'experiments/mmc_multiplacement_inputs_v1_2026-10-18/{case}/mmc'/name,folder/name)
  stage=time.perf_counter()-stage;env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_ITERATION_STATE_DIR']=str(folder/'states');tick=time.perf_counter()
  with (folder/'native.log').open('x') as log:code=subprocess.run(p['command'],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  seconds=time.perf_counter()-tick;states=list((folder/'states').glob('round_*.tsv'));assert [x.name for x in states]==['round_1.tsv'];counts={};header=None;overflow=0
  with states[0].open() as f:
   for line in f:
    x=line.split();counts[x[0]]=counts.get(x[0],0)+1
    if x[0]=='H':header=x;assert x==['H','1','0','0']
    elif x[0]=='N':assert int(x[1])==counts['N']-1;overflow+=max(0,int(x[2])-int(x[3]));assert float(x[4])==1
    else:assert x[0]=='T'
  assert counts['N']==904438 and counts['H']==1 and counts['T']>0;files={str(q):sha(q) for q in [states[0],folder/'native.log',*(folder/n for n in ['design.blif','design.net','design.place'])]};row=dict(case=case,exit_status=code,complete_native_process_seconds=seconds,input_copy_seconds=stage,header=header,counts=counts,overflow_units=overflow,physical_tree_and_CID_admission_pending=True,eligible_for_legal_route_commit=False,files=files);(folder/'receipt.json').write_text(json.dumps(dict(bindings=bindings,**row),indent=2)+'\n');rows.append(row);print('FIRST_ITERATION_CAPTURED',json.dumps({k:v for k,v in row.items() if k!='files'}),flush=True)
 (out/'results.json').write_text(json.dumps(dict(status='all3_first_iteration_captures_complete_physical_validation_pending',bindings=bindings,cases=rows,elapsed_before_summary_seconds=time.perf_counter()-begin),indent=2)+'\n')
if __name__=='__main__':main()

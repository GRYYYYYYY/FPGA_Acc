"""All-node native tag oracle, preserving all36 prior component snapshot bytes."""
import json,hashlib,os,shutil,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/wbuart_setup_tag_observer_v1_2026-10-20';OLD=R/'experiments/wbuart_delay_components_v1_2026-10-20';O=R/'experiments/wbuart_setup_tags_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);b=json.loads((B/'receipt.json').read_text());binary=Path(b['binary']);assert b['exit_status']==0 and sha(binary)==b['binary_sha256']
 for d in [b,json.loads((B/'protocol.json').read_text())]:
  for n,h in d['bindings'].items():assert sha(Path(n))==h
 previous=json.loads((OLD/'protocol.json').read_text());v=json.loads((OLD/'verification.json').read_text());assert len(v['rows'])==36 and v['checks']==560448
 for n,h in v['bindings'].items():assert sha(Path(n))==h
 names=['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','clock_constraints.tsv','initial_connections.tsv','components_before.tsv','components_after.tsv','updated_connections.tsv','delay_changes.tsv'];bindings={str(p):sha(p) for p in [Path(__file__),B/'protocol.json',B/'receipt.json',binary,OLD/'protocol.json',OLD/'verification.json']};(O/'protocol.json').write_text(json.dumps({'jobs':previous['jobs'],'bindings':bindings,'byte_parity_files':names,'scope':'Full native node tags A/R/CL/CC/S before/after each existing frozen perturbation, including constant generators and all ignored nodes. Public const analyzer reads only. All prior nine output files must remain byte equal. No target routing or changed model/test parameters.'},indent=2)+'\n')
 def run(job):
  d=O/job['case'];d.mkdir(parents=True);old=OLD/job['case']
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(old/name,d/name);assert sha(old/name)==sha(d/name)
  cmd=job['command'].copy();cmd[0]=str(binary);env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_TIMING_PERTURBATION']=job['mode']
  with (d/'native.log').open('x') as f:rc=subprocess.call(cmd,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT)
  parity={name:(d/name).exists() and sha(d/name)==sha(old/name) for name in names};passed=rc==0 and all(parity.values()) and not list(d.glob('*.route')) and all((d/n).exists() for n in ['setup_tags_before.tsv','setup_tags_after.tsv']);row={'case':job['case'],'exit_status':rc,'passed':passed,'prior_output_byte_parity':parity,'bindings':{str(p):sha(p) for p in [d/'native.log',*[d/n for n in names+['setup_tags_before.tsv','setup_tags_after.tsv'] if (d/n).exists()]]}};(d/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');print('NATIVE_TAGS_CAPTURE',job['case'],passed,flush=True);return {'case':job['case'],'passed':passed,'receipt':str(d/'receipt.json'),'sha256':sha(d/'receipt.json')}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,previous['jobs']))
 (O/'terminal.json').write_text(json.dumps({'status':'ALL36_NATIVE_TAG_ORACLE_CAPTURES_TERMINAL','rows':rows,'all_pass':all(r['passed'] for r in rows),'bindings':{str(O/'protocol.json'):sha(O/'protocol.json')},'reference_model_qualified':False},indent=2)+'\n')
if __name__=='__main__':main()

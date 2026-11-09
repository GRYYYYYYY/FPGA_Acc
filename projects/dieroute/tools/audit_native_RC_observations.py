"""Audit frozen routed0 observations from an arbitrary native-route protocol."""
from pathlib import Path
import argparse,csv,hashlib,json

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);args=parser.parse_args();D=args.directory.resolve();refs={}
 def sha(p):
  p=Path(p);h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  refs[str(p)]=h.hexdigest();return refs[str(p)]
 def rows(p):
  with Path(p).open() as f:return list(csv.DictReader(f))
 p=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text());assert m['status']=='all_native_RC_observations_terminal_requires_review'
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 tasks={int(v['id']):v for v in rows(p['connections'])};summary=[]
 for case in p['cases']:
  name=case['name'];env=case['environment'];probe=rows(env['PERSISTROUTE_VPR_TIMING_INPUT']);assert len(probe)==len(tasks)
  for row in probe:
   assert row['routed']=='0' and row['delay_ps']=='0';t=tasks[int(row['task_id'])];assert all(row[k]==t[k] for k in ['net_id','source','sink'])
  f=Path(env['PERSISTROUTE_VPR_TIMING_OUTPUT']);observations=rows(f);values={int(v['task_id']):v for v in observations};assert len(values)==len(observations)==len(tasks) and set(values)==set(tasks);sha(f)
  qfile=D/name/'native_validation/validation.json';q=json.loads(qfile.read_text());assert q['legal'] and q['vpr_exit_status']==0
  cmd=case['command']
  for flag,key in [('route','route_sha256'),('arch','arch_sha256'),('circuit','circuit_sha256'),('net','net_sha256'),('place','place_sha256'),('rr-graph','rr_graph_sha256'),('vpr','vpr_sha256')]:assert sha(cmd[cmd.index('--'+flag)+1])==q['inputs'][key]
  for filename,key in [('vpr_analysis.stdout','stdout_sha256'),('vpr_analysis.stderr','stderr_sha256')]:assert sha(qfile.parent/filename)==q[key]
  cpds={int(v['critical_path_delay_ps']) for v in observations};assert len(cpds)==1 and abs(next(iter(cpds))-q['critical_path_delay_ns']*1000)<=1;sha(qfile)
  summary.append({'name':name,'connections':len(observations),'wirelength':q['total_wirelength'],'cpd_ns':q['critical_path_delay_ns'],'native_delays_not_overridden':True})
 for f in [D/'protocol.json',D/'manifest.json',Path(__file__).resolve()]:sha(f)
 result={'status':'native_routed0_observations_provenance_and_quality_reviewed','cases':summary,'source_sha256':refs,'scope':'Native loaded routes and routed0 queries with exact task/endpoints and hashes. Integerps rounding;notnativefloat-bitidentity,repair or generalization.','research_complete':False}
 with (D/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(summary))
if __name__=='__main__':main()

"""Bind unmodified native delays to exact routes and compare all connection IDs."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,struct
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_native_RC_observation_20261020'
def rows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def main():
 refs={}
 def sha(p):
  p=Path(p);h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  refs[str(p)]=h.hexdigest();return refs[str(p)]
 p=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text());assert m['status']=='all_three_native_RC_observations_terminal_requires_review'
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 tasks={int(v['id']):v for v in rows(p['connections'])};observations={};quality={}
 for case in p['cases']:
  name=case['name'];env=case['environment'];probe=rows(env['PERSISTROUTE_VPR_TIMING_INPUT']);assert len(probe)==len(tasks) and all(v['routed']=='0' and v['delay_ps']=='0' for v in probe)
  for v in probe:
   t=tasks[int(v['task_id'])];assert all(v[k]==t[k] for k in ['net_id','source','sink'])
  out=Path(env['PERSISTROUTE_VPR_TIMING_OUTPUT']);values={int(v['task_id']):{k:int(x) for k,x in v.items()} for v in rows(out)};assert set(values)==set(tasks)
  qfile=D/name/'native_validation/validation.json';q=json.loads(qfile.read_text());assert q['legal'] and q['vpr_exit_status']==0
  cpds={v['critical_path_delay_ps'] for v in values.values()};assert len(cpds)==1 and abs(next(iter(cpds))-q['critical_path_delay_ns']*1000)<=1
  cmd=case['command'];route=Path(cmd[cmd.index('--route')+1]);assert sha(route)==q['inputs']['route_sha256']
  for f,key in [('vpr_analysis.stdout','stdout_sha256'),('vpr_analysis.stderr','stderr_sha256')]:assert sha(qfile.parent/f)==q[key]
  for f in [qfile,out]:sha(f)
  observations[name]=values;quality[name]={'wirelength':q['total_wirelength'],'cpd_ns':q['critical_path_delay_ns']}
 deltas={}
 for before,after in [('baseline','parent'),('parent','alternative')]:
  changes=[observations[after][t]['delay_ps']-observations[before][t]['delay_ps'] for t in tasks]
  deltas[before+'_to_'+after]={'changed_connections':sum(v!=0 for v in changes),'minimum_delta_ps':min(changes),'maximum_delta_ps':max(changes),'histogram_ps':dict(sorted(collections.Counter(changes).items()))}
 prefix=R/'work/width_coverage_native_costs_20261018/elliptic_28x22_cw320_seed1/input';treefile=R/'work/width_coverage_parents_20261018/parents/elliptic_28x22_cw320_seed1/route.route_trees.csv';parent=collections.defaultdict(dict)
 for row in rows(treefile):parent[int(row['net_id'])][int(row['child'])]=int(row['parent'])
 handles=[open(str(prefix)+ext,'rb') for ext in ['.nodes','.edges']];maps=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];nodes,edges=maps
 keyrows=[]
 for tid,t in tasks.items():
  net=int(t['net_id'])
  if net not in [381,396]:continue
  total=0;v=int(t['sink']);seen=set()
  while v!=int(t['source']):
   assert v not in seen;seen.add(v);u=parent[net][v];begin,count,_=struct.unpack_from('<IHH',nodes,8*u);weights=[struct.unpack_from('<IHH',edges,8*e)[2] for e in range(begin,begin+count) if struct.unpack_from('<I',edges,8*e)[0]==v];assert weights;total+=min(weights);v=u
  keyrows.append({'task':tid,'net':net,'source':int(t['source']),'sink':int(t['sink']),'parent_fixed_edge_sum_ps':total,**{name+'_native_ps':obs[tid]['delay_ps'] for name,obs in observations.items()},'parent_minus_baseline_native_ps':observations['parent'][tid]['delay_ps']-observations['baseline'][tid]['delay_ps']})
 for x in maps:x.close()
 for f in handles:f.close()
 for f in [treefile,Path(str(prefix)+'.nodes'),Path(str(prefix)+'.edges'),D/'protocol.json',D/'manifest.json',Path(__file__).resolve()]:sha(f)
 result={'status':'three_routes_native_no_override_connection_delays_independently_compared','connections_per_route':len(tasks),'quality':quality,'connection_delay_deltas':deltas,'critical_net_rows':keyrows,'source_sha256':refs,'scope':'routed0 preserves native net_delay. All task/endpoints and route hashes bound; delays rounded to integerps. Observations do not prove causality, native float-bit identity,RC optimality,general quality or FPGA timing.','research_complete':False}
 with (D/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','critical_net_rows']}))
 print(json.dumps(keyrows))
if __name__=='__main__':main()

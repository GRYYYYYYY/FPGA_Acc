"""Compare native routed delays and independently summed packed paths for two cases."""
import collections,csv,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'work/sb_development_native_delay_calibration_20261015'
def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
def load(q):return json.loads(Path(q).read_text())
def table(q):
 with Path(q).open() as f:return list(csv.DictReader(f))
def main():
 protocol=load(P/'protocol.json');manifest=load(P/'manifest.json');assert manifest['status']=='two_native_delay_probes_complete_requires_audit'
 for x in [protocol,load(P/'launch_protocol.json')]:
  for q,h in x['source_sha256'].items():assert sha(q)==h,q
 results=[];proofs=[]
 for c in protocol['cases']:
  d=P/c['case'];step=next(s for s in manifest['steps'] if s['case']==c['case']);assert step['returncode']==0 and step['command']==c['command']
  prefix=Path(c['route_prefix']);local_input=Path(c['local_timing_input']);local_output=Path(str(local_input).replace('.input.csv','.output.csv'));replay=load(prefix.parent/'replay_audit.json');assert replay['cpu_legal'] and replay['final_resources_and_costs_byte_equivalent']
  for q in [local_input,local_output]:assert sha(q)==replay['source_sha256'][str(q)]
  local={int(r['task_id']):r for r in table(local_input)};sta={int(r['task_id']):r for r in table(local_output)};native={int(r['task_id']):r for r in table(d/'native_observations.csv')};probe={int(r['task_id']):r for r in table(d/'native_probe.input.csv')}
  assert len(local)==len(sta)==len(native)==len(probe)==c['connections'] and local.keys()==sta.keys()==native.keys()==probe.keys()
  inp=c['input_prefix'];tasks=list(struct.iter_unpack('<IIIIHHIII',Path(inp+'.tasks').read_bytes()));nodes=list(struct.iter_unpack('<IHH',Path(inp+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(inp+'.edges').read_bytes()));assert len(tasks)==c['connections']
  paths=collections.defaultdict(list)
  for r in table(str(prefix)+'.paths.csv'):
   path=paths[int(r['task_id'])];assert int(r['path_index'])==len(path);path.append(int(r['resource_id']))
  assert set(paths)==set(local)
  errors=[];crit=[];slack=[]
  for task in tasks:
   tid,net,source,sink=task[:4];r=local[tid];b=probe[tid];assert [int(r[k]) for k in ['net_id','source','sink']]==[net,source,sink] and r['routed']=='1' and b['routed']=='0' and b['delay_ps']=='0'
   assert {k:v for k,v in r.items() if k not in ['routed','delay_ps']}=={k:v for k,v in b.items() if k not in ['routed','delay_ps']}
   previous=source;delay=0
   for node in paths[tid]:
    begin,count,_=nodes[previous];values={edges[i][2] for i in range(begin,begin+count) if edges[i][0]==node};assert len(values)==1;delay+=values.pop();previous=node
   assert previous==sink and delay==int(r['delay_ps'])==int(sta[tid]['delay_ps'])
   errors.append(int(native[tid]['delay_ps'])-delay);crit.append(abs(int(native[tid]['criticality_q'])-int(sta[tid]['criticality_q'])));slack.append(abs(int(native[tid]['slack_ps'])-int(sta[tid]['slack_ps'])))
  text=(d/'vpr.stdout').read_text()
  for marker in ['Finished loading route file','Completed routing consistency check successfully.','Circuit successfully routed','VPR succeeded']:assert marker in text
  printed=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1]);assert printed==c['baseline_cpd_ns']
  native_cpd={int(r['critical_path_delay_ps']) for r in native.values()};local_cpd={int(r['critical_path_delay_ps']) for r in sta.values()};assert len(native_cpd)==len(local_cpd)==1;nc=next(iter(native_cpd));lc=next(iter(local_cpd));assert abs(nc-printed*1000)<=0.51
  q=load(prefix.parent/'native_validation/validation.json');assert q['legal']
  assert sha(c['command'][c['command'].index('--read_rr_graph')+1])==q['inputs']['rr_graph_sha256']
  for name,key in [('circuit.net','net_sha256'),('circuit.place','place_sha256'),('native.route','route_sha256')]:assert sha(d/'native'/name)==q['inputs'][key]
  results.append(dict(case=c['case'],arm=c['arm'],connections=len(tasks),exact_integer_ps_matches=errors.count(0),native_minus_local_ps_histogram=dict(sorted(collections.Counter(errors).items())),maximum_absolute_delay_error_ps=max(map(abs,errors)),native_cpd_ps=nc,local_override_cpd_ps=lc,native_minus_local_cpd_ps=nc-lc,native_printed_cpd_ns=printed,maximum_absolute_criticality_q_difference=max(crit),maximum_absolute_slack_ps_difference=max(slack),native_zero_delay_connections=sum(int(r['delay_ps'])==0 for r in native.values()),local_zero_delay_connections=sum(int(r['delay_ps'])==0 for r in local.values())))
  proofs.extend([d/'vpr.stdout',d/'vpr.stderr',d/'native_observations.csv',d/'native_probe.input.csv',local_input,local_output,prefix.parent/'replay_audit.json',prefix.parent/'native_validation/validation.json'])
 proofs.extend([P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'run.py',Path(__file__).resolve()])
 report=dict(status='two_additional_development_final_routes_native_delays_and_local_path_sums_independently_compared',cases=results,total_connections=sum(r['connections'] for r in results),source_sha256={str(q):sha(q) for q in proofs},scope='Onecurrentlylegalfinalrouteeach:diffeqremainingtailandalu4flat. Nativequerydoesnotoverridenetdelays;task/source/sinkjoins,independentpackedpathsums,actualnativelegalityandCPDchecked. Observationalcalibrationwithroundedpsnotpairedalgorithmstudy,allroutes/floatbitexact,causalprooforboardtiming.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],cases=results,total_connections=report['total_connections'])))
if __name__=='__main__':main()

"""Check actual native delays against independently summed final packed RR paths."""
import collections,csv,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'work/sb_remaining_tail_native_delay_calibration_20261015'
def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
def table(q):
 with Path(q).open() as f:return list(csv.DictReader(f))
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='native_delay_probe_complete_requires_audit' and m['returncode']==0 and m['command']==p['command']
 for q,h in p['source_sha256'].items():assert sha(q)==h,q
 prefix=Path(p['route_prefix']);parent=json.loads((prefix.parent.parent.parent/'postrun_audit.json').read_text())
 local_input=Path(p['local_timing_input']);local_output=Path(str(local_input).replace('.input.csv','.output.csv'))
 for q in [local_input,local_output]:assert sha(q)==parent['source_sha256'][str(q)]
 local={int(r['task_id']):r for r in table(local_input)};native={int(r['task_id']):r for r in table(P/'native_observations.csv')};sta={int(r['task_id']):r for r in table(local_output)};probe={int(r['task_id']):r for r in table(P/'native_probe.input.csv')}
 assert len(local)==len(native)==len(sta)==len(probe)==1920 and local.keys()==native.keys()==sta.keys()==probe.keys()
 inp=p['input_prefix'];tasks=list(struct.iter_unpack('<IIIIHHIII',Path(inp+'.tasks').read_bytes()));nodes=list(struct.iter_unpack('<IHH',Path(inp+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(inp+'.edges').read_bytes()));paths=collections.defaultdict(list)
 for row in table(str(prefix)+'.paths.csv'):
  target=paths[int(row['task_id'])];assert int(row['path_index'])==len(target);target.append(int(row['resource_id']))
 assert set(paths)==set(local)
 errors=[];criticality=[];slack=[]
 for task in tasks:
  tid,net,source,sink=task[:4];r=local[tid];b=probe[tid]
  assert [int(r[k]) for k in ['net_id','source','sink']]==[net,source,sink] and r['routed']=='1' and b['routed']=='0' and b['delay_ps']=='0'
  assert {k:v for k,v in r.items() if k not in ['routed','delay_ps']}=={k:v for k,v in b.items() if k not in ['routed','delay_ps']}
  previous=source;delay=0
  for node in paths[tid]:
   begin,count,_=nodes[previous];values={edges[i][2] for i in range(begin,begin+count) if edges[i][0]==node};assert len(values)==1,('ambiguous_or_missing_path_edge',tid,previous,node)
   delay+=values.pop();previous=node
  assert previous==sink and delay==int(r['delay_ps'])==int(sta[tid]['delay_ps'])
  errors.append(int(native[tid]['delay_ps'])-delay);criticality.append(abs(int(native[tid]['criticality_q'])-int(sta[tid]['criticality_q'])));slack.append(abs(int(native[tid]['slack_ps'])-int(sta[tid]['slack_ps'])))
 text=(P/'vpr.stdout').read_text()
 for marker in ['Finished loading route file','Completed routing consistency check successfully.','Circuit successfully routed','VPR succeeded']:assert marker in text
 printed=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1]);assert printed==p['baseline_cpd_ns']==10.8661
 native_cpd={int(v['critical_path_delay_ps']) for v in native.values()};local_cpd={int(v['critical_path_delay_ps']) for v in sta.values()};assert native_cpd==local_cpd=={10866}
 assert min(errors)==-2 and max(errors)==2 and errors.count(0)==1266 and max(criticality)==32 and max(slack)==5
 q=json.loads((prefix.parent/'native_validation/validation.json').read_text())
 for flag,key in [('--read_rr_graph','rr_graph_sha256')]:assert sha(p['command'][p['command'].index(flag)+1])==q['inputs'][key]
 for name,key in [('circuit.net','net_sha256'),('circuit.place','place_sha256'),('native.route','route_sha256')]:assert sha(P/'native'/name)==q['inputs'][key]
 files=[P/'protocol.json',P/'manifest.json',P/'run.py',P/'vpr.stdout',P/'vpr.stderr',P/'native_observations.csv',local_input,local_output,prefix.parent.parent.parent/'postrun_audit.json',Path(__file__).resolve()]
 result=dict(status='same_final_native_route_1920_connection_delays_and_independent_local_path_sums_compared',connections=1920,exact_integer_ps_matches=errors.count(0),native_minus_local_ps_histogram=dict(sorted(collections.Counter(errors).items())),maximum_absolute_delay_error_ps=max(map(abs,errors)),native_cpd_ps=10866,local_override_cpd_ps=10866,native_printed_cpd_ns=printed,maximum_absolute_criticality_q_difference=max(criticality),maximum_absolute_slack_ps_difference=max(slack),native_zero_delay_connections=sum(int(r['delay_ps'])==0 for r in native.values()),local_zero_delay_connections=sum(int(r['delay_ps'])==0 for r in local.values()),source_sha256={str(f):sha(f) for f in files},scope='One actualfinalnativelylegalSB3layerex5premainingtailroute. Routed0hookdoesnotreplacenetdelay;fullsource/sink/taskjoins,independentpackedpathsumandnativeCPDmatchverified. Nativeandlocalvaluesroundedtointegerps;notfloatbitexact,allroutes/architectures,causalexclusionorhardwaretimingproof. CPDregressionrelativetobaselinecannotbesimplyascribedtolargeconversionerroronthissameobservedroute.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()

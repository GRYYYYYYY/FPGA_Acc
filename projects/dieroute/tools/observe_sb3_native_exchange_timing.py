"""Observe loaded native route delays with routed=0; no delay overrides."""
import csv,hashlib,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_native_exchange_timing_observation_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(path):
  path=Path(path);h=hashlib.sha256()
  with path.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  refs[str(path)]=h.hexdigest();return h.hexdigest()
 base=R/'work/sb3_ex5p_two_net_native_validation_v2_20261015';protocol=json.loads((base/'protocol.json').read_text());prior=json.loads((base/'result.json').read_text());case=protocol['case'];native=Path(case['native_case'])
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 tasks=list(csv.DictReader(Path(case['connections']).open()));assert len(tasks)==1920
 api=R/'work/vpr_four_layer_build_20261015/source_vtr/vpr/src/base/vpr_api.cpp';text=api.read_text()
 assert 'if (routed != 0)' in text and 'std::llround(net_delay[net_id][pin_index] * 1e12)' in text
 for f in [api,base/'protocol.json',base/'result.json',Path(case['connections']),Path(__file__).resolve()]:sha(f)
 (P/'protocol.json').write_text(json.dumps(dict(status='frozen_before_native_observation',source_sha256=refs.copy(),all_rows_routed=0,connection_rows=1920,scope='Load each actual candidate route; routed0 reads existing native delay without overrides. Source hook exports conservative minimum sink-block slack, not an independently exact atom-pin perconnection budget.',adopted=False,research_complete=False),indent=2)+'\n')
 outcomes=[]
 for trial in prior['outcomes']:
  label=trial['label'];d=P/label;d.mkdir();source_route=base/label/'native.route';assert sha(source_route)==trial['native_route_sha256']
  input_path=d/'observe.input.csv';output_path=d/'observe.output.csv'
  with input_path.open('w') as stream:
   writer=csv.writer(stream);writer.writerow(['iteration','task_id','net_id','source','sink','routed','delay_ps','criticality_q'])
   for task in tasks:writer.writerow([0,task['id'],task['net_id'],task['source'],task['sink'],0,0,0])
  command=[sys.executable,protocol['validator'],'--vpr',protocol['vpr'],'--device','DieRouteSBScale3']
  for flag,name in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:command+=['--'+flag,str(native/name)]
  command+=['--route',str(source_route),'--channel-width','80','--work-dir',str(d/'native_validation'),'--baseline-wirelength',str(case['baseline_wirelength']),'--baseline-cpd-ns',str(case['baseline_cpd_ns'])]
  env={k:v for k,v in os.environ.items() if not k.startswith(('PERSISTROUTE_','DIEROUTE_'))}
  env.update(PERSISTROUTE_VPR_TIMING_INPUT=str(input_path),PERSISTROUTE_VPR_TIMING_OUTPUT=str(output_path))
  with (d/'observe.log').open('w') as log:completed=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env)
  assert completed.returncode==0,label
  quality=json.loads((d/'native_validation/validation.json').read_text());old=trial['validation']
  assert quality['legal'] and (quality['total_wirelength'],quality['critical_path_delay_ns'])==(old['total_wirelength'],old['critical_path_delay_ns'])
  observed=list(csv.DictReader(output_path.open()));assert len(observed)==len(tasks) and {int(v['task_id']) for v in observed}=={int(v['id']) for v in tasks}
  cpds={int(v['critical_path_delay_ps']) for v in observed};assert len(cpds)==1 and abs(next(iter(cpds))-1000*old['critical_path_delay_ns'])<=1
  displaced=trial['displaced_net'];ids={int(v['id']) for v in tasks if int(v['net_id'])==displaced};rows=[{k:int(v) for k,v in row.items()} for row in observed if int(row['task_id']) in ids]
  for f in [input_path,output_path,d/'native_validation/validation.json']:sha(f)
  outcomes.append(dict(label=label,native_qor_unchanged=True,cpd_ps=next(iter(cpds)),connections_observed=len(observed),displaced_net=displaced,displaced_connections=rows))
  print(json.dumps(outcomes[-1]),flush=True)
 report=dict(status='three_native_exchange_routes1920each_no_override_observation_qor_unchanged',outcomes=outcomes,source_sha256=refs,
  adopted=False,research_complete=False,scope='Observed actual loaded native routing with every input routed0; no delay replacement. Existing hook reports min sink-block slack over atom sinks; conservative observation is not an exact perpin budget. No new routing or quality improvement.')
 (P/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

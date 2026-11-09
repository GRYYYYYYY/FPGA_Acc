"""Existing pre-search observer on exact current3 inputs; no target route labels."""
from pathlib import Path
import json,hashlib,time,os,subprocess,resource,shutil,math,struct
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 begin=time.perf_counter();O=R/'experiments/mmc_current_initial_timing_snapshots_v1_2026-10-19';O.mkdir(exist_ok=False);B=R/'build/native_initial_criticality_snapshot_v2_2026-10-10';receipt=B/'receipt.json';b=json.loads(receipt.read_text());binary=B/'sequence_vpr';assert sha(binary)==b['binary_sha256'];oldroot=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';oldpayload=oldroot/'initial_connection_criticalities.json';identity={x['connection_id']:x for x in json.loads(oldpayload.read_text())};oldproof=json.loads((oldroot/'verification.json').read_text());assert sha(oldpayload)==oldproof['bindings'][str(oldpayload)];command=json.loads((oldroot/'startup.json').read_text())['command'];assert command[0]==str(binary);bindings={str(p):sha(p) for p in [receipt,binary,oldpayload,oldroot/'verification.json',oldroot/'startup.json',Path(__file__).resolve()]};plans=[]
 for file,h in b['bindings'].items():assert sha(file)==h
 for i in range(1,4):
  case=f'episode_{i:02d}';root=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}';ep=root/'demand/endpoints.json';meta=json.loads(ep.read_text());stage=root/'staged_input_verification_v1.json';s=json.loads(stage.read_text());assert s['all_native_logical_NET_local_pin_identities_preserved'] and not s['native_route_labels_generated'];assert command[command.index('--read_rr_graph')+1]==meta['inputs']['graph']['path'];assert sha(meta['inputs']['graph']['path'])==meta['graph_sha256'];src=root/'mmc'
  for name in ['design.blif','design.net','design.place']:
   f=src/name;h=sha(f);assert s['bindings'].get(str(f))==h;bindings[str(f)]=h
  bindings[str(ep)]=sha(ep);bindings[str(stage)]=sha(stage);plans.append({'case':case,'endpoint':str(ep),'source':str(src),'cwd':str(O/case),'argv':command,'environment_set':{'ROUTECAST_INITIAL_CRITICALITY':str(O/case/'criticality.tsv')}})
 save(O/'execution_protocol.json',{'jobs':plans,'bindings':bindings,'observer_source':str(B/'observer.cpp'),'scope':'Fixed3 exact current geometries; existing REAL native getter wrapper exports all pins before first connection search then exits. No routed target label, fallback, price or seed tuning. Old vector used for stable logical pin metadata only.','total_setup_seconds_before_protocol':time.perf_counter()-begin});rows=[]
 for plan in plans:
  d=Path(plan['cwd']);d.mkdir();tick=time.perf_counter()
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(Path(plan['source'])/name,d/name);assert sha(d/name)==bindings[str(Path(plan['source'])/name)]
  copy_seconds=time.perf_counter()-tick;env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(plan['environment_set'])
  def limits():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  print('CURRENT_INITIAL_TIMING_START',plan['case'],flush=True);tick=time.perf_counter()
  with (d/'native.log').open('x') as log:
   child=subprocess.Popen(plan['argv'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits);save(O/'live_process.json',{'case':plan['case'],'pid':child.pid,'startticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19]});code=child.wait()
  seconds=time.perf_counter()-tick
  try:
   assert code==0 and 'ROUTECAST INITIAL CRITICALITY SNAPSHOT 119473' in (d/'native.log').read_text() and not list(d.glob('*.route'));observed={}
   for seq,line in enumerate((d/'criticality.tsv').open(),1):
    w=line.split();assert len(w)==10 and w[0]=='C' and int(w[1])==seq;key=int(w[2]),int(w[4]);assert key not in observed;value=struct.unpack('f',struct.pack('f',float(w[5])))[0];assert math.isfinite(value) and 0<=value<=float(w[6])<=1 and w[8] in ['0','1'] and w[9] in ['0','1'];observed[key]=w
   assert len(observed)==119473;meta=json.loads(Path(plan['endpoint']).read_text());records=[];keys=set()
   for q in sorted(meta['connections'],key=lambda x:x['connection_id']):
    prior=identity[q['connection_id']];assert prior['net']==q['net_id'];key=q['net_id'],prior['local_sink_pin'];assert key not in keys;keys.add(key);w=observed[key];assert int(w[3])==prior['global_pin'] and w[8]=='0';records.append({'connection_id':q['connection_id'],'net':q['net_id'],'local_sink_pin':key[1],'global_pin':int(w[3]),'source_rr':q['source'],'target_rr':q['sink'],'criticality_float32_text':w[5],'maximum_text':w[6],'exponent_text':w[7]})
   assert len(records)==115572 and keys=={k for k,w in observed.items() if w[8]=='0'};save(d/'initial_connection_criticalities.json',records);row={'case':plan['case'],'status':'SNAPSHOT_ONLY_EXIT0_NO_ROUTE_RAW_PIN_VALIDATION_PASS','all_sink_pins':len(observed),'physical_connections':len(records),'copy_and_input_hash_seconds':copy_seconds,'native_startup_snapshot_seconds':seconds,'independent_verification_pending':True}
  except Exception as e:
   row={'case':plan['case'],'status':'SNAPSHOT_OR_PIN_VALIDATION_FAILED','returncode':code,'error':repr(e)};rows.append(row);save(O/'terminal.json',{'status':'FAILED_PRESERVED_STOPPED_NO_RETRY','rows':rows});raise
  save(d/'capture_receipt.json',{'row':row,'bindings':{str(f):sha(f) for f in [Path(plan['endpoint']),d/'criticality.tsv',d/'initial_connection_criticalities.json',d/'native.log',d/'design.place',d/'design.net',d/'design.blif']}});rows.append(row);save(O/'progress.json',{'rows':rows});print('CURRENT_INITIAL_TIMING_DONE',plan['case'],flush=True)
 save(O/'terminal.json',{'status':'ALL3_CURRENT_INPUT_INITIAL_TIMING_SNAPSHOT_ONLY_PASS_INDEPENDENT_ADMISSION_PENDING','rows':rows,'total_seconds_before_receipt':time.perf_counter()-begin})
if __name__=='__main__':main()

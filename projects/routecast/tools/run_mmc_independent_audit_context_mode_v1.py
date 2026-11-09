"""Fresh independently parsed context shared via fork; each original auditor runs in isolation."""
import argparse,hashlib,json,os,resource,runpy,signal,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
import immutable_xml_prediction_audit as topology_module
import buffered_rc_node_classes as electrical_module
import exact_rc_lattice_unique_pairs_v1 as scale_module
from source_binding_v2 import closure
from pre_route_endpoints import sha

def write(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def main(model,output,mode):
 assert mode in ['separate','shared']
 started=time.perf_counter();model=Path(model).resolve();out=Path(output).resolve()
 assert not out.exists()
 limit=8*2**30;free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=limit+8*2**30
 resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
 physical=R/'tools/verify_resident_demand_frame_physical_v4.py';events=R/'tools/verify_resident_events_round_schedule_cache_v6.py'
 receipt=json.loads((model/'receipt.json').read_text());protocol=json.loads((model/'protocol.json').read_text());assert receipt['bindings']==protocol['bindings']
 endpoint=next(Path(p) for p in receipt['bindings'] if p.endswith('/endpoints.json'));ep=json.loads(endpoint.read_text());graph=Path(ep['inputs']['graph']['path']).resolve();expected_digest=ep['graph_sha256']
 bindings=closure([Path(__file__),physical,events]);bindings.update({str(p):sha(p) for p in [model/'receipt.json',model/'protocol.json',model/'initial.json',model/'floors.json',model/'sketch.json',endpoint]})
 assert all(sha(p)==h for p,h in receipt['bindings'].items())
 out.mkdir();write(out/'process.json',dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text(),args=sys.argv))
 write(out/'protocol.json',dict(bindings=bindings,context_mode=mode,graph=str(graph),graph_expected_sha256=expected_digest,independent_context_from_original_XML=True,shared_mutable_audit_state=False,all_original_auditor_bodies_unchanged=True,all_acquisition_forks_hashing_and_audits_paid=True,limit_bytes=limit,margin_bytes=8*2**30,child_timeout_seconds=1200,scope='Same harness: fresh graph/scale per child in separate mode, once per batch in shared mode. Isolated fork children in both modes. No model/ledger/epoch/path result reuse, no historical parsed context. Local audit integration only, not end-to-end net benefit.'))
 try:
  tick=time.perf_counter();digest=expected_digest
  context=xml=ids=classes=switches=scale=None
  if mode=='shared':
   xml=topology_module.ImmutableXMLAudit(graph,expected_digest)
   ids,classes,switches,digest=electrical_module.read(graph)
   context=(xml,ids,classes,switches,digest)
   assert digest==expected_digest
   scale=scale_module.exact_scale(ids,classes,switches,xml.graph.edges)
  write(out/'fresh_context.json',dict(mode=mode,parent_parse_and_exact_scale_seconds=time.perf_counter()-tick,graph_sha256=digest,parent_fresh_context_builds=int(mode=='shared')))
  stages=[]
  for name,tool,args in [('initial',physical,[str(model),'initial',str(out/'initial_verification.json')]),('sketch',physical,[str(model),'sketch',str(out/'sketch_verification.json')]),('events',events,[str(model),'mmc',str(out/'events_verification.json'),'1'])]:
   assert all(sha(Path(p))==h for p,h in bindings.items())
   free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=limit+8*2**30
   tick=time.perf_counter();sys.stdout.flush();sys.stderr.flush();pid=os.fork()
   if pid==0:
    with (out/(name+'.log')).open('x') as log:
     os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
     try:
      calls=dict(topology=0,electrical=0,scale=0)
      original_topology=topology_module.ImmutableXMLAudit;original_electrical=electrical_module.read;original_scale=scale_module.exact_scale
      def cached_topology(path,expected):
       assert Path(path).resolve()==graph and expected==digest
       calls['topology']+=1
       if mode=='shared':return xml
       return original_topology(path,expected)
      def cached_electrical(path):
       assert Path(path).resolve()==graph
       calls['electrical']+=1
       if mode=='shared':return ids,classes,switches,digest
       return original_electrical(path)
      def cached_scale(a,b,c,d):
       calls['scale']+=1
       if mode=='shared':
        assert a is ids and b is classes and c is switches and d is xml.graph.edges
        return scale
       return original_scale(a,b,c,d)
      topology_module.ImmutableXMLAudit=cached_topology;electrical_module.read=cached_electrical;scale_module.exact_scale=cached_scale
      sys.argv=[str(tool),*args];runpy.run_path(str(tool),run_name='__main__')
      assert calls==dict(topology=1,electrical=1,scale=1)
      write(out/(name+'_context_calls.json'),calls)
     except BaseException:
      traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
     sys.stdout.flush();sys.stderr.flush();os._exit(0)
   # The parent owns only this fork child; COW prevents child audit mutations reaching siblings.
   try:start=Path('/proc',str(pid),'stat').read_text()
   except FileNotFoundError:start=None
   write(out/(name+'_process.json'),dict(pid=pid,start_stat=start,auditor=str(tool),args=args,forked_from=os.getpid(),limit_bytes=limit))
   print('SHARED AUDIT START',name,pid,flush=True);deadline=time.monotonic()+1200;timed_out=False
   while True:
    done,status=os.waitpid(pid,os.WNOHANG)
    if done:break
    if time.monotonic()>=deadline:
     timed_out=True;os.kill(pid,signal.SIGTERM);stop=time.monotonic()+30
     while True:
      done,status=os.waitpid(pid,os.WNOHANG)
      if done:break
      if time.monotonic()>=stop:os.kill(pid,signal.SIGKILL);_,status=os.waitpid(pid,0);break
      time.sleep(.1)
     break
    time.sleep(.1)
   code=os.waitstatus_to_exitcode(status);row=dict(exit_status=code,timed_out=timed_out,seconds=time.perf_counter()-tick);write(out/(name+'_terminal.json'),row);stages.append(row)
   assert code==0 and not timed_out,'Failed child preserved; no retry'
  for path,old in [('initial_verification.json','initial_physical_verification.json'),('sketch_verification.json','sketch_physical_verification.json'),('events_verification.json','verification.json')]:
   a=json.loads((out/path).read_text());b=json.loads((model/old).read_text());assert {k:v for k,v in a.items() if k!='bindings'}=={k:v for k,v in b.items() if k!='bindings'}
   assert all(sha(p)==h for p,h in a['bindings'].items())
  assert sha(graph)==digest and all(sha(Path(p))==h for p,h in bindings.items())
  outputs={str(p):sha(p) for p in out.glob('*.json')}
  write(out/'verification.json',dict(all_pass=True,all_three_original_auditors_executed=True,all_proofs_semantically_equal_closed_standalone_audits=True,context_mode=mode,fresh_graph_context_loads=1 if mode=='shared' else 3,fresh_exact_scale_scans=1 if mode=='shared' else 3,each_isolated_child_topology_electrical_and_scale_requests=1,stages=stages,full_batch_seconds=time.perf_counter()-started,bindings=bindings,outputs=outputs,scope='Local fresh-context MMC audit batch; no measured native workflow net benefit or paired speedup. Corruption rejection remains a separate requirement.',promoted=False))
  write(out/'terminal.json',dict(exit_status=0,all_three_audits_and_parity_pass=True));print('PASS all3 original audits and complete proof parity',flush=True)
 except BaseException as error:
  write(out/'terminal.json',dict(exit_status=1,error_type=type(error).__name__,error=str(error),no_retry=True));raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('output');p.add_argument('mode',choices=['separate','shared']);a=p.parse_args();main(a.model,a.output,a.mode)

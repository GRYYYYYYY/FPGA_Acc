"""Evaluate prospectively registered MMC forecasts against admitted future labels."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from prospective_pressure_metrics_v1 import metrics,gate
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,separators=(',',':'));f.write('\n')
def main():
 N=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19';T=R/'experiments/mmc_prospective_pressure_targets_v2_2026-10-19';O=R/'experiments/mmc_prospective_pressure_evaluation_v2_2026-10-19';P=R/'experiments/mmc_prospective_pressure_protocol_v2_2026-10-19/protocol.json';A=P.parent/'constant_control_addendum_v1.json';admission=N/'prediction_admission.json';proof=T/'verification.json'
 if not admission.exists() or not proof.exists():raise SystemExit('NOT_READY: admitted predictions and independently split labels required')
 spec=json.loads(P.read_text());add=json.loads(A.read_text());a=json.loads(admission.read_text());v=json.loads(proof.read_text());assert a['all3_independent_prediction_audits_pass'] and v['status']=='all3_admitted_traces_split_at_iteration1';assert a['bindings'][str(A)]==sha(A) and add['parent_protocol_sha256']==sha(P)
 bindings={str(q):sha(q) for q in [P,A,admission,proof,pathlib.Path(__file__).resolve(),R/'tools/prospective_pressure_metrics_v1.py']}
 for evidence in [a,v]:
  for q,h in evidence['bindings'].items():assert sha(q)==h,q;bindings[q]=h
 cmd=spec['native_commands'][0]['argv'];graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);assert sha(graph)==spec['bindings'][str(graph)];domain=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:domain.append(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 domain.sort();assert len(domain)==len(set(domain))==spec['expected_domain_size'];k=spec['top_k'];assert k==len(domain)//20
 source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';sourceproof=source.parent/'independent_xml_verification_v1.json';sp=json.loads(sourceproof.read_text());assert sp['all_native_paths_exact'] and sp['all_uniqueNET_occupancy_matches_full_printed_audit'];assert sp['bindings'][str(source)]==sha(source)
 def ledger_scores(p):
  assert a['bindings'][str(p)]==sha(p);frame=json.loads(p.read_text());assert len(frame['records'])==115572;ledger={int(n):x for n,x in frame['ledger'].items()};assert all(type(x) is int and x>0 for x in ledger.values());return [ledger.get(n,0) for n in domain]
 O.mkdir();write(O/'domain.json',domain);predictions={}
 # Materialize ALL3 input-derived vectors before reading any future target payload.
 source_scores=ledger_scores(source)
 for name in spec['episodes']:
  lookup={x['model']:pathlib.Path(x['path']) for x in a['predictions'] if x['episode']==name};assert set(lookup)=={'raw_min','native_retained'}
  predictions[name]={'native_retained':ledger_scores(lookup['native_retained']),'raw_min':ledger_scores(lookup['raw_min']),'previous_native':source_scores,'uniform_risk':[1]*len(domain)};p=O/(name+'_predictions.json');write(p,predictions[name]);bindings[str(p)]=sha(p)
 write(O/'prediction_vector_admission.json',dict(bindings=bindings,all3_vectors_materialized_before_future_payload_reads=True,domain_sha256=sha(O/'domain.json')))
 rows=[]
 for name in spec['episodes']:
  p=T/name/'targets.json';assert v['bindings'][str(p)]==sha(p);future=json.loads(p.read_text());assert future['first_target_iteration']==2;results={}
  for target,raw in future['targets'].items():
   truth={int(n):x for n,x in raw.items()};assert all(type(x) is int and x>0 for x in truth.values());values=[truth.get(n,0) for n in domain];results[target]={m:metrics(scores,values,k,domain) for m,scores in predictions[name].items()}
  primary=results['sum_checkpoint_overflow_units'];decision=gate(primary['native_retained'],{m:primary[m] for m in ['raw_min','previous_native','uniform_risk']},k,len(domain));rows.append(dict(episode=name,primary_gate=decision,metrics=results));print(name,decision,flush=True)
 assert all(sha(q)==h for q,h in bindings.items())
 write(O/'results.json',dict(status='all3_registered_pressure_forecasts_evaluated',bindings=bindings,episodes=rows,all3_primary_gate_pass=all(x['primary_gate']=='pass' for x in rows),accepted_full_workflow_gain=False,strict_unseen_family_admitted=False,scope='Known-family future-pressure forecast test only. Constant-control addendum applied; no postoutcome selection. Native utility, complete elapsed time, family holdout and hardware claims remain unproven.'))
if __name__=='__main__':main()

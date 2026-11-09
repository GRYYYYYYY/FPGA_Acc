"""Publish new isolated frames after epoch-bound serial batch admission."""
import json,sys,os,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
from criticality_net_admission_v1 import validate
from criticality_objective_admission_v1 import score
from multiplicative_net_congestion_v1 import cost
from atomic_model_batch_v1 import State
from versioned_digest_cache_v1 import Cache

def publish(path,frame):
 temporary=path.with_suffix('.pending')
 with temporary.open('x') as stream:
  json.dump(frame,stream,separators=(',',':'));stream.write('\n');stream.flush();os.fsync(stream.fileno())
 os.link(temporary,path);temporary.unlink()

def main():
 audit=R/'experiments/mmc_objective_terminal_batch_verification_v1_2026-10-18/verification.json'
 core=R/'experiments/atomic_model_batch_core_v1_2026-10-18/verification.json'
 v=json.loads(audit.read_text());c=json.loads(core.read_text());assert v['status']==c['status']=='pass'
 bindings={**v['bindings'],**c['bindings'],str(audit):sha(audit),str(core):sha(core),**closure([Path(__file__)])}
 source=R/'experiments/mmc_objective_terminal_subset_v1_2026-10-18'
 inputs=json.loads((source/'protocol.json').read_text())['inputs']
 out=R/'experiments/mmc_terminal_batch_commit_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=inputs,policy='Fixed independently audited candidates only; old canonical snapshot digest and all involved NET epochs bound before prepare. Revalidate full combined physical trees, budgets, both ledgers, per-node overflow and affectedNET original-snapshot objective. Commit one serial opaque ticket and publish a complete isolated frame with exclusive atomic hard-link visibility.',scope='Per-case isolated research model transition, not cross-case/filesystem transactions or interprocess synchronization. Original inputs unchanged. Native legalization/forecast utility/end-to-end timing still unproved.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  _,digest,nodes,f,rc,_=load_endpoints(inputs['case_01']['endpoint']);caps=f['capacities'];weight=rc.scale//(20*10**9)
  spans={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}}
  for case,data in inputs.items():
   base,crit,b=load(data['endpoint'],data['node_base_proof'],data['criticality_directory'],len(nodes),rc.scale);bindings.update(b)
   frame=json.loads(Path(data['frame']).read_text());assert frame['graph_sha256']==digest and frame['scale']==rc.scale and frame['history']=={}
   artifact=source/(case+'.json');assert bindings[str(artifact)]==sha(artifact)
   selection=json.loads(artifact.read_text());updates={r['connection_id']:r for r in selection['chosen_replacements']};assert len(updates)==len(selection['chosen_replacements'])
   expected_summary=next(s for s in v['summaries'] if s['case']==case)
   assert Fraction(expected_summary['global_objective_delta'])<=0
   needed={e for r in frame['records'] for e in r['answer']['physical_edge_ids']}
   needed.update(e for r in updates.values() for e in r['answer']['physical_edge_ids'])
   slots={e:s for s,e in enumerate(f['edge_ids']) if e in needed};assert slots.keys()==needed
   def own_connection(r):return {r['source']}|{f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids']}
   oldbyid={r['connection_id']:r for r in frame['records']};assert updates.keys()<=oldbyid.keys()
   changed={r['net_id'] for cid,r in updates.items() if r['answer']!=oldbyid[cid]['answer']}
   epochs={str(r['net_id']):frame['epochs'][str(r['net_id'])] for r in updates.values()}
   def transition(old):
    oldgroups=defaultdict(list);newgroups=defaultdict(list)
    for r in old['records']:
     oldgroups[r['net_id']].append(r);newgroups[r['net_id']].append(updates.get(r['connection_id'],r))
    oldledger=Counter();newledger=Counter();oldind=Counter();newind=Counter();objective_deltas={}
    ledger={int(p):n for p,n in old['ledger'].items() if n}
    for net,recs in oldgroups.items():
     qs=[{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in recs]
     oa=validate(f,rc,slots,qs,recs);na=validate(f,rc,slots,qs,newgroups[net])
     oldledger.update(oa['owned']);newledger.update(na['owned'])
     for r in recs:oldind.update(own_connection(r))
     for r in newgroups[net]:newind.update(own_connection(r))
     if net in changed:
      resources=oa['owned']|na['owned'];prices={p:cost(base[p],0,ledger.get(p,0)-(p in oa['owned']),caps[p],False,weight*spans.get(p,0)) for p in resources}
      delta=score(f,slots,newgroups[net],crit,prices,na['delays'])-score(f,slots,recs,crit,prices,oa['delays'])
      if delta>0:raise ValueError('batch NET objective increase')
      objective_deltas[str(net)]=str(delta)
    assert dict(oldledger)==ledger and dict(oldind)=={int(p):n for p,n in old['independent_connection_ledger'].items() if n}
    if any(n>max(oldledger[p],caps[p]) for p,n in newledger.items()):raise ValueError('batch node overflow increase')
    overflow=sum(max(0,n-caps[p]) for p,n in newledger.items());assert overflow==expected_summary['overflow']
    result=dict(old,records=[updates.get(r['connection_id'],r) for r in old['records']],ledger=dict(newledger),independent_connection_ledger=dict(newind),epochs=dict(old['epochs']),overflow_units=overflow,eligible_for_legal_route_commit=False,batch_update_policy='VERIFIED_TERMINAL_ATOMIC_MODEL_BATCH_V1',scope='Isolated admitted RouteCast demand model, residual overflow remains; not a legal native route or evidence of prediction/utility gain.')
    for net in changed:result['epochs'][str(net)]+=1
    return result,dict(case=case,changed_NETs=sorted(changed),changed_queries=sum(r['answer']!=oldbyid[cid]['answer'] for cid,r in updates.items()),objective_deltas=objective_deltas,overflow=overflow,full_repriced_objective_delta=expected_summary['global_objective_delta'],full_objective_admission_transferred_by_exact_bound_source_and_candidate_bytes=True)
   state=State(frame);before=state.digest;ticket=state.prepare(before,epochs,transition)
   assert state.digest==before and all(sha(p)==h for p,h in bindings.items())
   event=state.commit(ticket);committed=state.snapshot();assert state.digest!=before
   folder=out/case;folder.mkdir();publish(folder/'frame.json',committed)
   restored=State(json.loads((folder/'frame.json').read_text()));assert restored.digest==state.digest
   with (folder/'event.json').open('x') as stream:json.dump(dict(source_frame_sha256=sha(data['frame']),source_model_digest=before,committed_frame_sha256=sha(folder/'frame.json'),expected_epochs=epochs,**event),stream,indent=2)
   summary={k:event[k] for k in ['case','changed_queries','overflow','generation','full_repriced_objective_delta']};summary['changed_NETs']=len(changed)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.rglob('*.json')})
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='all3_isolated_model_batches_committed_replay_audit_pending',bindings=bindings,summaries=summaries,scope='Serial in-process atomic snapshots and exclusive complete-file publication; no original frame writes. Independent replay of persisted state/epoch/ledgers pending; no native or full-flow gain.'),stream,indent=2)

if __name__=='__main__':main()

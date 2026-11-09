"""Extract sampled per-RR native pressure from existing independently replayed traces."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 root=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18'
 proof=root/'cohort_verification.json';v=json.loads(proof.read_text());assert v['status']=='pass' and v['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass']
 diagnostic=root/'guard_resource_type_diagnostic_v1.json';g=json.loads(diagnostic.read_text());assert g['status']=='pass'
 rows={(r['case'],r['arm']):r for r in g['rows']}
 bindings={**v['bindings'],**g['bindings'],str(proof):sha(proof),str(diagnostic):sha(diagnostic),**closure([Path(__file__)])}
 out=R/'experiments/mmc_checkpoint_pressure_targets_v1_2026-10-18';out.mkdir()
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,phase='iteration_end_after_local_opins',targets=['max sampled overflow units perRR','sum sampled overflow units perRR','number of designated end checkpoints over capacity perRR'],domain='All original RR IDs; zero for never overused at this designated complete checkpoint phase. Absence is not zero occupancy.',scope='Exactly6already-exposed partial-seed off/on traces, not cold policy or unseen labels. Sampling omits within-NET/transient peaks. No new native run, forecast gate, failure classifier, RRR identity metric or time gain.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  ep=json.loads((R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path'])
  caps=array('Q');kinds=[];stack=[]
  for event,node in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(node);continue
   if node.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
    assert int(node.get('id'))==len(caps);caps.append(int(node.get('capacity')));kinds.append(node.get('type'));stack[-2].remove(node);node.clear()
   if node.tag=='rr_nodes':break
   stack.pop()
  for case,arm in sorted(rows):
   trace=R/'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18'/case/arm/'owner_trace.tsv';assert bindings[str(trace)]==sha(trace)
   expected=rows[(case,arm)]['iterations'];peak=Counter();area=Counter();frequency=Counter();selected=False;iteration=None;seen=set();checkpoints=[];types=Counter()
   with trace.open() as source:
    for line in source:
     if line.startswith('CP '):
      _,phase,i=line.split();selected=phase=='iteration_end_after_local_opins';iteration=int(i);seen=set();types=Counter();continue
     if selected and line.startswith('V '):
      _,n,occupancy,capacity=line.split();n=int(n);occupancy=int(occupancy);capacity=int(capacity)
      assert n not in seen and caps[n]==capacity and occupancy>capacity
      seen.add(n);types[kinds[n]]+=1;overflow=occupancy-capacity;peak[n]=max(peak[n],overflow);area[n]+=overflow;frequency[n]+=1
     if selected and line.strip()=='CE':
      e=expected[str(iteration)];assert len(seen)==e['overused_RR_nodes'] and dict(types)==e['overused_RR_types']
      checkpoints.append(dict(iteration=iteration,overused_RR_nodes=len(seen),types=dict(types)));selected=False
   assert [r['iteration'] for r in checkpoints]==list(range(1,len(expected)+1)) and checkpoints[-1]['overused_RR_nodes']==0
   assert sum(frequency.values())==sum(r['overused_RR_nodes'] for r in checkpoints)
   assert all(peak[n]<=area[n] and frequency[n]<=len(checkpoints) for n in peak)
   target=out/(case+'_'+arm+'.json')
   with target.open('x') as stream:json.dump(dict(case=case,policy=arm,source_trace_sha256=sha(trace),graph_sha256=sha(graph),RR_domain_size=len(caps),implicit_zero_means='zero sampled overflow at designated checkpoints, never zero occupancy',peak_overflow_units=dict(peak),sum_checkpoint_overflow_units=dict(area),checkpoints_overused=dict(frequency),checkpoints=checkpoints),stream)
   bindings[str(target)]=sha(target)
   summary=dict(case=case,policy=arm,end_checkpoints=len(checkpoints),ever_overused_RRs=len(peak),ever_overused_types=dict(Counter(kinds[n] for n in peak)),max_sampled_overflow_units=max(peak.values()),sum_checkpoint_overflow_units=sum(area.values()))
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(path)==h for path,h in bindings.items())
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='all6_existing_trace_pressure_targets_extracted_checkpoint_counts_matched',bindings={**bindings,str(out/'protocol.json'):sha(out/'protocol.json')},summaries=summaries,scope='Supplemental policy-specific sampled pressure labels only; original cold/final occupancy gates unchanged. No new native execution, heldout certification or performance claim. Independent per-resource aggregate replay remains pending.'),stream,indent=2)

if __name__=='__main__':main()

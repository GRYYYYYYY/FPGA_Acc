"""Independent occurrence-list reduction of each sampled per-RR pressure target."""
import json,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 root=R/'experiments/mmc_checkpoint_pressure_targets_v1_2026-10-18';receipt=root/'receipt.json';v=json.loads(receipt.read_text());assert v['status']=='all6_existing_trace_pressure_targets_extracted_checkpoint_counts_matched'
 bindings={**v['bindings'],str(receipt):sha(receipt),**closure([Path(__file__)])};rows=[];cache=Cache()
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  for summary in v['summaries']:
   case,policy=summary['case'],summary['policy'];target=root/(case+'_'+policy+'.json');t=json.loads(target.read_text())
   trace=R/'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18'/case/policy/'owner_trace.tsv';assert sha(trace)==t['source_trace_sha256']
   occurrences=defaultdict(list);iteration_nodes={};phase=None;iteration=None
   with trace.open() as stream:
    for line in stream:
     if line[:3]=='CP ':
      words=line.split();phase=words[1];iteration=int(words[2])
      if phase=='iteration_end_after_local_opins':assert iteration not in iteration_nodes;iteration_nodes[iteration]=set()
     elif line.strip()=='CE':phase=None
     elif phase=='iteration_end_after_local_opins' and line[:2]=='V ':
      words=line.split();n=int(words[1]);excess=int(words[2])-int(words[3]);assert excess>0 and 0<=n<t['RR_domain_size']
      assert n not in iteration_nodes[iteration];iteration_nodes[iteration].add(n);occurrences[n].append((iteration,excess))
   peak={};area={};frequency={}
   for n,items in occurrences.items():
    values=[excess for i,excess in sorted(items)];assert len({i for i,excess in items})==len(values)
    peak[n]=max(values);area[n]=sum(values);frequency[n]=len(values)
   for key,expected in [('peak_overflow_units',peak),('sum_checkpoint_overflow_units',area),('checkpoints_overused',frequency)]:assert {int(n):value for n,value in t[key].items()}==expected
   assert sorted(iteration_nodes)==list(range(1,summary['end_checkpoints']+1)) and not iteration_nodes[summary['end_checkpoints']]
   assert [len(iteration_nodes[r['iteration']]) for r in t['checkpoints']]==[r['overused_RR_nodes'] for r in t['checkpoints']]
   assert len(occurrences)==summary['ever_overused_RRs'] and sum(area.values())==summary['sum_checkpoint_overflow_units']
   row=dict(case=case,policy=policy,resources_verified=len(occurrences),checkpoint_occurrences_verified=sum(frequency.values()),all3_per_resource_targets_equal=True)
   rows.append(row);print(json.dumps(row),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (root/'independent_verification_v1.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,rows=rows,scope='Independent perRR occurrence-list reductions and complete designated checkpoint bookkeeping on previously admitted traces. Zero means no sampled overflow, not zero occupancy. Supplemental exposed-policy targets only, no cold gate replacement or new native run.'),stream,indent=2)

if __name__=='__main__':main()

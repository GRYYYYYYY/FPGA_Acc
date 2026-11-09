"""Freeze source-only exposures first, then extract six admitted trace NET targets."""
import hashlib,json
from array import array
from pathlib import Path
from native_NET_event_targets_v1 import extract

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=Path('experiments/mmc_NET_pressure_exposure_v1_2026-10-18');receipt=source/'receipt.json';r=json.loads(receipt.read_text());assert r['status']=='all90_source_only_NET_exposure_vectors_materialized';plan=json.loads((source/'protocol.json').read_text());domains=json.loads((source/'NET_domains.json').read_text());out=Path('experiments/mmc_NET_pressure_targets_v1_2026-10-18');out.mkdir(exist_ok=False)
 cp=Path('experiments/mmc_native_owner_trace_replay_v2_2026-10-18/cohort_verification.json');cohort=json.loads(cp.read_text());assert cohort['status']=='pass';bindings={str(p.resolve()):sha(p) for p in [receipt,source/'protocol.json',source/'NET_domains.json',cp,Path(__file__),Path('tools/native_NET_event_targets_v1.py')]}
 for p,h in r['bindings'].items():assert sha(p)==h
 # Semantic fixture retains a zero-event NET and rejects broken links/counts.
 stats=[dict(iteration=1,NET_operations=1,connection_operations=1,heap_pushes=3,heap_pops=2)]
 text='TRACE 1\nCP initial 0\nT 10 0 1 0 1 99\nT 20 0 1 0 1 98\nCE\nQ 1 1 10 overuse 99 2 1\nB 1 1 10 1 0 1\nE 1 1 10\nT 10 0 1 0 1 99\nEE\nS 1 1 1 3 2\nEND 1 1 1\n'
 fixture=out/'valid_fixture.tsv';fixture.write_text(text);values,summary=extract(fixture,[10,20],stats);assert values[20]==dict(first_iteration_overuse_guard=0,total_overuse_guard_decisions=0,total_successful_NET_route_operations=0) and values[10]['total_successful_NET_route_operations']==1
 bads={'wrong_event_NET':text.replace('E 1 1 10','E 1 1 20'),'unknown_NET':text.replace('Q 1 1 10','Q 1 1 30'),'wrong_stats':text.replace('S 1 1 1 3 2','S 1 2 1 3 2'),'missing_END':text.replace('END 1 1 1\n',''),'missing_zero_event_NET':text.replace('T 20 0 1 0 1 98\n','')}
 for name,bad in bads.items():
  path=out/(name+'.tsv');path.write_text(bad)
  try:extract(path,[10,20],stats)
  except AssertionError:pass
  else:raise AssertionError(name)
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,frozen_source_plan=str((source/'protocol.json').resolve()),positive_fixture='valid_fixture.tsv',rejected_fixtures=list(bads),scope=plan['scope']),f,indent=2)
 manifest={};rows=[]
 for case in plan['cases']:
  ids=domains[case]['NET_ids']
  for policy in plan['policies']:
   proofpath=Path('experiments/mmc_native_owner_trace_replay_v2_2026-10-18')/case/(policy+'.json');assert sha(proofpath)==cohort['bindings'][str(proofpath.resolve())];proof=json.loads(proofpath.read_text());assert proof['status']=='pass' and proof['incomplete_attempts']==0
   trace=Path('experiments/mmc_native_owner_cascade_trace_v1_2026-10-18')/case/policy/'owner_trace.tsv';assert sha(trace)==proof['bindings'][str(trace.resolve())];bindings[str(proofpath.resolve())]=sha(proofpath);bindings[str(trace.resolve())]=sha(trace)
   values,summary=extract(trace,ids,proof['iteration_stats']);assert summary['decisions']==proof['decisions'] and summary['total_overuse_decisions']==proof['first_true_native_guards']['overuse'];rows.append(dict(case=case,policy=policy,summary=summary))
   for target in plan['targets']:
    path=out/(case+'__'+policy+'__'+target+'.u64');a=array('Q',(values[net][target] for net in ids))
    with path.open('xb') as f:a.tofile(f)
    manifest[case+'__'+policy+'__'+target]=dict(path=str(path.resolve()),sha256=sha(path),typecode='Q',itemsize=a.itemsize,values=len(a),byteorder=__import__('sys').byteorder)
   print('NET EVENT TARGETS EXTRACTED',case,policy,summary['successful_NET_operations'],flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'vector_manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='all18_NET_target_vectors_extracted',bindings=bindings,rows=rows,zero_event_NETs_retained=True,scope='Per-NET observed guards and successful wholeNET operation counts only. No per-NET heap, connection work, sole cause or native utility claim.'),f,indent=2)
if __name__=='__main__':main()

"""Observe one live frozen host predictor, then audit/evaluate its full receipt."""
import json,time,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha

def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  args=(p/'cmdline').read_bytes().split(b'\0');stat=(p/'stat').read_text();start=stat[stat.rfind(')')+2:].split()[19]
  return {'pid':pid,'start_ticks':start,'argv':[x.decode() for x in args if x]}
 except (OSError,ValueError,IndexError):return None

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'authenticated_host_completion_chain';out.mkdir();(out/'source').mkdir()
 parent=b/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';matches=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  ident=identity(int(p.name))
  if ident and 'tools/stereo_authenticated_prediction.py' in ident['argv']:matches.append(ident)
 if len(matches)!=1:raise ValueError('expected one live exact host predictor')
 process=matches[0];names=['stereo_host_completion_chain.py','audit_stereo_prediction.py','streaming_prediction_audit.py','physical_prediction_audit.py','net_union_topology.py','prepared_csr.py','pre_route_endpoints.py','rr_graph.py','evaluate_stereo_baseline.py','prediction_metrics.py','stream_metric_domain.py']
 sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 protocol={'observed_process':process,'parent_protocol_sha256':sha(parent/'protocol.json'),'sources':sources,'scope':'observe original live predictor without restart; full original XML audit then native-label evaluator; no full baseline parity or feedback/net-benefit claim'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps({'stage':'waiting_for_full_prediction_receipt','process':process}),flush=True)
 while not (parent/'receipt.json').exists():
  if identity(process['pid'])!=process:raise RuntimeError('original predictor terminal/missing without full receipt; no restart')
  time.sleep(10)
 assert sha(parent/'protocol.json')==protocol['parent_protocol_sha256']
 r=json.loads((parent/'receipt.json').read_text());assert r['connections']==81610 and r['nets']==61314 and r['prediction_sha256']==sha(parent/'prediction.json') and r['journal_sha256']==sha(parent/'net_results.jsonl')
 stages=[];name=parent.name
 for cmd in [['python3','-u','tools/audit_stereo_prediction.py','--prediction',name],['python3','-u','tools/evaluate_stereo_baseline.py','--prediction',name]]:
  assert all(sha(Path('tools')/n)==h for n,h in sources.items());start=time.monotonic();print(json.dumps({'stage':'launch','command':cmd}),flush=True)
  result=subprocess.run(cmd,env=__import__('os').environ.copy());stages.append({'command':cmd,'exit_code':result.returncode,'wall_s':time.monotonic()-start});(out/'stages.json').write_text(json.dumps(stages,indent=2)+'\n')
  if result.returncode:raise RuntimeError('dependent audit/evaluation failed; no restart')
 assert all(sha(Path('tools')/n)==h for n,h in sources.items())
 receipt={'prediction_receipt_sha256':sha(parent/'receipt.json'),'stages':stages,'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope']}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()

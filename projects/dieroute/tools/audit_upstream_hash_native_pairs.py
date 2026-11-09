"""Compare all emitted route artifacts before interpreting matched process times."""
import argparse,hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'work/upstream_target_hash_native_pairs_20261018'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def outputs(directory):return {p.name:p for p in directory.glob('route.*') if p.is_file()}
def compare(reference,candidate):
 a,b=outputs(reference),outputs(candidate)
 assert a and a.keys()==b.keys(), 'route artifact inventory differs'
 checks=[]
 for name in sorted(a):
  if name=='route.json':
   x,y=[json.loads(p.read_text()) for p in [a[name],b[name]]]
   assert 'wall_ms' in x and 'wall_ms' in y
   x.pop('wall_ms');y.pop('wall_ms');assert x==y,name
  else:assert a[name].read_bytes()==b[name].read_bytes(),name
  checks.append({'name':name,'reference_sha256':sha(a[name]),'candidate_sha256':sha(b[name]),'comparison':'all_fields_except_wall_ms' if name=='route.json' else 'byte_equal'})
 return checks

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check-only',action='store_true');args=p.parse_args()
 protocol=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text())
 ready=m['status']=='ten_native_pair_attempts_terminal_requires_independent_review'
 if args.check_only:print(json.dumps({'all_attempts_terminal':ready,'review_started':False}));return
 assert ready,'Native pair queue not terminal'
 assert len(m['steps'])==len(protocol['steps'])==10
 refs={};rows=[];reference=D/'runs/pair0_parent';q=json.loads((reference/'route.json').read_text());epochs=q['iterations'];assert q['legal'] and not q['board_result']
 for f,h in protocol['source_sha256'].items():assert sha(Path(f))==h,f
 for step in m['steps']:
  assert step['returncode']==0 and step['status']=='terminal_requires_review',step['label']
  run=D/'runs'/step['label'];mp=run/'manifest.json';s=json.loads(mp.read_text());assert s['status']=='online_router_completed_equivalence_audit_required' and s['returncode']==0 and s['requests']==epochs
  checks=compare(reference,run)
  assert sum(c['name'].endswith('.input.csv') for c in checks)==epochs
  assert sum(c['name'].endswith('.output.csv') for c in checks)==epochs
  ns=step['complete_process_wall_ns'];assert ns>=s['cold_start_through_shutdown_ns']>0
  rows.append({'label':step['label'],'complete_process_wall_ns':ns,'engine_startup_through_shutdown_ns':s['cold_start_through_shutdown_ns'],'comparisons':checks})
  refs[str(mp)]=sha(mp)
 bylabel={v['label']:v for v in rows};pairs=[]
 for i in range(5):
  a,b=[bylabel[f'pair{i}_{arm}']['complete_process_wall_ns'] for arm in ['parent','candidate']]
  pairs.append({'pair':i,'parent_ns':a,'candidate_ns':b,'parent_over_candidate':a/b,'candidate_change_percent':100*(b/a-1)})
 for f in [D/'protocol.json',D/'manifest.json',D/'launch_receipt.json',D/'supervise.py',Path(__file__).resolve()]:refs[str(f)]=sha(f)
 result={'status':'ten_native_runs_outputs_equivalent_and_matched_process_times_reviewed','runs':rows,'pairs':pairs,'median_paired_parent_over_candidate':statistics.median(v['parent_over_candidate'] for v in pairs),'source_sha256':refs,'scope':'One ex5p development case, five alternating-order pairs on shared host. Complete wrapper process time includes persistent STA startup and shutdown. Warm caches and concurrent workloads; no representative generalization, physical FPGA performance, universal equivalence or adoption. Native legality of this new run set requires separate native writeback validation.','adopted':False,'research_complete':False}
 out=D/'independent_pair_audit.json'
 with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()

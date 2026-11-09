"""Count source-level pre-search descriptor scans on the completed real trace."""
from pathlib import Path
import json,hashlib,collections
R=Path(__file__).resolve().parents[1];W=R/'work'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 o=W/'scalar_estimator_validation_work_20261021';o.mkdir();a=W/'resident_estimator_trace_capture_20261020/full_trace_audit.json';index=W/'resident_estimator_trace_capture_20261020/full_trace_audit.index.jsonl';audit=json.loads(a.read_text());phases=collections.Counter()
 with index.open() as f:
  for line in f:
   if line.strip():phases[json.loads(line)['phase']]+=1
 assert phases=={1:19768,2:19768} and audit['jobs']==sum(phases.values())
 n,e,portals=[audit[k] for k in ['nodes','edges','portals']];forward=W/'resident_both_word_full_trace_replay_20261021/source/upstream_word_top.cpp';reverse=W/'resident_both_word_full_trace_replay_20261021/source/tail_word_top.cpp'
 assert forward.read_bytes()==(W/'resident_upstream_word_HLS_20261020/source/upstream_word_top.cpp').read_bytes();assert reverse.read_bytes()==(W/'resident_tail_word_HLS_v2_20261021/source/tail_word_top.cpp').read_bytes()
 # This counts complete descriptor-loop iterations, not actual bus transactions.
 categories={'forward_node_row_and_dynamic_flag_checks':n*phases[1],'forward_edge_field_checks':e*phases[1],'forward_resource_reserved_field_checks':n*phases[1],'reverse_node_row_and_dynamic_flag_checks':n*phases[2],'reverse_incoming_arc_checks':e*phases[2],'reverse_portal_fields_and_dynamic_banned_checks':portals*phases[2],'reverse_resource_reserved_field_checks':n*phases[2],'reverse_edge_reserved_field_checks':e*phases[2]}
 result={'status':'real_trace_source_level_validation_scan_iterations_counted','graphs':1,'forward_jobs':phases[1],'reverse_jobs':phases[2],'node_count':n,'edge_count':e,'portal_count':portals,'validation_loop_iterations':categories,'total_validation_loop_iterations_excluding_variable_seed_checks':sum(categories.values()),'source_sha256':{str(p):sha(p) for p in [a,index,forward,reverse,W/'resident_both_word_trace_review_queue_20261021/audit.json',Path(__file__)]},'scope':'Source-level complete validation loop iterations for valid real trace calls,not number of distinct resources,RTL cycles or measured HBM bytes. Repeated structural checks mixed with dynamic allowed/tree/banned/state checks cannot all be removed or cached safely. Seed checks,scratch initialization,search and all transport are excluded,so this is not a performance model or speedup proof.','design_obligations_before_amortization':['Device-owned authenticated graph/session generation,not two caller-supplied equal identity fields','Validate full graph/CSR/portal shape and canonical fields once before publishing a resident immutable lease','Prevent graph mutation during jobs;drain or revoke outstanding work before reuse,reset or generation changes','Keep dynamic snapshot state and allowed/tree/banned flags separately validated and version-bound','Preserve malformed/stale/failure rejection,resource read journals and partial-output invalidation','Count validation/load/lease setup,transport,backpressure,queue failures and native checks in end-to-end timing'],'research_complete':False}
 (o/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['node_count','edge_count','portal_count','validation_loop_iterations','total_validation_loop_iterations_excluding_variable_seed_checks']}))
if __name__=='__main__':main()

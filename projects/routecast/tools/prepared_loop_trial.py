"""Measured prepared frontend/search/atomic proposal loop and native timing guard."""
import json,re,shutil,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha,placements
from rr_graph import read_rr_graph
from prepared_endpoints import PreparedEndpoints
from prepared_templates import PreparedTemplates
from regional_search_cache import CachedRegionalSearch
from hybrid_repair import repair
from affected_connections import affected
from rr_batch_occupancy import BatchOccupancy
from physical_prediction_audit import audit
from feedback_scores import scores
from connection_golden import Result

run_start=time.monotonic();out=Path('experiments/prepared_loop_2026-10-04')
if out.exists():raise ValueError('fresh output required')
parent=Path('experiments/matched_hpwl_trial_2026-10-04');native_base=Path('experiments/native_iteration_capture_2026-10-04');config=json.loads((native_base/'protocol.json').read_text());e=json.loads(Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json').read_text());inputs=e['inputs']
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
placements_input={str(cid):{'path':str((parent/f'candidate_{cid}.place').resolve()),'sha256':sha(parent/f'candidate_{cid}.place')} for cid in range(1,8)}
p={'scope':'replay known seven controls to measure integrated pipeline, no new quality/heldout evidence','inputs':inputs,'placements':placements_input,'native_inputs':config['inputs'],'baseline_native_receipt_sha256':sha(native_base/'receipt.json'),'refinement_rounds':2,'margin':1,'cache_groups':128,'proposal_rule':'min channel span, then overuse, then candidate ID with baseline0','accept_rule':'native wirelength strictly lower and CPD <= baseline; otherwise retain baseline','timing_scope':'cold preparation, all seven projection+search+fork+atomic commit+score, actual selected native route; validations reported separately and full experiment wall also measured','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
for entry in list(inputs.values())+list(config['inputs'].values()):
    assert sha(entry['path'])==entry['sha256']
cold_start=time.monotonic();g=read_rr_graph(inputs['graph']['path']);frontend=PreparedEndpoints(inputs['net']['path'],inputs['graph']['path'],inputs['place']['path']);templates=PreparedTemplates(g,2);cache=CachedRegionalSearch(g);factory=lambda graph,margin:cache
initial=repair(g,e,templates.predict(e),search_type=factory);base=BatchOccupancy(g)
for r in initial['connections']:assert base.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
cold_wall=time.monotonic()-cold_start;old={r['connection_id']:r for r in initial['connections']};base_snapshot=(base.states,base.occupancy);rows=[{'candidate_id':0,**scores(g,e,initial['node_occupancy'])}];queries=[];validation_wall=0;branches={0:base}
for text,entry in placements_input.items():
    cid=int(text);start=time.monotonic();after,_=frontend.project(entry['path']);closure=affected(e,after);ids=set(closure['recompute_connection_ids']);dirty={**after,'connections':[r for r in after['connections'] if r['connection_id'] in ids]}
    candidate=templates.predict(dirty);partial=repair(g,dirty,candidate,search_type=factory);branch=base.fork()
    updates=[{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in partial['connections']]
    assert branch.update_batch(updates)==Result.COMMITTED
    occupancy={str(n):v for n,v in branch.occupancy.items() if v};quality=scores(g,after,occupancy);row={'candidate_id':cid,**quality};rows.append(row);branches[cid]=branch;query_wall=time.monotonic()-start
    check_start=time.monotonic();fresh=json.loads((parent/f'candidate_{cid}_prediction.json').read_text());merged=dict(old)
    for r in partial['connections']:merged[r['connection_id']]=r
    assert json.loads(json.dumps(merged))==json.loads(json.dumps({r['connection_id']:r for r in fresh['connections']}))
    assert occupancy==fresh['node_occupancy'];checked=audit(g,after,{**fresh,'connections':list(merged.values())});assert (base.states,base.occupancy)==base_snapshot;validation_wall+=time.monotonic()-check_start
    report={'candidate_id':cid,'recomputed':len(ids),'projection_search_fork_commit_score_wall_s':query_wall,'scores':quality,'independent_audit':checked,'baseline_unmodified':True};queries.append(report);print(json.dumps(report),flush=True)
selected=min(rows,key=lambda r:(r['channel_net_span_sum'],r['predicted_channel_overuse_units'],r['candidate_id']))['candidate_id']
decision={'protocol_sha256':sha(out/'protocol.json'),'selected_candidate':selected,'scores':rows,'scope':'known-candidate timing replay; decision saved before replicated selected native run'}
(out/'decision.json').write_text(json.dumps(decision,indent=2)+'\n');decision_sha=sha(out/'decision.json')
assert selected!=0 # Fixed control cohort's known selector; baseline otherwise needs no native rerun.
work=Path('work/prepared_loop_2026-10-04/selected');native=out/'selected_native';command=[sys.executable,str((out/'source/capture_routing_iterations.py').resolve())]
for k in ('vpr','arch','blif','net','graph'):command+=['--'+k,config['inputs'][k]['path']]
command+=['--place',placements_input[str(selected)]['path'],'--work-dir',str(work.resolve()),'--output-dir',str(native.resolve()),'--channel-width','200'];native_start=time.monotonic();process=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);native_wall=time.monotonic()-native_start;(out/'native_launcher.log').write_text(process.stdout)
if process.returncode:raise RuntimeError('selected native evaluation failed')
text=(native/'vpr_stdout.txt').read_text();baseline_log=(native_base/'vpr_stdout.txt').read_text();baseline_receipt=json.loads((native_base/'receipt.json').read_text());assert sha(native_base/'vpr_stdout.txt')==baseline_receipt['log_sha256']
def metrics(log):
    assert 'Completed placement consistency check successfully.' in log and 'Completed routing consistency check successfully.' in log
    return {'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',log)[1]),'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',log)[1])}
result=metrics(text);reference=metrics(baseline_log);assert placements(work/'diffeq.place',inputs['net']['sha256'])==placements(placements_input[str(selected)]['path'],inputs['net']['sha256']);accept=result['wirelength']<reference['wirelength'] and result['cpd_ns']<=reference['cpd_ns'];accepted=branches[selected] if accept else base
assert not accept and accepted is base and (base.states,base.occupancy)==base_snapshot # Expected known negative control.
assert sha(out/'decision.json')==decision_sha
for entry in placements_input.values():assert sha(entry['path'])==entry['sha256']
receipt={'protocol_sha256':sha(out/'protocol.json'),'decision_sha256':decision_sha,'cold_prepare_and_baseline_wall_s':cold_wall,'all_seven_warm_queries_wall_s':sum(r['projection_search_fork_commit_score_wall_s'] for r in queries),'validation_wall_s':validation_wall,'selected_native_launcher_wall_s':native_wall,'full_experiment_wall_s':time.monotonic()-run_start,'queries':queries,'selected_candidate':selected,'selected_native_metrics':result,'baseline_native_metrics':reference,'accept':accept,'accepted_candidate':selected if accept else 0,'baseline_epochs_paths_occupancy_preserved':True,'limitations':['known control replay','baseline native result reused','CPU only','exact postroute timing guard, no timing predictor','native selected replicate is fresh but baseline/all-candidate comparisons use archives']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='queries'}),flush=True)

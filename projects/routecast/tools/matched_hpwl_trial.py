"""Matched-HPWL candidate scores frozen before isolated native evaluations."""
from copy import deepcopy
import json,shutil,subprocess,sys,time,re
from pathlib import Path
from pre_route_endpoints import extract,placements,sha
from rr_graph import read_rr_graph
from connectivity_trial import construct
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch
from regional_search_cache import CachedRegionalSearch
from affected_connections import affected
from physical_prediction_audit import audit
from feedback_scores import scores
from prediction_metrics import spearman
from native_node_labels import node_labels

out=Path('experiments/matched_hpwl_trial_2026-10-04')
if out.exists():raise ValueError('fresh output required')
control=Path('experiments/matched_hpwl_candidates_2026-10-04');selection=json.loads((control/'receipt.json').read_text())['selected']
epath=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json');before=json.loads(epath.read_text());inputs=before['inputs'];net=Path(inputs['net']['path']);original_place=Path(inputs['place']['path']);graph=Path(inputs['graph']['path'])
prior=Path('experiments/native_iteration_capture_2026-10-04');native_config=json.loads((prior/'protocol.json').read_text())
old_candidate=Path('experiments/connectivity_trial_2026-10-04/refinement_2.json')
out.mkdir();(out/'source').mkdir();modules=['matched_hpwl_trial.py','pre_route_endpoints.py','rr_graph.py','connectivity_trial.py','hybrid_repair.py','lazy_region_search.py','regional_search_cache.py','affected_connections.py','physical_prediction_audit.py','feedback_scores.py','prediction_metrics.py','native_node_labels.py','capture_routing_iterations.py','rr_occupancy.py','connection_golden.py','template_connectivity.py','template_sketch.py','pin_pools.py','pin_template_trial.py','semantic_sketch.py','run_sketch.py']
for name in modules:shutil.copyfile(Path(__file__).with_name(name),out/'source'/name)
protocol={'scope':'development matched-HPWL controls, pre-route scores frozen before new native outcomes; no unseen-family claim','inputs':{**inputs,'endpoints':{'path':str(epath.resolve()),'sha256':sha(epath)},'old_candidate':{'path':str(old_candidate.resolve()),'sha256':sha(old_candidate)},'selection':{'path':str((control/'receipt.json').resolve()),'sha256':sha(control/'receipt.json')}},'native_inputs':native_config['inputs'],'baseline_native_receipt_sha256':sha(prior/'receipt.json'),'selected_pairs':selection,'refinement_rounds':2,'margin':1,'cache_groups':128,'decision_rule':'minimum channel_net_span_sum, then predicted_channel_overuse_units, then candidate ID; baseline ID 0','geometry_control':'every candidate total net bbox HPWL equals baseline 4302','native_router':'unchanged seed1 cw200 max50 worker1','source_sha256':{n:sha(out/'source'/n) for n in modules},'timing_scope':'record conversion+partial prediction separately from full-rebuild validation and native routing; no hardware claim'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
for v in list(protocol['inputs'].values())+list(protocol['native_inputs'].values()):
    if sha(v['path'])!=v['sha256']:raise ValueError('input changed')
g=read_rr_graph(graph);slots=placements(original_place,sha(net));cache=CachedRegionalSearch(g);factory=lambda graph,margin:cache
initial=repair(g,before,json.loads(old_candidate.read_text()),search_type=factory);oldrows={r['connection_id']:r for r in initial['connections']};baseline_scores=scores(g,before,initial['node_occupancy']);assert baseline_scores['net_bbox_hpwl']==4302
rows=[{'candidate_id':0,'pair':None,**baseline_scores}];predicted_wall_total=0
for cid,entry in enumerate(selection,1):
    start=time.monotonic();pair=entry['pair'];changed_slots=dict(slots);a,b=pair;changed_slots[a]=(*slots[b][:4],slots[a][4]);changed_slots[b]=(*slots[a][:4],slots[b][4])
    moved=out/f'candidate_{cid}.place';lines=[]
    for line in original_place.read_text().splitlines():
        fields=line.split()
        if fields and fields[0] in pair:
            x,y,z,layer,bid=changed_slots[fields[0]];line=f'{fields[0]}\t{x}\t{y}\t{z}\t{layer}\t#{bid}'
        lines.append(line)
    moved.write_text('\n'.join(lines)+'\n');after,_=extract(net,moved,graph);closure=affected(before,after);ids=set(closure['recompute_connection_ids']);dirty={**after,'connections':[r for r in after['connections'] if r['connection_id'] in ids]}
    candidate=construct(g,dirty,2);partial=repair(g,dirty,candidate,search_type=factory)
    merged=dict(oldrows)
    for r in partial['connections']:merged[r['connection_id']]=r
    # Reconstruct occupancy directly from physical arcs, independent of ledger.
    users={}
    for r in merged.values():
        nodes={r['source']}|{g.edges[eid].sink for eid in r['physical_edge_ids']}
        for n in nodes:users.setdefault(n,set()).add(r['net_id'])
    occupancy={str(n):len(v) for n,v in users.items()};metrics=scores(g,after,occupancy);assert metrics['net_bbox_hpwl']==4302
    cost=time.monotonic()-start;predicted_wall_total+=cost
    fresh_candidate=construct(g,after,2);fresh=repair(g,after,fresh_candidate,search_type=LazyRegionalSearch)
    assert json.loads(json.dumps(merged))==json.loads(json.dumps({r['connection_id']:r for r in fresh['connections']}))
    assert occupancy==fresh['node_occupancy'];checked=audit(g,after,{**fresh,'connections':list(merged.values())})
    row={'candidate_id':cid,'pair':pair,**metrics,'recomputed':len(ids),'conversion_and_partial_prediction_wall_s':cost,'partial_candidate_work':candidate['work'],'partial_repair_work':partial['repair_work'],'independent_audit':checked}
    rows.append(row)
    for name,data in [('endpoints',after),('prediction',fresh),('scores',row)]:
        (out/f'candidate_{cid}_{name}.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'stage':'prediction',**row}),flush=True)
selected=min(rows,key=lambda r:(r['channel_net_span_sum'],r['predicted_channel_overuse_units'],r['candidate_id']))['candidate_id']
decision={'rows':rows,'selected_candidate':selected,'protocol_sha256':sha(out/'protocol.json'),'prediction_conversion_wall_s':predicted_wall_total,'scope':'all candidate scores and decision frozen before new native routing'}
(out/'decision.json').write_text(json.dumps(decision,indent=2)+'\n');decision_sha=sha(out/'decision.json')
# Native routing begins only after decision artifact exists.
native=[]
baseline_log=(prior/'vpr_stdout.txt').read_text();baseline_receipt=json.loads((prior/'receipt.json').read_text());assert sha(prior/'vpr_stdout.txt')==baseline_receipt['log_sha256']
def parse(text):
    if 'Completed routing consistency check successfully.' not in text or 'Completed placement consistency check successfully.' not in text:raise ValueError('native consistency gate failed')
    result={}
    for k,pattern in [('wirelength',r'Total wirelength:\s*(\d+)'),('iterations',r'Successfully routed after (\d+) routing iterations'),('cpd_ns',r'Final critical path delay \(least slack\):\s*([0-9.]+) ns')]:
        m=re.search(pattern,text)
        if m is None:raise ValueError('missing native result')
        result[k]=float(m[1]) if k=='cpd_ns' else int(m[1])
    return result
native.append({'candidate_id':0,**parse(baseline_log),'wall_s':baseline_receipt['wall_s'],'reused_baseline':True})
for cid in range(1,len(selection)+1):
    work=Path(f'work/matched_hpwl_trial_2026-10-04/candidate_{cid}');run=out/f'native_{cid}';command=[sys.executable,str((out/'source/capture_routing_iterations.py').resolve())]
    for k in ('vpr','arch','blif','net','graph'):command+=['--'+k,native_config['inputs'][k]['path']]
    command+=['--place',str((out/f'candidate_{cid}.place').resolve()),'--work-dir',str(work.resolve()),'--output-dir',str(run.resolve()),'--channel-width','200']
    process=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(out/f'native_{cid}_launcher.log').write_text(process.stdout)
    if process.returncode:raise RuntimeError('native capture failed')
    receipt=json.loads((run/'receipt.json').read_text());normalized=work/'diffeq.place';input_place=out/f'candidate_{cid}.place'
    assert placements(normalized,sha(net))==placements(input_place,sha(net))
    labels=node_labels(g,receipt['final_route']['path'],sha(normalized));assert all(v<=g.nodes[int(n)].capacity for n,v in labels.items())
    result={'candidate_id':cid,**parse((run/'vpr_stdout.txt').read_text()),'wall_s':receipt['wall_s'],'input_placement_sha256':sha(input_place),'normalized_placement_sha256':sha(normalized),'coordinates_preserved':True,'native_final_overflow_nodes':0}
    native.append(result);print(json.dumps({'stage':'native',**result}),flush=True)
assert sha(out/'decision.json')==decision_sha
native_by_id={r['candidate_id']:r for r in native};analysis={}
for score in ('channel_net_span_sum','predicted_channel_overuse_units'):
    analysis[score]={'native_wirelength_spearman':spearman([r[score] for r in rows],[native_by_id[r['candidate_id']]['wirelength'] for r in rows])}
result={'protocol_sha256':sha(out/'protocol.json'),'decision_sha256':decision_sha,'selected_candidate':selected,'native_results':native,'analysis':analysis,'selected_wirelength_delta_vs_baseline':native_by_id[selected]['wirelength']-native_by_id[0]['wirelength'],'selected_cpd_delta_ns_vs_baseline':native_by_id[selected]['cpd_ns']-native_by_id[0]['cpd_ns'],'prediction_conversion_wall_s':predicted_wall_total,'native_all_candidates_wall_s':sum(r['wall_s'] for r in native),'limitations':['single design','eight total candidates including baseline','no criticality model','prediction timing excludes shared initialization and full equivalence auditing','routing all candidates is an evaluation oracle, not the feedback production cost']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'stage':'complete',**result}),flush=True)

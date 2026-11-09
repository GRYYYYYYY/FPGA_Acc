"""Isolated native routing reference for preselected placement swaps, no feedback."""
import json,re,shutil,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha,placements as read_placement
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from pin_template_trial import spatial
from prediction_metrics import compare

out=Path('experiments/native_swap_validation_normalized_v2_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir(parents=True);(out/'source').mkdir()
for n in ('native_swap_validation.py','capture_routing_iterations.py','native_node_labels.py','rr_graph.py','pre_route_endpoints.py','pin_template_trial.py','prediction_metrics.py','pin_pools.py','template_sketch.py','connection_golden.py','rr_occupancy.py','semantic_sketch.py'):
    shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
base=Path('experiments/multi_swap_2026-10-04');prior=Path('experiments/native_iteration_capture_2026-10-04');config=json.loads((prior/'protocol.json').read_text());inputs={k:config['inputs'][k] for k in ('vpr','arch','blif','net','graph')}
for entry in inputs.values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
placements={str(step):{'path':str((base/f'step_{step}.place').resolve()),'sha256':sha(base/f'step_{step}.place')} for step in range(1,5)}
p={'scope':'native fixed-router reference on preselected random swaps; no sketch influence on move selection','inputs':inputs,'placements':placements,'parent_swap_protocol_sha256':sha(base/'protocol.json'),'baseline_protocol_sha256':sha(prior/'protocol.json'),'source_sha256':{x.name:sha(x) for x in (out/'source').glob('*.py')},'seed':1,'channel_width':200,'max_iterations':50,'num_workers':1,'per_run_timeout_s':300}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');g=read_rr_graph(inputs['graph']['path']);summaries=[]
def metrics(text):
    markers=['Completed placement consistency check successfully.','Completed routing consistency check successfully.','Circuit successfully routed with a channel width factor of 200.']
    result={'placement_consistency_passed':markers[0] in text,'routing_consistency_passed':markers[1] in text,'routing_succeeded':markers[2] in text}
    for name,pattern in [('iterations',r'Successfully routed after (\d+) routing iterations'),('wirelength',r'Total wirelength:\s*(\d+)'),('cpd_ns',r'Final critical path delay \(least slack\):\s*([0-9.]+) ns')]:
        m=re.search(pattern,text);result[name]=float(m[1]) if m and name=='cpd_ns' else (int(m[1]) if m else None)
    return result
baseline=metrics((prior/'vpr_stdout.txt').read_text())
for step,place in placements.items():
    command=[sys.executable,str((out/'source/capture_routing_iterations.py').resolve())]
    for k,v in inputs.items():command+=['--'+k,v['path']]
    command+=['--place',place['path'],'--work-dir',str(Path(f'work/native_swap_validation_normalized_v2_2026-10-04/step_{step}').resolve()),'--output-dir',str((out/f'step_{step}').resolve()),'--channel-width','200']
    if step=='1':
        run=Path('experiments/native_swap_validation_2026-10-04/step_1')
        original=json.loads((run/'protocol.json').read_text())
        for k,v in inputs.items():
            if original['inputs'][k]!=v:raise ValueError('reused native input changed')
        if original['inputs']['place']!=place:raise ValueError('reused native placement differs')
        receipt=json.loads((run/'receipt.json').read_text())
        if receipt['protocol_sha256']!=sha(run/'protocol.json') or receipt['log_sha256']!=sha(run/'vpr_stdout.txt') or receipt['final_route']['sha256']!=sha(receipt['final_route']['path']):raise ValueError('reused native artifacts changed')
    else:
        process=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (out/f'step_{step}_launcher.log').write_text(process.stdout)
        if process.returncode:raise RuntimeError(f'native step {step} failed; inspect archived log')
        run=out/f'step_{step}';receipt=json.loads((run/'receipt.json').read_text())
    text=(run/'vpr_stdout.txt').read_text();observed=metrics(text)
    normalized=Path(json.loads((run/'protocol.json').read_text())['cwd'])/'diffeq.place'
    if read_placement(normalized,inputs['net']['sha256'])!=read_placement(place['path'],inputs['net']['sha256']):raise ValueError('native placement coordinates changed')
    normalized_sha=sha(normalized)
    if not all(observed[k] for k in ('placement_consistency_passed','routing_consistency_passed','routing_succeeded')):raise ValueError('native completion gate failed')
    final=node_labels(g,receipt['final_route']['path'],normalized_sha)
    if any(v>g.nodes[int(n)].capacity for n,v in final.items()):raise ValueError('native final overflow')
    fresh=json.loads((base/f'step_{step}_fresh.json').read_text());quality=compare(spatial(g,fresh['node_occupancy']),spatial(g,final),20)
    counts=[]
    for entry in receipt['iteration_files']:
        values=node_labels(g,entry['path'],normalized_sha);counts.append(sum(v>g.nodes[int(n)].capacity for n,v in values.items()))
    summary={'step':int(step),'input_placement_sha256':place['sha256'],'normalized_placement_sha256':normalized_sha,'placement_coordinates_preserved':True,'reused_native_capture':step=='1',**observed,'wall_s':receipt['wall_s'],'native_iteration_overuse_nodes':counts,'predictor_spatial_vs_native_final':quality,'baseline_wirelength':baseline['wirelength'],'baseline_cpd_ns':baseline['cpd_ns'],'scope':'random placement perturbation reference; not estimator-directed improvement'}
    summaries.append(summary);(out/f'step_{step}_native_final_labels.json').write_text(json.dumps({'graph_sha256':g.sha256,'placement_sha256':normalized_sha,'route_sha256':receipt['final_route']['sha256'],'node_occupancy':final},indent=2)+'\n');print(json.dumps(summary),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'baseline':baseline,'summary':summaries,'all_native_checks_passed':True},indent=2)+'\n')

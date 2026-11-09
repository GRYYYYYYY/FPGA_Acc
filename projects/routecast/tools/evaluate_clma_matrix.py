"""Hash-bound unified audit/evaluation of completed clma variants."""
import json,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from native_node_labels import node_labels
from physical_prediction_audit import audit
from pin_template_trial import spatial
from prediction_metrics import compare

out=Path('experiments/clma_matrix_evaluation_2026-10-04')
if out.exists():raise ValueError('fresh output required')
parent=Path('experiments/clma_cross_design_2026-10-04');resume=Path('experiments/clma_cross_design_continuation_2026-10-04');pp=json.loads((parent/'protocol.json').read_text());rp=json.loads((resume/'protocol.json').read_text());rr=json.loads((resume/'receipt.json').read_text())
if rr['protocol_sha256']!=sha(resume/'protocol.json') or rp['parent_protocol_sha256']!=sha(parent/'protocol.json'):raise ValueError('parent/continuation protocol changed')
for name,digest in rr['artifacts'].items():
    if sha(resume/name)!=digest:raise ValueError('continuation artifact changed')
for entry in rp['reused_completed_artifacts'].values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('parent artifact changed')
paths={'graph':Path(pp['inputs']['graph']['path']),'endpoints':Path(pp['inputs']['endpoints']['path']),'route':Path('../persistroute/experiments/vpr9/clma_seed1/clma.route'),'labels':parent/'native_final_labels.json','raw':parent/'raw.json'}
for name,root in [('0',parent),('1',parent),('2',resume),('fixed',resume)]:
    paths[f'candidate_{name}']=root/f'candidate_{name}.json';paths[f'hybrid_{name}']=root/f'hybrid_{name}.json'
out.mkdir();(out/'source').mkdir()
# Complete local dependency closure, including transitive imports, is archived.
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'scope':'single additional clma design/seed, full frozen-cohort audit and final-occupancy comparison; no family holdout or feedback/hardware claim','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'parent_protocol_sha256':sha(parent/'protocol.json'),'continuation_receipt_sha256':sha(resume/'receipt.json'),'spatial_k':20,'resource_k':'5 percent floor minimum1','tie_rule':'descending value then ascending resource ID','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
g=read_rr_graph(paths['graph']);ep=json.loads(paths['endpoints'].read_text());labels=json.loads(paths['labels'].read_text())
truth=node_labels(g,paths['route'],ep['inputs']['place']['sha256'])
if labels['graph_sha256']!=g.sha256 or labels['route_sha256']!=sha(paths['route']) or truth!=labels['node_occupancy']:raise ValueError('independent native label mismatch')
resources=[n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and node.capacity];target_spatial=spatial(g,truth);target_resource={str(n):truth.get(str(n),0)/g.nodes[n].capacity for n in resources}
expected=Counter(tuple(r[k] for k in ('connection_id','net_id','source','sink')) for r in ep['connections']);reports={}
for name in ('raw','0','1','2','fixed'):
    pred=json.loads(paths['raw' if name=='raw' else 'hybrid_'+name].read_text());values=pred['node_occupancy']
    report={'spatial':compare(spatial(g,values),target_spatial,20),'resource':compare({str(n):values.get(str(n),0)/g.nodes[n].capacity for n in resources},target_resource,max(1,len(resources)//20))}
    if name=='raw':
        if pred['graph_sha256']!=g.sha256 or pred['connections_requested']!=len(ep['connections']):raise ValueError('raw identity/cohort mismatch')
        report.update(completed=pred['connections_completed'],search_edge_visits=sum(r['edge_visits'] for r in pred['search_traces']),reported_search_commit_wall_s=pred['search_and_commit_wall_s'],scope='occupancy-only baseline artifact; no physical path list to replay')
    else:
        c=json.loads(paths['candidate_'+name].read_text());cohort=Counter(tuple(r[k] for k in ('connection_id','net_id','source','sink')) for r in c['connections'])
        if cohort!=expected or c['physical_graph_sha256']!=g.sha256:raise ValueError('candidate cohort/graph mismatch')
        checked=audit(g,ep,pred,c)
        work={**pred['repair_work'],'candidate_search_edge_visits':c['work']['edge_visits'],'candidate_witness_edge_visits':c['work']['witness_edge_visits']}
        report.update(completed=pred['completed'],methods=pred['methods'],nodes=c['nodes'],edges=c['edges'],performed_rounds=c['performed_rounds'],stable_partition=c['stable_partition'],work=work,independent_path_audit=checked)
    reports[name]=report;print(json.dumps({'variant':name,**report}),flush=True)
for entry in protocol['inputs'].values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed during evaluation')
receipt={'protocol_sha256':sha(out/'protocol.json'),'reports':reports,'all_four_template_physical_audits_passed':True,'native_labels_independently_replayed':True,'scope':protocol['scope']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

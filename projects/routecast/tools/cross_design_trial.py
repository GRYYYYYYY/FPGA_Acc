"""Frozen graph/endpoints-only cross-design predictor ablation."""
import argparse,hashlib,json,shutil,time,datetime
from pathlib import Path
from rr_graph import read_rr_graph
from run_sketch import predict
from connectivity_trial import construct
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def freeze(out):
    if out.exists():raise ValueError('fresh directory required')
    out.mkdir(parents=True);(out/'source').mkdir()
    files=['cross_design_trial.py','rr_graph.py','run_sketch.py','semantic_sketch.py','rr_occupancy.py','connection_golden.py','connectivity_trial.py','pin_template_trial.py','pin_pools.py','prediction_metrics.py','template_sketch.py','template_connectivity.py','hybrid_repair.py','lazy_region_search.py']
    for n in files:shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
    inputs={'graph':Path('../persistroute/experiments/vpr9/clma_seed1/rr_graph.xml'),'endpoints':Path('experiments/clma_constant_policy_2026-10-04/endpoints.json')}
    p={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'clma cross-design transfer; diffeq development parameters unchanged; not broad heldout-family validation','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in inputs.items()},'source_sha256':{n:sha(out/'source'/n) for n in files},'variants':[0,1,2,None],'cost':'rr_length_switch','budget':'all graph nodes','repair_margin':1,'repair_policy':'lazy regional then full fallback','label_policy':'no labels available to predictor','timeout_seconds':1800,'primary':['complete cohort path coverage','repair method counts','search edge visits'],'limitations':['single additional design/seed','no joint capacity routing','no hardware speed claim','CPU wall includes graph/refinement/repair but no evaluation or end-to-end placement feedback']}
    (out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')


def run(out):
    p=json.loads((out/'protocol.json').read_text())
    for n,h in p['source_sha256'].items():
        if sha(Path(__file__).with_name(n))!=h:raise ValueError('source changed')
    for v in p['inputs'].values():
        if sha(v['path'])!=v['sha256']:raise ValueError('input changed')
    start=time.monotonic();g=read_rr_graph(p['inputs']['graph']['path']);e=json.loads(Path(p['inputs']['endpoints']['path']).read_text())
    load=time.monotonic()-start;summary=[]
    start=time.monotonic();baseline=predict(g,e,'rr_length_switch',len(g.nodes));baseline['graph_load_wall_s']=load
    (out/'raw.json').write_text(json.dumps(baseline,indent=2)+'\n');print(json.dumps({'variant':'raw','completed':baseline['connections_completed'],'wall_s':time.monotonic()-start}),flush=True)
    for rounds in p['variants']:
        name='fixed' if rounds is None else str(rounds);start=time.monotonic()
        candidate=construct(g,e,rounds);built=time.monotonic()-start
        (out/f'candidate_{name}.json').write_text(json.dumps(candidate,indent=2)+'\n')
        hybrid=repair(g,e,candidate,p['repair_margin'],search_type=LazyRegionalSearch)
        hybrid['candidate_construct_wall_s']=built;hybrid['construct_and_repair_wall_s']=time.monotonic()-start
        (out/f'hybrid_{name}.json').write_text(json.dumps(hybrid,indent=2)+'\n')
        row={'variant':name,'nodes':candidate['nodes'],'edges':candidate['edges'],'lifted':candidate['lifted_connections'],'completed':hybrid['completed'],'requested':hybrid['requested'],'methods':hybrid['methods'],'candidate_work':candidate['work'],'repair_work':hybrid['repair_work'],'construct_and_repair_wall_s':hybrid['construct_and_repair_wall_s']}
        summary.append(row);print(json.dumps(row),flush=True)
    (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'summary':summary,'artifacts':{x.name:sha(x) for x in out.glob('*.json') if x.name not in {'protocol.json','receipt.json'}}},indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.output_dir)
    else:run(a.output_dir)

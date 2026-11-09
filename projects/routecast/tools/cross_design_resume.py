"""Continuation after authoritative parent timeout, preserving completed variants."""
import argparse,json,shutil,time,signal
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from connectivity_trial import construct
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch
from physical_prediction_audit import audit

p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');a=p.parse_args()
parent=Path('experiments/clma_cross_design_2026-10-04');out=Path('experiments/clma_cross_design_continuation_2026-10-04')
if a.freeze:
    if out.exists():raise ValueError('fresh output required')
    prior=json.loads((parent/'protocol.json').read_text());out.mkdir(parents=True);(out/'source').mkdir()
    # Preserve exact predictor implementation from the original frozen run.
    for file in (parent/'source').glob('*.py'):shutil.copyfile(file,out/'source'/file.name)
    for name in ('cross_design_resume.py','pre_route_endpoints.py','physical_prediction_audit.py'):
        shutil.copyfile(Path(__file__).with_name(name),out/'source'/name)
    reused={}
    for name in ('raw.json','candidate_0.json','hybrid_0.json','candidate_1.json','hybrid_1.json'):
        reused[name]={'path':str((parent/name).resolve()),'sha256':sha(parent/name)}
    candidate=parent/'candidate_2.json'
    candidate_entry={'path':str(candidate.resolve()),'sha256':sha(candidate)} if candidate.exists() else None
    proto={'parent_protocol_sha256':sha(parent/'protocol.json'),'inputs':prior['inputs'],'reused_completed_artifacts':reused,'reused_two_round_candidate':candidate_entry,'variants':[2,None],'cost':prior['cost'],'repair_margin':prior['repair_margin'],'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'scope':'parent ended at frozen whole-run time limit; compute only unfinished variants','timeout_policy':'1800 seconds per continuation variant process; independent parent timeout retained'}
    (out/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n');raise SystemExit(0)
proto=json.loads((out/'protocol.json').read_text())
for n,h in proto['source_sha256'].items():
    if sha(Path(__file__).with_name(n))!=h:raise ValueError('source changed')
for entry in list(proto['inputs'].values())+list(proto['reused_completed_artifacts'].values()):
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
g=read_rr_graph(proto['inputs']['graph']['path']);e=json.loads(Path(proto['inputs']['endpoints']['path']).read_text());summaries=[]
def timeout_handler(signum,frame):raise TimeoutError('continuation variant exceeded 1800 seconds')
signal.signal(signal.SIGALRM,timeout_handler)
for rounds in proto['variants']:
    signal.alarm(1800)
    name='fixed' if rounds is None else str(rounds);start=time.monotonic()
    reuse=proto['reused_two_round_candidate'] if rounds==2 else None
    if reuse:
        if sha(reuse['path'])!=reuse['sha256']:raise ValueError('candidate changed')
        candidate=json.loads(Path(reuse['path']).read_text())
    else:candidate=construct(g,e,rounds)
    (out/f'candidate_{name}.json').write_text(json.dumps(candidate,indent=2)+'\n')
    hybrid=repair(g,e,candidate,proto['repair_margin'],search_type=LazyRegionalSearch)
    checked=audit(g,e,hybrid,candidate)
    (out/f'hybrid_{name}.json').write_text(json.dumps(hybrid,indent=2)+'\n')
    row={'variant':name,'requested':hybrid['requested'],'completed':hybrid['completed'],'nodes':candidate['nodes'],'edges':candidate['edges'],'methods':hybrid['methods'],'candidate_work':candidate['work'],'repair_work':hybrid['repair_work'],'continuation_wall_s':time.monotonic()-start,'candidate_reused':reuse is not None,'independent_audit':checked}
    (out/f'summary_{name}.json').write_text(json.dumps(row,indent=2)+'\n');summaries.append(row);print(json.dumps(row),flush=True)
signal.alarm(0)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'summary':summaries,'all_path_audits_passed':True,'artifacts':{f.name:sha(f) for f in out.glob('*.json') if f.name!='protocol.json'}},indent=2)+'\n')

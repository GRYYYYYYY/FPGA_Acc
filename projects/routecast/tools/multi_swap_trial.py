"""Preselected cumulative placement swaps, exact full-rebuild comparisons."""
from collections import Counter
from copy import deepcopy
import json,random,re,shutil,time
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import extract,placements,physical_maps,sha
from rr_graph import read_rr_graph
from connectivity_trial import construct
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch
from regional_search_cache import CachedRegionalSearch
from affected_connections import affected
from rr_batch_occupancy import BatchOccupancy
from physical_prediction_audit import audit
from connection_golden import Result

out=Path('experiments/multi_swap_2026-10-04')
if out.exists():raise ValueError('fresh output required')
before_path=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json');before=json.loads(before_path.read_text());inputs=before['inputs']
for entry in inputs.values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
net=Path(inputs['net']['path']);place=Path(inputs['place']['path']);graph=Path(inputs['graph']['path'])
slots=placements(place,sha(net));types,grid,_=physical_maps(graph);groups={}
for block in ET.parse(net).getroot().findall('block'):
    name=block.attrib['name'];logical=re.sub(r'\[\d+\]$','',block.attrib['instance'])
    if logical!='clb':continue
    x,y,z,layer,_=slots[name];signature=(logical,z,layer,grid[(x,y,layer)][0]);groups.setdefault(signature,[]).append(name)
names=next(v for v in groups.values() if len(v)>=8);rng=random.Random(20261004);rng.shuffle(names);pairs=[names[i:i+2] for i in range(0,8,2)]
out.mkdir(parents=True);(out/'source').mkdir()
modules=['multi_swap_trial.py','pre_route_endpoints.py','rr_graph.py','connectivity_trial.py','hybrid_repair.py','lazy_region_search.py','regional_search_cache.py','affected_connections.py','rr_batch_occupancy.py','physical_prediction_audit.py','rr_occupancy.py','connection_golden.py','template_connectivity.py','template_sketch.py','pin_pools.py','pin_template_trial.py','prediction_metrics.py','semantic_sketch.py','run_sketch.py']
for n in modules:shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
old_candidate=Path('experiments/connectivity_trial_2026-10-04/refinement_2.json')
protocol={'inputs':{**inputs,'old_endpoints':{'path':str(before_path.resolve()),'sha256':sha(before_path)},'old_candidate':{'path':str(old_candidate.resolve()),'sha256':sha(old_candidate)}},'pairs':pairs,'seed':20261004,'selection':'first compatible CLB signature group, shuffled before any result','refinement_rounds':2,'margin':1,'cache_groups':128,'scope':'four cumulative two-CLB swaps, no metric-based selection or native feedback claim','source_sha256':{n:sha(out/'source'/n) for n in modules}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
g=read_rr_graph(graph);cache=CachedRegionalSearch(g);factory=lambda graph,margin:cache
current=repair(g,before,json.loads(old_candidate.read_text()),search_type=factory);ledger=BatchOccupancy(g);epochs={}
for r in current['connections']:
    cid=r['connection_id'];epochs[cid]=1
    assert ledger.update(cid,1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
summaries=[]
for step,pair in enumerate(pairs,1):
    a,b=pair;sa,sb=slots[a],slots[b];slots[a]=(*sb[:4],sa[4]);slots[b]=(*sa[:4],sb[4])
    moved=out/f'step_{step}.place';lines=[]
    for line in place.read_text().splitlines():
        fields=line.split()
        if fields and fields[0] in slots:
            x,y,z,layer,bid=slots[fields[0]];line=f'{fields[0]}\t{x}\t{y}\t{z}\t{layer}\t#{bid}'
        lines.append(line)
    moved.write_text('\n'.join(lines)+'\n');after,_=extract(net,moved,graph);closure=affected(before,after)
    ids=set(closure['recompute_connection_ids']);dirty={**after,'connections':[r for r in after['connections'] if r['connection_id'] in ids]}
    hits,misses=cache.hits,cache.misses;start=time.monotonic();candidate=construct(g,dirty,2);partial=repair(g,dirty,candidate,search_type=factory);partial_wall=time.monotonic()-start
    updates=[]
    for r in partial['connections']:
        cid=r['connection_id'];updates.append({**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':epochs[cid]+1,'edge_ids':r['physical_edge_ids']})
    state_before=(ledger.states,ledger.occupancy)
    invalid=deepcopy(updates);invalid[-1]['edge_ids']=[-1]
    assert ledger.update_batch(invalid)==Result.INVALID
    assert (ledger.states,ledger.occupancy)==state_before
    assert ledger.update_batch(updates)==Result.COMMITTED
    for r in updates:epochs[r['connection_id']]=r['epoch']
    start=time.monotonic();fresh_candidate=construct(g,after,2);fresh=repair(g,after,fresh_candidate,search_type=LazyRegionalSearch);full_wall=time.monotonic()-start
    merged={r['connection_id']:r for r in current['connections']}
    for r in partial['connections']:merged[r['connection_id']]=r
    fullrows={r['connection_id']:r for r in fresh['connections']}
    assert json.loads(json.dumps(merged))==json.loads(json.dumps(fullrows))
    assert {str(n):v for n,v in ledger.occupancy.items() if v}==fresh['node_occupancy']
    checked=audit(g,after,{**fresh,'connections':list(merged.values())})
    summary={'step':step,'pair':pair,'changed_endpoints':len(closure['changed_connection_ids']),'recomputed':len(ids),'requested':len(after['connections']),'methods':fresh['methods'],'cache_hits':cache.hits-hits,'cache_misses':cache.misses-misses,'partial_candidate_work':candidate['work'],'partial_repair_work':partial['repair_work'],'full_candidate_work':fresh_candidate['work'],'full_repair_work':fresh['repair_work'],'partial_wall_s':partial_wall,'full_wall_s':full_wall,'invalid_batch_preserved_old_state':True,'exact_full_rebuild_equivalence':True,'independent_audit':checked}
    for n,obj in [('endpoints',after),('closure',closure),('partial',partial),('fresh',fresh),('summary',summary)]:
        (out/f'step_{step}_{n}.json').write_text(json.dumps(obj,indent=2)+'\n')
    summaries.append(summary);print(json.dumps(summary),flush=True);before=after;current={**fresh,'connections':list(merged.values())}
receipt={'protocol_sha256':sha(out/'protocol.json'),'summary':summaries,'all_checks_passed':True,'artifacts':{p.name:sha(p) for p in out.glob('*.json') if p.name!='protocol.json'},'limitations':['single diffeq graph/seed','four preselected moves','full index reconstruction','timing excludes endpoint conversion and batch commit','no native routing quality or hardware result']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

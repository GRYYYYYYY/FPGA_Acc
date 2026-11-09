"""Paired exact-search microbenchmark; not end-to-end speedup."""
from collections import defaultdict
import json,shutil,time,statistics
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from semantic_sketch import Sketch
from indexed_sketch import IndexedSketch
out=Path('experiments/indexed_search_fanout_2026-10-04')
if out.exists():raise ValueError('fresh output required')
endpoints={'diffeq':Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json'),'elliptic':Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json')}
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'scope':'paired physical-graph search microbenchmark; no full pipeline or hardware speedup','cohort':'first8 SOURCE groups sorted by descending distinct sink count then sourceID; all sinks in those groups','rounds':3,'order':'alternate original/indexed each round','cost':'rr_length_switch','budget':'all nodes','inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in endpoints.items()},'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[]
for design,path in endpoints.items():
    e=json.loads(path.read_text());g=read_rr_graph(e['inputs']['graph']['path']);assert g.sha256==e['graph_sha256'];groups=defaultdict(set)
    for r in e['connections']:groups[r['source']].add(r['sink'])
    cohort=sorted(groups.items(),key=lambda row:(-len(row[1]),row[0]))[:8];engines={};prep={}
    for name,cls in [('original',Sketch),('indexed',IndexedSketch)]:
        start=time.monotonic();engines[name]=cls(g,'rr_length_switch',len(g.nodes));prep[name]=time.monotonic()-start
    timings=defaultdict(list);reference=None
    for round_id in range(3):
        for name in (['original','indexed'] if round_id%2==0 else ['indexed','original']):
            start=time.monotonic();values=[engines[name].search(s,t) for s,t in cohort];timings[name].append(time.monotonic()-start)
            if reference is None:reference=values
            assert values==reference
    row={'design':design,'graph_sha256':g.sha256,'source_ids':[s for s,t in cohort],'sink_classes':sum(len(t) for s,t in cohort),'preparation_wall_s':prep,'search_wall_s':dict(timings),'median_search_wall_s':{k:statistics.median(v) for k,v in timings.items()},'exact_paths_and_counters_equal':True,'settled_nodes':sum(v.settled_nodes for v in reference),'edge_visits':sum(v.edge_visits for v in reference)};rows.append(row);print(json.dumps(row),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows},indent=2)+'\n')

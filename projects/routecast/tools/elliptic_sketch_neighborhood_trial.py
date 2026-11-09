"""Development neighborhood size/cost trial; no native-route reads."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_endpoints import PreparedEndpoints
from prepared_templates import PreparedTemplates
from compact_indexed_sketch import CompactIndexedSketch
from regional_search_cache import CachedRegionalSearch
from hybrid_repair import repair
from sketch_resource_neighborhood import resource_neighborhood
out=Path('experiments/elliptic_sketch_neighborhood_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
epath=Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json');e=json.loads(epath.read_text());place=Path('experiments/elliptic_local_candidates_2026-10-05/candidate_6.place');ppath=Path('experiments/elliptic_prospective_feedback_2026-10-05/candidate_6_prediction.json')
inputs={str(epath):sha(epath),str(place):sha(place),str(ppath):sha(ppath),**{v['path']:v['sha256'] for v in e['inputs'].values()}}
assert all(sha(p)==h for p,h in inputs.items())
(out/'protocol.json').write_text(json.dumps({'inputs_sha256':inputs,'hops':[0,1,2],'scope':'development size/cost experiment on previously explored candidate6; no native input, no policy retuning','sources_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}},indent=2)+'\n')
t=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);frontend=PreparedEndpoints(e['inputs']['net']['path'],e['inputs']['graph']['path'],e['inputs']['place']['path']);after,_=frontend.project(place);templates=PreparedTemplates(g,2,search_type=CompactIndexedSketch);cache=CachedRegionalSearch(g);baseline=repair(g,e,templates.predict(e),search_type=lambda graph,margin:cache);prep=time.monotonic()-t
(out/'baseline_prediction.json').write_text(json.dumps(baseline)+'\n');candidate=json.loads(ppath.read_text());reports=[]
for hops in (0,1,2):
 t=time.monotonic();r=resource_neighborhood(g,e,after,baseline,candidate,hops=hops);r['construction_and_physical_audit_wall_s']=time.monotonic()-t
 (out/f'closure_{hops}.json').write_text(json.dumps(r,indent=2)+'\n');reports.append({'hops':hops,'nets':len(r['expanded_net_ids']),'connections':len(r['recompute_connection_ids']),'wall_s':r['construction_and_physical_audit_wall_s']})
assert all(sha(p)==h for p,h in inputs.items())
receipt={'preparation_wall_s':prep,'reports':reports,'input_hashes_unchanged':True,'limitations':['closure sizing only; expanded reroute/search cost and quality not measured','no unseen-family or acceleration claim']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

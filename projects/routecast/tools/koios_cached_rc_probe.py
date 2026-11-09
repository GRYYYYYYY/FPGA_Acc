"""Cold Koios full-model build and pre-frozen maximum-fanout group probe."""
import json,time,shutil,os
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from cached_bound_rc import CachedBoundRC
from path_rc import PathRC,State
from physical_prediction_audit import audit
from rr_occupancy import Occupancy
from connection_golden import Result
out=Path('experiments/koios_cached_rc_probe_2026-10-04');cap=Path('experiments/koios_spmv_cost_binding_2026-10-04');front=Path('experiments/koios_spmv_endpoints_v2_2026-10-04')
if out.exists():raise ValueError('fresh output required')
r=json.loads((cap/'receipt.json').read_text());fr=json.loads((front/'receipt.json').read_text());inputs={k:{'path':str((cap/k).resolve()),'sha256':v} for k,v in r['outputs'].items()};inputs['endpoints']={'path':str((front/'endpoints.json').resolve()),'sha256':fr['outputs']['endpoints.json']};assert r['exit_code']==0 and all(sha(v['path'])==v['sha256'] for v in inputs.values());e=json.loads(Path(inputs['endpoints']['path']).read_text());groups=defaultdict(list)
for row in e['connections']:groups[row['net_id']].append(row)
net=min(groups,key=lambda n:(-len(groups[n]),n));cohort=groups[net];sources={v['source'] for v in cohort};assert len(sources)==1;source=next(iter(sources));targets={v['sink'] for v in cohort};out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
p={'inputs':inputs,'scope':'cold preparation and largest endpoint-fanout SOURCE group probe; no native route labels; not fullcohort accuracy','selection':'largest endpoint fanout, tie ascending netID','net_id':net,'connections':len(cohort),'node_budget':'entire physical graph','objective':'unchanged normalized halfRC+base/scale1e6/nearest-even, explicit8classbinding, no pressure/tree/lookahead/labels','samples':'1001 evenly spaced physical edge IDs, exact raw RC oracle plus indexed base; no selection by score','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps({'pid':os.getpid(),'stage':'load_graph','net_id':net,'connections':len(cohort)}),flush=True);start=time.monotonic();g=read_rr_graph(inputs['rr_graph.xml']['path']);load=time.monotonic()-start;print(json.dumps({'stage':'graph_loaded','load_s':load,'nodes':len(g.nodes),'edges':len(g.edges)}),flush=True);text=Path(inputs['rr_indexed_data.echo']['path']).read_text();csv=Path(inputs['routecast_node_cost_indices.csv']['path']).read_text();identity={'graph_sha256':g.sha256,'table_sha256':inputs['rr_indexed_data.echo']['sha256'],'bindings_sha256':inputs['routecast_node_cost_indices.csv']['sha256']};start=time.monotonic();model=CachedBoundRC(g,text,csv,identity);prep=time.monotonic()-start;print(json.dumps({'stage':'model_ready','preparation_s':prep,'cache_entries':model.cache_entries}),flush=True)
# Deterministic raw-oracle samples include endpoints of the serialized edge range.
start=time.monotonic();rc=PathRC(g);sample_ids={i*(len(g.edges)-1)//1000 for i in range(1001)};wanted={eid for eid in sample_ids};seen={}
for arcs in model.outgoing.values():
 for eid,dst,w in arcs:
  if eid in wanted:
   edge=g.edges[eid];delay=rc.step(State(Fraction(0),Fraction(0)),eid).delay;base=Fraction(model.rows[model.indices[dst]]['base']);expected=round((delay+base)/model.normalization*model.scale/2);assert w==(expected if g.nodes[dst].capacity else None);seen[eid]=w
assert set(seen)==sample_ids;oracle_s=time.monotonic()-start;del rc;print(json.dumps({'stage':'oracle_checked','samples':len(seen),'oracle_s':oracle_s}),flush=True);start=time.monotonic();result=model.search(source,targets);query=time.monotonic()-start;assert not result.budget_exhausted and set(result.paths)==targets
ledger=Occupancy(g);rows=[]
for row in cohort:
 path=result.paths[row['sink']];assert ledger.update(row['connection_id'],1,net,source,row['sink'],path)==Result.COMMITTED;rows.append({**row,'physical_edge_ids':path,'method':'cached_bound_rc'})
pilot={**e,'connections':cohort};prediction={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(rows),'completed':len(rows),'methods':{'cached_bound_rc':len(rows)}};checked=audit(g,pilot,prediction)
for name,data in [('prediction.json',prediction),('endpoints.json',pilot),('oracle_samples.json',seen)]: (out/name).write_text(json.dumps(data)+'\n')
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());receipt={'protocol_sha256':sha(out/'protocol.json'),'graph_load_s':load,'preparation_s':prep,'oracle_check_s':oracle_s,'query_s':query,'edge_visits':result.edge_visits,'settled_nodes':result.settled_nodes,'budget_exhausted':result.budget_exhausted,'cache_entries':model.cache_entries,'all_edge_cost_queries':model.edge_cost_queries,'exact_oracle_samples':len(seen),'audit':checked,'inputs_unchanged':True,'outputs':{n:sha(out/n) for n in ('prediction.json','endpoints.json','oracle_samples.json')}};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

"""Frozen existing paths RC expansion diagnostic; no new path selection."""
import json, shutil, time
from pathlib import Path
from rr_graph import read_rr_graph
from path_rc import PathRC
from pre_route_endpoints import sha
out=Path('experiments/path_rc_diagnostic_2026-10-04')
if out.exists():raise ValueError('fresh directory required')
out.mkdir();(out/'source').mkdir()
for name in ('path_rc_trial.py','path_rc.py','rr_graph.py','pre_route_endpoints.py'):
 shutil.copyfile(Path(__file__).with_name(name),out/'source'/name)
specs={
 'diffeq':('../persistroute/experiments/vpr9/diffeq_seed1/rr_graph.xml','baseline_cluster_criticality_v6_2026-10-04'),
 'elliptic':('work/elliptic_graph_capture_2026-10-04/rr_graph.xml','elliptic_cluster_criticality_v6_2026-10-04')}
inputs={}
for design,(graph,context) in specs.items():
 for kind,p in [('graph',Path(graph)),('paths',Path('experiments/frozen_pressure_zero_2026-10-04')/f'{design}_prediction.json'),('criticality',Path('experiments')/context/'joined_criticality.json')]:inputs[f'{design}_{kind}']={'path':str(p.resolve()),'sha256':sha(p)}
protocol={'inputs':inputs,'initial_resistance':0,'initial_delay':0,'scope':'fixed previously predicted paths; exact serialized-decimal VPR connection-expansion RC only, no branching/tree loading/native float parity/new search/candidate CPD','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
summary={};start=time.monotonic()
for design in specs:
 graph=read_rr_graph(inputs[f'{design}_graph']['path']);model=PathRC(graph)
 paths=json.loads(Path(inputs[f'{design}_paths']['path']).read_text());ctx=json.loads(Path(inputs[f'{design}_criticality']['path']).read_text())
 assert graph.sha256==paths['physical_graph_sha256']==ctx['graph_sha256']
 endpoints={r['connection_id']:r for r in ctx['connections']};records=[]
 for p in paths['connections']:
  e=endpoints[p['connection_id']]
  assert all(p[k]==e[k] for k in ('net_id','source','sink'))
  edges=p['physical_edge_ids'];assert edges and graph.edges[edges[-1]].sink==e['sink']
  state=model.path(e['source'],edges)
  intrinsic=sum(model.switches[graph.edges[eid].switch_id][2] for eid in edges)
  records.append({'connection_id':e['connection_id'],'expansion_delay_fraction':str(state.delay),'intrinsic_delay_fraction':str(intrinsic),'final_resistance_fraction':str(state.resistance),'expansion_delay_ns':float(state.delay)*1e9,'criticality':e['criticality']})
 assert len(records)==len(endpoints) and len({r['connection_id'] for r in records})==len(records)
 values=sorted(r['expansion_delay_ns'] for r in records)
 summary[design]={'connections':len(records),'all_endpoints_and_arcs_checked':True,'negative_path_delays':sum(r['expansion_delay_ns']<0 for r in records),'min_ns':values[0],'median_ns':values[len(values)//2],'max_ns':values[-1],'paths_with_rc_correction':sum(r['expansion_delay_fraction']!=r['intrinsic_delay_fraction'] for r in records),'switch_types':sorted({__import__('xml.etree.ElementTree',fromlist=['ElementTree']).fromstring(x).attrib['type'] for x in graph.switches.values()})}
 (out/f'{design}_path_rc.json').write_text(json.dumps({'graph_sha256':graph.sha256,'records':records},indent=2)+'\n')
assert all(sha(x['path'])==x['sha256'] for x in inputs.values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'elapsed_s':time.monotonic()-start,'inputs_unchanged':True,'summary':summary,'outputs':{p.name:sha(p) for p in out.glob('*_path_rc.json')}},indent=2)+'\n')
print(json.dumps(summary,indent=2))
